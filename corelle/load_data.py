from pg_viewtils import reflect_table
from .database import db

def import_model(name):
    model = reflect_table(db, 'model')
    session = create_session()
    obj = session.query(model).get(name)
    if not obj:
        obj = model(name=name)
        session.add(obj)
        session.commit()
    return obj

def import_rotations(model):
    rotation = reflect_table(db,'rotation')
    session = create_session()

