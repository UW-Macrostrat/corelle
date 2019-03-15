from pg_viewtils import reflect_table
from .database import db, create_session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects.postgresql import insert
from functools import partial
from json import dumps
import fiona

def get_model(name):
    model = reflect_table(db, 'model')
    conn = db.connect()
    try:
        conn.execute(model.insert().values(name=name))
    except IntegrityError:
        pass
    return conn.execute(
        model.select().where(model.c.name==name)
    ).first()[0]

__plate = reflect_table(db,'plate')

def insert_plate(conn, **vals):
    stmt = (insert(__plate)
        .values(vals)
        .on_conflict_do_nothing())
    conn.execute(stmt)

def import_plates(model_id, plates):
    plate_polygon = reflect_table(db, 'plate_polygon')
    session = create_session()
    with fiona.open(plates, 'r') as src:

        conn = db.connect()
        trans = conn.begin()

        add_plate = partial(
                insert_plate,
                conn, model_id=model_id)

        add_plate(id=0, name='Mantle reference frame')
        add_plate(id=800, name='Spin axis')

        for feature in src:
            geom = dumps(feature['geometry'])
            p = feature['properties']

            plate_id = p["PlateID"]

            add_plate(
                id=plate_id,
                model_id=model_id,
                parent_id=p['ParentPlat'],
                name=p['PlateName'],
                cotid=p['COTID'],
                coid=p['COID'])

            young_lim = p['LimYngP']
            if young_lim == -999:
                young_lim = None
            poly_vals = dict(
                plate_id=plate_id,
                young_lim=young_lim,
                old_lim=p['LimOldP'],
                geometry=func.ST_SetSRID(
                    func.ST_Multi(func.ST_GeomFromGeoJSON(geom)),
                    4326
                ))

            stmt = (plate_polygon
                    .insert()
                    .values(poly_vals))

            conn.execute(stmt)

        trans.commit()

def import_rotations(model_id, rotations):
    rotation = reflect_table(db,'rotation')
    session = create_session()

def import_model(name, plates, rotations, drop=False):
    model_id = get_model(name)
    import_plates(model_id, plates)
    import_rotations(model_id, rotations)


