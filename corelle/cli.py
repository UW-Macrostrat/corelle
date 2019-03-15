import warnings
warnings.filterwarnings("ignore")

from click import (
    group, argument, option,
    echo, style, Path)

from .database import initialize
from .load_data import import_model
from .rotate import build_cache, get_rotation

@group()
def cli():
    pass

@cli.command(name='init')
@option('--drop', is_flag=True, default=False)
def init(drop=False):
    initialize(drop=drop)

file = Path(exists=True, dir_okay=False)

@cli.command(name='import')
@argument('model_name')
@argument('plates', type=file)
@argument('rotations', type=file)
@option('--drop', is_flag=True, default=False)
def _import(model_name, plates, rotations, drop=False):
    """
    Import a plate-rotation model
    """
    import_model(model_name, plates, rotations, drop=False)

@cli.command(name='cache')
def cache():
    """
    Compute and cache rotations
    """
    build_cache()

@cli.command(name='rotate')
@argument('plate', type=int)
@argument('time', type=float)
def rotate(plate, time):
    """
    Rotate a plate to a time
    """
    get_rotation(plate, time)
