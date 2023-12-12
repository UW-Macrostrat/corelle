from sqlalchemy import func, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects.postgresql import insert
from time import perf_counter
from json import dumps
import fiona
from click import echo, style
import json
import yaml
from os.path import splitext
from pathlib import Path
from tempfile import TemporaryDirectory
from macrostrat.utils import working_directory
from wget import download
from contextlib import contextmanager
from geoalchemy2 import func as gfunc
from geoalchemy2.shape import from_shape
from shapely.geometry import shape, MultiPolygon

from .database import db
from .query import get_sql

__conn = None


def connect():
    global __conn
    if __conn is None:
        __conn = db.engine.connect()
    return __conn


def create_model(name, **kwargs):
    model = db.reflect_table("model", schema="corelle")
    conn = connect()
    try:
        conn.execute(
            insert(model)
            .values(name=name, **kwargs)
            .on_conflict_do_update(index_elements=(model.c.id,), set_=kwargs)
        )
    except IntegrityError:
        pass
    return conn.execute(model.select().where(model.c.name == name)).first()[0]


__plate = db.reflect_table("plate", schema="corelle")
__feature = db.reflect_table("feature", schema="corelle")
__rotation = db.reflect_table("rotation", schema="corelle")
__plate_polygon = db.reflect_table("plate_polygon", schema="corelle")


def pg_geometry(feature):
    """Convert a GeoJSON feature to a PostGIS geometry"""
    geom = shape(feature.geometry)
    # ensure the geometry is a valid multipolygon
    return gfunc.ST_Multi(gfunc.ST_MakeValid(from_shape(geom, srid=4326)))


def import_plate(model_id, feature, fields=None):
    def field(field_id):
        # If we have provided a mapping of fields for the input
        # geojson file, we should use these fields for
        if fields and field_id in fields:
            field_id = fields[field_id]
        return feature["properties"].get(field_id, None)

    plate_id = field("id") or feature.get("id", None)
    if plate_id is None:
        raise Exception(f"Invalid plate ID: {feature}")

    plate = dict(
        id=plate_id,
        model_id=model_id,
        parent_id=field("parent_id"),
        name=field("name"),
        cotid=field("cotid"),
        coid=field("coid"),
    )

    young_lim = field("young_lim")
    if young_lim == -999:
        young_lim = None

    plate_polygon = dict(
        plate_id=plate_id,
        model_id=model_id,
        young_lim=young_lim,
        old_lim=field("old_lim"),
        geometry=pg_geometry(feature),
    )

    return plate, plate_polygon


def import_plates(model_id, datafile, fields={}):
    """Import all plates for a model"""
    if fields is None:
        fields = {}

    plates = []
    plate_polygons = []
    with fiona.open(datafile, "r") as src:
        mrf = fields.get("mantle_reference_frame", None)
        if mrf is not None:
            plate = dict(id=mrf, model_id=model_id, name="Mantle reference frame")
            plates.append(plate)

        # The spin axis is assumed to have plate ID 0 by default
        spin_axis = fields.get("spin_axis", 0)
        spin_axis_plate = dict(id=spin_axis, model_id=model_id, name="Spin axis")
        plates.append(spin_axis_plate)

        for feature in src:
            plate, plate_polygon = import_plate(model_id, feature, fields=fields)
            plates.append(plate)
            plate_polygons.append(plate_polygon)

    # Run database transaction
    conn = connect()
    trans = conn.begin()
    conn.execute(insert(__plate).values(plates))
    for poly in plate_polygons:
        conn.execute(insert(__plate_polygon).values(poly))
    trans.commit()

    # For faster updates, this materialized view could become an actual table
    conn.execute("REFRESH MATERIALIZED VIEW corelle.plate_polygon_cache")


def create_feature(dataset, feature):
    props = feature["properties"]
    if props is not None:
        props = dict(props)

    return dict(
        dataset_id=dataset,
        properties=(props or None),
        geometry=pg_geometry(feature),
    )


def import_features(name, features, overwrite=False):
    start = perf_counter()
    conn = connect()
    with fiona.open(features, "r") as src:
        if overwrite:
            conn.execute(__feature.delete().where(__feature.c.dataset_id == name))

        vals = []
        for i, feature in enumerate(src):
            vals.append(create_feature(name, feature))

    trans = conn.begin()
    conn.execute(insert(__feature).values(vals))
    trans.commit()

    step1 = perf_counter()
    elapsed = step1 - start
    echo(
        f"Imported {i+1} features for dataset "
        + style(name, bold=True)
        + f" in {elapsed:.2f} seconds"
    )

    sql = get_sql("cache-feature-dataset")
    trans = conn.begin()
    conn.execute(sql, dataset_id=name)
    trans.commit()

    elapsed = perf_counter() - step1
    echo(f"  cached transformed features in {elapsed:.2f} seconds")


