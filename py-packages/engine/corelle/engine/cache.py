"""Precomputed rotations, stored in `corelle.rotation_cache`."""

import numpy as N
from sqlalchemy.sql import text

from .query import get_sql
from .rotate import get_rotation_series

update_derived = get_sql("update-cache")

_cached_rotation = text(
    """
    SELECT c.rotation
    FROM corelle.rotation_cache c
    JOIN corelle.model m ON m.id = c.model_id
    WHERE m.name = :model_name AND c.plate_id = :plate_id AND c.t_step = :time
    """
)

_insert_rotation = text(
    """
    INSERT INTO corelle.rotation_cache (model_id, plate_id, t_step, rotation)
    VALUES (:model_id, :plate_id, :t_step, :rotation)
    """
)


def get_from_cache(conn, cache_args):
    (model_name, plate_id, time) = cache_args
    params = dict(model_name=model_name, plate_id=plate_id, time=time)
    res = conn.execute(_cached_rotation, params).scalar()
    if res is not None:
        return N.quaternion(*res)
    return None


def build_rotation_caches(conn):
    conn.execute(text("DELETE FROM corelle.rotation_cache"))
    models = conn.execute(text("SELECT * FROM corelle.model")).fetchall()
    for model in models:
        build_rotation_cache(conn, model)


def build_rotation_cache(conn, model, time_step=1):
    min_age = model.min_age or 0
    max_age = model.max_age or 1000

    # Get model steps every 1 Myr
    t_steps = list(range(int(min_age), int(max_age) + 1, time_step))

    conn.execute(
        text("DELETE FROM corelle.rotation_cache WHERE model_id = :model_id"),
        dict(model_id=model.id),
    )

    for tstep in get_rotation_series(conn, model.name, *t_steps):
        time = tstep["time"]
        print(model.name, " - ", time, " Ma")
        rows = [
            build_cache_row(model.id, plate_id, time, q)
            for plate_id, q in tstep["rotations"]
            if q is not None
        ]
        add_to_cache(conn, rows)


def build_cache_row(model_id, plate_id, t_step, q):
    return dict(
        model_id=int(model_id),
        plate_id=int(plate_id),
        t_step=float(t_step),
        rotation=[float(v) for v in (q.w, q.x, q.y, q.z)],
    )


def add_to_cache(conn, data):
    if data:
        conn.execute(_insert_rotation, data)
