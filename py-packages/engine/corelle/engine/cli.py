import warnings

from IPython import embed
from os import environ
import click
from click import group, argument, option, echo
from macrostrat.utils import working_directory
from pathlib import Path

warnings.filterwarnings("ignore")


@group()
def cli():
    """Register and pre-calculate plate-rotation models"""
    pass


@cli.command(name="init")
@option("--drop", is_flag=True, default=False)
def init(drop=False):
    """Create database fixtures"""
    from .database import initialize

    initialize(drop=drop)


file = click.Path(exists=True, dir_okay=False)


@cli.command(name="import")
@argument("model_name")
@argument("plates", type=file)
@argument("rotations", type=file)
@option("--fields", type=file)
@option("--overwrite", is_flag=True, default=False)
@option("--min-age", type=float, default=None)
@option("--max-age", type=float, default=None)
def _import(
    model_name,
    plates,
    rotations,
    fields=None,
    overwrite=False,
    min_age=None,
    max_age=None,
):
    """
    Import a plate-rotation model
    """
    from .load_data import import_model

    import_model(
        model_name,
        plates,
        rotations,
        fields=fields,
        overwrite=overwrite,
        min_age=min_age,
        max_age=max_age,
    )


@cli.command(name="import-features")
@argument("name")
@argument("file", type=file)
@option("--overwrite", is_flag=True, default=False)
def _import_features(name, file, overwrite=False):
    """
    Import features that can be associated with the models
    """
    from .load_data import import_features

    import_features(name, file, overwrite=False)


@cli.command(name="import-starter-data")
def import_basic():
    """Import basic models and data"""
    from .load_data import load_basic_data

    load_basic_data()


@cli.command(name="reset-cache")
def cache():
    """
    Compute and cache rotations
    """
    from .rotate import reset_cache

    reset_cache()
    echo("Cache was reset!")


@cli.command(name="rotate")
@argument("model", type=str)
@argument("plate", type=int)
@argument("time", type=float)
@option("--verbose", "-v", is_flag=True, default=False)
def rotate(model, plate, time, verbose=False):
    """
    Rotate a plate to a time
    """
    import numpy as N
    from corelle.math import quaternion_to_euler
    from .rotate import get_rotation

    q = get_rotation(model, plate, time, verbose=verbose)
    if q is None:
        echo(f"No rotation for plate {plate} at {time} Ma.")
        return
    angle = N.degrees(q.angle())
    echo(f"Rotate {angle:.2f}° around {q.vec}")
    lat, lon, angle = quaternion_to_euler(q)
    echo(f"Pole: {lat:.2f}°, {lon:.2f}°; Angle: {angle:.2f}°")


@cli.command(name="rotate-all")
@argument("model", type=str)
@argument("time", type=float)
@option("--verbose", "-v", is_flag=True, default=False)
def rotate_all(model, time, verbose=False):
    """
    Rotate all plates in a model to a time
    """
    import numpy as N
    from .rotate import get_all_rotations

    for plate_id, q in get_all_rotations(model, time, verbose=verbose):
        angle = N.degrees(q.angle())
        echo(f"{plate_id}: rotate {angle:.2f}° around {q.vec}")


@cli.command(name="serve")
@option("-p", "--port", type=int, default=5000)
@option("--debug", is_flag=True, default=False)
def serve(**kwargs):
    """Run the application server"""
    from corelle.server import app

    app.run(host="0.0.0.0", **kwargs)


@cli.command(name="shell")
def shell():
    """Get a shell in the application context"""
    embed()


@cli.command(name="cache-rotations")
def build_cache():
    """Cache rotations for all models"""
    from .cache import build_rotation_caches

    build_rotation_caches()


def parent_dir(_start: str, name: str) -> Path:
    start = Path(_start)
    while start.parent is not None:
        start = start.parent
        if start.name == name:
            return start
    return None


@cli.command(name="test", context_settings=dict(ignore_unknown_options=True))
def test(*args):
    """Run tests"""
    basedir = parent_dir(__file__, "py-packages")

    with working_directory(basedir):
        from pytest import main

        main(list(args))
