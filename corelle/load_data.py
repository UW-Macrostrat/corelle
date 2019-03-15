from pg_viewtils import reflect_table
from .database import db, create_session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects.postgresql import insert
from functools import partial
from time import perf_counter
from json import dumps
import fiona
import csv

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
                parent_id=p['ParentPlat'],
                name=p['PlateName'],
                cotid=p['COTID'],
                coid=p['COID'])

            _ = func.ST_GeomFromGeoJSON(geom)
            geom = func.ST_SetSRID(func.ST_Multi(_), 4326)

            young_lim = p['LimYngP']
            if young_lim == -999:
                young_lim = None
            poly_vals = dict(
                plate_id=plate_id,
                young_lim=young_lim,
                old_lim=p['LimOldP'],
                geometry=geom)

            stmt = (plate_polygon
                    .insert()
                    .values(poly_vals))

            conn.execute(stmt)

        trans.commit()

def import_rotations(model_id, rotations):
    rotation = reflect_table(db,'rotation')
    session = create_session()
    conn = db.connect()

    with open(rotations, 'r') as f:
        start = perf_counter()
        for i, line in enumerate(f):
            if line.startswith('*'): continue
            data, meta = line.strip().split("!",1)
            row = data.split()

            # Insert first plate id
            plate_id = row[0]
            ref_plate_id = row[5]
            insert_plate(conn,
                    id=plate_id,
                    model_id=model_id)
            insert_plate(conn,
                    id=ref_plate_id,
                    model_id=model_id)

            vals = dict(
                plate_id=plate_id,
                t_step=row[1],
                latitude=row[2],
                longitude=row[3],
                angle=row[4],
                ref_plate_id=ref_plate_id,
                metadata=meta)
            _ = rotation.insert().values(vals)
            conn.execute(_)
        elapsed = perf_counter()-start
        print(f"Imported {i} rotations in {elapsed} seconds")

def import_model(name, plates, rotations, drop=False):
    model_id = get_model(name)
    import_plates(model_id, plates)
    import_rotations(model_id, rotations)


