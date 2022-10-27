"""
Mapped database models. These would ideally be in the database module, but
they need to be here to avoid initialization issues.
"""
from pg_viewtils import reflect_table
from sqlalchemy.sql import select

from ..database import db

_model = reflect_table(db, "model", schema="corelle")
_plate = reflect_table(db, "plate", schema="corelle")
_rotation = reflect_table(db, "rotation", schema="corelle")
_rotation_cache = reflect_table(db, "rotation_cache", schema="corelle")

conn = db.connect()


def get_from_cache(cache_args):
    # Get a rotation from the in-memory cache
    (model_name, plate_id, time) = cache_args

    tbl = _rotation_cache.join(_model, _model.c.id == _rotation_cache.c.model_id)
    res = conn.execute(
        select([_rotation_cache.c.rotation])
        .select_from(tbl)
        .where(_model.c.name == model_name)
        .where(_rotation_cache.c.plate_id == plate_id)
        .where(_rotation_cache.c.t_step == time)
    ).scalar()
    if res is not None:
        return N.quaternion(*res)
    return None


def model_id(name):
    stmt = _model.select().where(_model.c.name == name)
    return conn.execute(stmt).scalar()
