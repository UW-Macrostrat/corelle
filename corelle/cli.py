import warnings
warnings.filterwarnings("ignore")

import json, yaml
import numpy as N
from IPython import embed

from click import (
    group, argument, option,
    echo, style, Path)
from os.path import splitext

@group()
def cli():
    pass

@cli.command(name='init')
@option('--drop', is_flag=True, default=False)
def init(drop=False):
    from .database import initialize
    initialize(drop=drop)

file = Path(exists=True, dir_okay=False)

def load_fields(fn):
    if not fn:
        return None
    ext = splitext(fn)[1]
    with open(fn, "r") as f:
        if ext == '.json':
            return json.load(f)
        if ext in ['.yaml', '.yml']:
            return yaml.load(f)
    return None

@cli.command(name='import')
@argument('model_name')
@argument('plates', type=file)
@argument('rotations', type=file)
@option('--fields', type=file)
@option('--drop', is_flag=True, default=False)
def _import(model_name, plates, rotations, fields=None, drop=False):
    """
    Import a plate-rotation model
    """
    from .load_data import import_model
    fields = load_fields(fields)
    import_model(model_name, plates, rotations, fields=fields,drop=False)

@cli.command(name='import-features')
@argument('name')
@argument('file', type=file)
@option('--overwrite', is_flag=True, default=False)
def _import_features(name, file, overwrite=False):
    """
    Import features that can be associated with the models
    """
    from .load_data import import_features
    import_features(name, file, overwrite=False)

@cli.command(name='cache')
def cache():
    """
    Compute and cache rotations
    """
    build_cache()

@cli.command(name='rotate')
@argument('model', type=str)
@argument('plate', type=int)
@argument('time', type=float)
@option('--verbose','-v', is_flag=True, default=False)
def rotate(model, plate, time, verbose=False):
    """
    Rotate a plate to a time
    """
    from .rotate import get_rotation
    q = get_rotation(model, plate, time, verbose=verbose)
    angle = N.degrees(q.angle())
    echo(f"Rotate {angle:.2f}° around {q.vec}")

@cli.command(name='rotate-all')
@argument('model', type=str)
@argument('time', type=float)
@option('--verbose','-v', is_flag=True, default=False)
def rotate_all(model, time, verbose=False):
    """
    Rotate all plates in a model to a time
    """
    from .rotate import get_all_rotations
    for plate_id, q in get_all_rotations(model, time, verbose=verbose):
        angle = N.degrees(q.angle())
        echo(f"{plate_id}: rotate {angle:.2f}° around {q.vec}")

@cli.command(name='serve')
@option('-p','--port', type=int, default=5000)
@option('--debug', is_flag=True, default=False)
def serve(**kwargs):
    from .api import app
    app.run(**kwargs)

@cli.command(name='shell')
def shell():
    from .api import app
    embed()
