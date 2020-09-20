import numpy as N
import quaternion as Q
from pg_viewtils import reflect_table
from click import secho
from decimal import Decimal

from .math import cart2sph, sph2cart, euler_to_quaternion, quaternion_to_euler
from ..query import get_sql
from ..database import db

__model = reflect_table(db, "model")
__plate = reflect_table(db, "plate")
__rotation = reflect_table(db, "rotation")

conn = db.connect()


class RotationError(Exception):
    pass


class UndefinedRotationError(RotationError):
    def __init__(self, plate_id, time):
        super().__init__(self, f"No rotation found for plate {plate_id} at time {time}")
        self.plate_id = plate_id
        self.time = time


cache = {}
cache_list = []


def build_cache(q, cache_args):
    # Fetches a sequence of rotations per unit time
    cache[cache_args] = q
    cache_list.append(cache_args)
    if len(cache_list) > 50000:
        id = cache_list.pop(0)
        try:
            del cache[id]
        except KeyError:
            pass
    return q


def model_id(name):
    stmt = __model.select().where(__model.c.name == name)
    return conn.execute(stmt).scalar()


__sql = get_sql("rotation-pairs")


def check_model_id(model_name):
    # Make sure our model id actually exists
    id = model_id(model_name)
    if id is None:
        raise RotationError("Unknown model id")


# Cache this expensive, recursive function.
def get_rotation(
    model_name, plate_id, time, verbose=False, depth=0, rowset=None, safe=True,
):
    """Core function to rotate a plate to a time by accumulating quaternions"""
    time = float(time)
    cache_args = (model_name, plate_id, Decimal(time))
    if cache_args in cache:
        return cache[cache_args]

    if safe:
        check_model_id(model_name)

    __cache = lambda q: build_cache(q, cache_args)

    prefix = " " * depth
    if verbose:
        secho(prefix + str(plate_id))

    if plate_id is None or plate_id == 0:
        return __cache(N.quaternion(1, 0, 0, 0))

    params = dict(plate_id=plate_id, model_name=model_name, time=time)

    pairs = []
    if rowset:
        _pairs = [p for p in rowset if p.plate_id == plate_id]
        pairs = [
            p
            for p in _pairs
            if N.allclose(float(p.r1_step), time) and not p.interpolated
        ] + [p for p in _pairs if p.r1_step < time and (p.r2_step or -1) > time]
        # pairs.sort(key=lambda x: -x.r1_step)
    if len(pairs) == 0:
        pairs = db.execute(__sql, **params).fetchall()
    if len(pairs) == 0:
        return None
    if verbose:
        for i, pair in enumerate(pairs):
            color = "green" if i == 0 else "white"
            secho(prefix + f"{pair.plate_id} → {pair.ref_plate_id}", fg=color)

    row = pairs[0]
    r1_step = float(row.r1_step)
    __close_pairs = [p for p in pairs if not p.interpolated]
    if len(__close_pairs) > 0:
        row = __close_pairs[0]

    q1 = euler_to_quaternion(row.r1_rotation)

    r1_base = get_rotation(
        model_name,
        row.ref_plate_id,
        row.r1_step,
        verbose=verbose,
        depth=depth + 1,
        rowset=rowset,
        safe=False,
    )
    if r1_base is None:
        return __cache(None)

    if not row.interpolated:
        # We have an exact match!
        # Just a precautionary guard, this should be assured by our SQL
        return __cache(r1_base * q1)

    ## Interpolated rotations

    base = get_rotation(
        model_name,
        row.ref_plate_id,
        time,
        verbose=verbose,
        depth=depth + 1,
        rowset=rowset,
        safe=False,
    )
    if base is None:
        return __cache(None)

    q2 = euler_to_quaternion(row.r2_rotation)

    # Cache rotations for r2_step, which will likely be used by other rotations.
    # We do this because SQL queries are much more expensive than vector math.
    # r2_base = get_rotation(
    #     model_name, row.ref_plate_id, r2_step, verbose, depth=depth + 1
    # )
    # r2_rot = None
    # if r2_rot is not None:
    #     r2_rot = r2_base * q2
    # build_cache(r2_rot, (model_name, plate_id, r2_step))

    # Calculate interpolated rotation between the two timesteps
    res = Q.slerp(q1, q2, float(row.r1_step), float(row.r2_step), time)
    return __cache(base * res)


def plates_for_model(model):
    sql = get_sql("plates-for-model")
    for row in conn.execute(sql, model_name=model):
        yield row[0]


def rotate_point(point, model, time):
    if time == 0:
        return point
    sql = get_sql("plate-for-point")
    plate_id = conn.execute(
        sql, lon=point[0], lat=point[1], model_name=model, time=time
    ).scalar()
    if plate_id is None:
        return None
    q = get_rotation(model, plate_id, time)
    v0 = sph2cart(*point)
    v1 = Q.rotate_vectors(q, v0)
    return cart2sph(v1)


__tstep_rotation_pairs = get_sql("rotation-pairs-for-time")
__active_plates_sql = get_sql("active-plates-at-time")
__model_plates_sql = get_sql("plates-for-model")


def plates_for_model(model):
    """Returns a list of plate IDs for a given model"""
    return [k[0] for k in conn.execute(__model_plates_sql, model_name=model)]


def get_all_rotations(
    model, time, verbose=False, active_only=True, plates=None, safe=True
):
    """Get all rotations for a model and a timestep

    Parameters
    ----------
    model : str
            The rotation model to use
    time : float
           The time to rotate to, in Myr before present.

    Yields
    ------
    dict
    """
    if plates is None:
        if active_only:
            res = conn.execute(__active_plates_sql, time=time, model_name=model)
            plates = [p[0] for p in res]
        else:
            plates = plates_for_model(model)

    rowset = conn.execute(
        __tstep_rotation_pairs, time=time, model_name=model
    ).fetchall()

    if safe:
        check_model_id(model)
    for plate_id in plates:
        q = get_rotation(
            model, plate_id, time, verbose=verbose, rowset=rowset, safe=False
        )
        if q is None:
            continue
        if N.isnan(q.w):
            continue
        yield plate_id, q


def get_rotation_series(model, *times, **kwargs):
    # Pre-compute plates for speed...
    # LOL this actually makes things slower
    #  kwargs["plates"] = plates_for_model(model)
    check_model_id(model)
    for t in times:
        r = get_all_rotations(model, float(t), safe=False, **kwargs)
        yield dict(rotations=list(r), time=float(t))


def get_plate_rotations(model, plate_id, verbose=False):
    time_step = 1
    time_range = (0, 500)
    time_steps = range(0, 500, 1)
    return ((get_rotation(model, plate_id, t), t) for t in time_steps)
