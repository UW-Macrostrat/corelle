"""
Mapped database models. These would ideally be in the database module, but
they need to be here to avoid initialization issues.
"""
from .database import db

_model = db.reflect_table("model", schema="corelle")
_plate = db.reflect_table("plate", schema="corelle")
_rotation = db.reflect_table("rotation", schema="corelle")
_rotation_cache = db.reflect_table("rotation_cache", schema="corelle")

conn = db.engine.connect()


def model_id(name):
    stmt = _model.select().where(_model.c.name == name)
    return conn.execute(stmt).scalar()
