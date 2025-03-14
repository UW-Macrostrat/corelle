"""
Mapped database models. These would ideally be in the database module, but
they need to be here to avoid initialization issues.
"""

from sqlalchemy.sql import select

from rich.progress import Progress
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql import text
import numpy as N

from corelle.math import quaternion_to_euler
from .storage import _model, _rotation_cache, conn, model_id
from .rotate import get_rotation_series
from .database import db
from .query import get_sql

update_derived = get_sql("update-cache")


def get_from_cache(cache_args):
    # Get a rotation from the database cache
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


def build_rotation_caches():
    # Truncate the rotation cache
    conn.execute(_rotation_cache.delete())
    # Get the list of models
    models = conn.execute(_model.select()).fetchall()

    for model in models:
        build_rotation_cache(model)


def build_rotation_cache(model, time_step=1):
    # Get the time span of the model

    min_age = model.min_age or 0
    max_age = model.max_age or 1000

    # Get model steps every 1 Myr
    t_steps = list(range(int(min_age), int(max_age) + 1, time_step))

    session = db.session()

    session.execute(
        text("DELETE FROM corelle.rotation_cache WHERE model_id = :model_id"),
        dict(model_id=model.id),
    )
    session.commit()

    rotations = get_rotation_series(model.name, *t_steps)

    for tstep in rotations:
        time = tstep["time"]
        print(model.name, " - ", time, " Ma")
        rows = [
            build_cache_row(model.id, plate_id, time, q)
            for plate_id, q in tstep["rotations"]
            if q is not None
        ]
        add_to_cache(session, rows)

        # Add derived columns
        # session.execute(update_derived, model_id=model.id, t_step=time)
        # progress.advance(task)


def build_cache_row(model_id, plate_id, t_step, q):
    # lat, lon, angle = quaternion_to_euler(q)
    # # Create geometry as WKT
    # geom = f"SRID=4326;POINT({lon} {lat})"

    return dict(
        model_id=int(model_id),
        plate_id=int(plate_id),
        t_step=float(t_step),
        rotation=[q.w, q.x, q.y, q.z],
    )


def add_to_cache(session, data):
    if not data:
        return
    # Add a rotation to the database cache
    session.execute(insert(_rotation_cache), data)
    session.commit()
