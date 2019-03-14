from pg_viewtils import reflect_table
from .database import db, create_session
from sqlalchemy.exc import IntegrityError

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

def import_plates(model_id, plates):
    rotation = reflect_table(db,'plate')
    session = create_session()

def import_rotations(model_id, rotations):
    rotation = reflect_table(db,'rotation')
    session = create_session()

def import_model(name, plates, rotations, drop=False):
    model_id = get_model(name)
    import_plates(model_id, plates)
    import_rotations(model_id, rotations)