def create_rotation_row(model_id, line):
    """
    Import a line from a GPlates rotations file
    """
    if line.startswith("*"):
        return None, []

    data, meta = line.strip().split("!", 1)
    row = data.split()

    if int(row[0]) == 999:
        return None, []

    # Insert first plate id
    plate_id = row[0]
    ref_plate_id = row[5]
    # Not sure that every plate_id-ref_plate_id
    # pair is actually unique as would be needed
    # here...
    ref_plate = dict(id=ref_plate_id, model_id=model_id)
    plate = dict(id=plate_id, model_id=model_id, parent_id=ref_plate_id)

    rotation = dict(
        plate_id=plate_id,
        model_id=model_id,
        t_step=row[1],
        latitude=row[2],
        longitude=row[3],
        angle=row[4],
        ref_plate_id=ref_plate_id,
        # Postgres chokes on NULL characters in strings
        metadata=meta.replace("\x00", ""),
    )

    # Return the rotation and the plates that it refers to
    return rotation, [ref_plate, plate]


def import_rotations(model_id, filename):
    """
    Import a set of plate rotations defined
    in a GPlates rotation file structure.

    Constructed on 2019-03-15 for use with
    PaleoPlates data, so it might not work
    well for other `.rot` files in its current
    form.
    """
    rotations = []
    plates = []
    start = perf_counter()
    with open(filename, "r") as f:
        for i, line in enumerate(f):
            rotation, next_plates = create_rotation_row(model_id, line)
            if rotation is not None:
                rotations.append(rotation)
            plates.extend(next_plates)

    conn = connect()
    trans = conn.begin()
    conn.execute(
        insert(__plate)
        .values(plates)
        .on_conflict_do_nothing(index_elements=(__plate.c.id, __plate.c.model_id))
    )
    conn.execute(insert(__rotation).values(rotations).on_conflict_do_nothing())
    trans.commit()

    elapsed = perf_counter() - start
    print(f"Imported {i+1} rotations in {elapsed:.2f} seconds")


def import_model(
    name, plates, rotations, fields=None, overwrite=False, min_age=None, max_age=None
):
    print("Importing model", name)
    conn = connect()
    q = text("SELECT count(*) FROM corelle.model WHERE name=:name")
    res = conn.execute(q, name=name).scalar()
    if res == 1 and not overwrite:
        print("Model has already been imported.")
        return

    model_id = create_model(name, min_age=min_age, max_age=max_age)
    import_plates(model_id, plates, fields=load_fields(fields))
    import_rotations(model_id, rotations)
    # Right now we don't cache rotations on model import, but we could.


def load_fields(fn):
    if not fn:
        return None
    ext = splitext(fn)[1]
    with open(fn, "r") as f:
        if ext == ".json":
            return json.load(f)
        if ext in [".yaml", ".yml"]:
            return yaml.load(f, Loader=yaml.SafeLoader)
    return None


corelle_data_dir = Path(__file__).parent.parent.parent.parent.parent / "data"


def load_basic_data():
    """Load basic model and feature datasets"""
    with working_directory(str(corelle_data_dir)):
        import_model(
            "PalaeoPlates",
            "eglington/PlatePolygons2016All.json",
            "eglington/T_Rot_Model_PalaeoPlates_2019_20190302_experiment.rot",
            fields="eglington-fields.yaml",
        )

        import_model(
            "Seton2012",
            "seton_2012.geojson",
            "Seton_etal_ESR2012_2012.1.rot",
            fields="seton-fields.yaml",
            min_age=0,
            max_age=200,
        )

        import_model(
            "Wright2013",
            "wright_plates.geojson",
            "wright_2013.rot",
            fields="wright-fields.yaml",
            min_age=0,
            max_age=550,
        )

        import_model(
            "Scotese",
            "scotese.geojson",
            "scotese.rot",
            fields="scotese-fields.yaml",
            min_age=0,
            max_age=550,
        )

    # Import Natural Earth features
    # Download natural earth data to temp file
    prefix = "https://raw.githubusercontent.com/martynafford/natural-earth-geojson/master/110m/"

    # Create a temp directory
    with download_context():
        for dataset in [
            prefix + "cultural/ne_110m_populated_places_simple.json",
            prefix + "physical/ne_110m_land.json",
        ]:
            fn = dataset.split("/")[-1]
            dsn = fn.split(".")[0]

            # Check if this dataset has already been imported
            q = text(
                "SELECT count(*) FROM (SELECT DISTINCT dataset_id FROM corelle.feature WHERE dataset_id=:name) AS a"
            )
            res = connect().execute(q, name=dsn).scalar()
            if res == 1:
                continue

            # Download the dataset
            download(dataset, out=fn)

            # Import the dataset
            import_features(dsn, fn, overwrite=True)


@contextmanager
def download_context():
    with TemporaryDirectory() as tmpdir:
        with working_directory(tmpdir):
            yield tmpdir
