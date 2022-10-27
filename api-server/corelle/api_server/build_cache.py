from rich import print
from rich.progress import Progress


from .rotate.storage import _model, _rotation_cache, add_to_cache, conn
from .rotate.engine import get_rotation_series


def build_rotation_caches():
    # Truncate the rotation cache
    conn.execute(_rotation_cache.delete())
    # Get the list of models
    models = conn.execute(_model.select()).fetchall()

    for model in models:
        build_rotation_cache(model)


def build_rotation_cache(model):
    # Get the time span of the model

    min_age = model["min_age"] or 0
    max_age = model["max_age"] or 1000

    # Get model steps every 1 Myr
    t_steps = list(range(int(min_age), int(max_age) + 1, 5))

    with Progress() as progress:
        task = progress.add_task(
            f"Building cache for model {model.name}", total=len(t_steps)
        )
        rotations = get_rotation_series(model.name, *t_steps)

        for tstep in rotations:
            time = tstep["time"]
            for (plate_id, q) in tstep["rotations"]:
                add_to_cache((model.name, plate_id, time), q)
            progress.advance(task)
