"""
Mapped database models. These would ideally be in the database module, but
they need to be here to avoid initialization issues.
"""
from .database import db

_model = db.reflect_table("model", schema="corelle")
_plate = db.reflect_table("plate", schema="corelle")
_rotation = db.reflect_table("rotation", schema="corelle")
_rotation_cache = db.reflect_table("rotation_cache", schema="corelle")


class PooledConnection:
    """Runs each statement in its own transaction on a pooled connection.

    A shared long-lived connection idles in a transaction between requests; once
    it breaks, every later query fails until the process restarts.
    """

    def execute(self, *args, **kwargs):
        with db.engine.begin() as connection:
            result = connection.execute(*args, **kwargs)
            if not result.returns_rows:
                return result
            # Buffer rows so they outlive the connection.
            return result.freeze()()


conn = PooledConnection()


def model_id(name):
    stmt = _model.select().where(_model.c.name == name)
    return conn.execute(stmt).scalar()
