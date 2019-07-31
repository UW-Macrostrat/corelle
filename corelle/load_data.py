from pg_viewtils import reflect_table
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects.postgresql import insert
from time import perf_counter
from json import dumps
import fiona
import csv
from click import echo, style

from .database import db, create_session

__conn = None
def connect():
    global __conn
    if __conn is None:
        __conn = db.connect()
    return __conn

def get_model(name):
    model = reflect_table(db, 'model')
    conn = connect()
    try:
        conn.execute(model.insert().values(name=name))
    except IntegrityError:
        pass
    return conn.execute(
        model.select().where(model.c.name==name)
    ).first()[0]

__plate = reflect_table(db,'plate')
__feature = reflect_table(db, 'feature')
__rotation = reflect_table(db,'rotation')
__plate_polygon = reflect_table(db, 'plate_polygon')

def pg_geometry(feature):
    geom = dumps(feature['geometry'])
    _ = func.ST_GeomFromGeoJSON(geom)
    return func.ST_SetSRID(func.ST_Multi(_), 4326)

def insert_plate(**vals):
    connect().execute(
        insert(__plate)
            .values(vals)
            .on_conflict_do_nothing())

def import_plate(model_id, feature, fields=None):

    conn = connect()

    def field(field_id):
        # If we have provided a mapping of fields for the input
        # geojson file, we should use these fields for
        if fields and field_id in fields:
            field_id = fields[field_id]
        return feature['properties'].get(field_id, None)

    plate_id = field("id")

    insert_plate(
        id=plate_id,
        model_id=model_id,
        parent_id=field('parent_id'),
        name=field('name'),
        cotid=field('cotid'),
        coid=field('coid'))

    young_lim = field('young_lim')
    if young_lim == -999:
        young_lim = None

    poly_vals = dict(
        plate_id=plate_id,
        model_id=model_id,
        young_lim=young_lim,
        old_lim=field('old_lim'),
        geometry=pg_geometry(feature))

    conn.execute(__plate_polygon
            .insert()
            .values(poly_vals))

def import_plates(model_id, plates, fields={}):
    session = create_session()
    with fiona.open(plates, 'r') as src:
        conn = connect()
        trans = conn.begin()

        mrf = None
        if fields:
            mrf = fields.get("mantle_reference_frame", None)
        if mrf is not None:
            insert_plate(
                id=mrf,
                model_id=model_id,
                name='Mantle reference frame')

        # The spin axis is assumed to have plate ID 0 by default
        spin_axis = fields.get("spin_axis", 0)
        insert_plate(
            id=spin_axis,
            model_id=model_id,
            name='Spin axis')

        for feature in src:
            import_plate(model_id, feature, fields=fields)

        trans.commit()

def import_feature(dataset, feature):
    conn = connect()

    vals = dict(
        dataset_id=dataset,
        properties=(feature['properties'] or None),
        geometry=pg_geometry(feature))

    conn.execute(__feature
            .insert()
            .values(vals))

def import_features(name, features, overwrite=False):
    session = create_session()

    with fiona.open(features, 'r') as src:
        conn = connect()
        trans = conn.begin()

        if overwrite:
            conn.execute(__feature
                .delete()
                .where(__feature.c.dataset_id == dataset))

        for i, feature in enumerate(src):
            import_feature(name, feature)
        trans.commit()
    echo(f"Imported {i+1} features for dataset "+style(name, bold=True))

def import_rotation_row(model_id, line):
    """
    Import a line from a GPlates rotations file
    """
    if line.startswith('*'): return

    conn = connect()
    data, meta = line.strip().split("!",1)
    row = data.split()

    if int(row[0]) == 999:
        return

    # Insert first plate id
    plate_id = row[0]
    ref_plate_id = row[5]
    # Not sure that every plate_id-ref_plate_id
    # pair is actually unique as would be needed
    # here...
    insert_plate(
        id=ref_plate_id,
        model_id=model_id)
    insert_plate(
        id=plate_id,
        model_id=model_id,
        parent_id=ref_plate_id)

    vals = dict(
        plate_id=plate_id,
        model_id=model_id,
        t_step=row[1],
        latitude=row[2],
        longitude=row[3],
        angle=row[4],
        ref_plate_id=ref_plate_id,
        # Postgres chokes on NULL characters in strings
        metadata=meta.replace('\x00', ''))
    _ = __rotation.insert().values(vals)
    conn.execute(_)

def import_rotations(model_id, rotations):
    """
    Import a set of plate rotations defined
    in a GPlates rotation file structure.

    Constructed on 2019-03-15 for use with
    PaleoPlates data, so it might not work
    well for other `.rot` files in its current
    form.
    """
    conn = connect()
    with open(rotations, 'r') as f:
        start = perf_counter()
        for i, line in enumerate(f):
            import_rotation_row(model_id, line)
        elapsed = perf_counter()-start
        print(f"Imported {i+1} rotations in {elapsed:.2f} seconds")

def import_model(name, plates, rotations, fields=None, drop=False):
    model_id = get_model(name)
    import_plates(model_id, plates, fields=fields)
    import_rotations(model_id, rotations)
