from rich import print
from rich.progress import Progress
from sqlalchemy.dialects.postgresql import array, insert
import numpy as N

from .rotate.storage import _model, _rotation_cache, conn
from .rotate.engine import get_rotation_series
from .rotate.math import quaternion_to_euler


def build_rotation_caches():
    # Truncate the rotation cache
    conn.execute(_rotation_cache.delete())
    # Get the list of models
    models = conn.execute(_model.select()).fetchall()

    for model in models:
        build_rotation_cache(model)


def build_rotation_cache(model, time_step=1):
    # Get the time span of the model

    min_age = model["min_age"] or 0
    max_age = model["max_age"] or 1000

    # Get model steps every 1 Myr
    t_steps = list(range(int(min_age), int(max_age) + 1, time_step))

    with Progress() as progress:
        task = progress.add_task(
            f"Building cache for model {model.name}", total=len(t_steps)
        )
        rotations = get_rotation_series(model.name, *t_steps)

        for tstep in rotations:
            time = tstep["time"]
            rows = [
                build_row(model.id, plate_id, time, q)
                for plate_id, q in tstep["rotations"]
                if q is not None
            ]
            add_to_cache(rows)
            progress.advance(task)


def build_row(model_id, plate_id, t_step, q):
    lat, lon, angle = quaternion_to_euler(q)
    # Create geometry as WKT
    geom = f"SRID=4326;POINT({lon} {lat})"

    return dict(
        model_id=int(model_id),
        plate_id=int(plate_id),
        t_step=float(t_step),
        rotation=[q.w, q.x, q.y, q.z],
        pole=geom,
        angle=float(N.radians(angle)),
    )


def add_to_cache(data):
    if not data:
        return
    # Add a rotation to the database cache
    conn.execute(insert(_rotation_cache).on_conflict_do_nothing(), data)
