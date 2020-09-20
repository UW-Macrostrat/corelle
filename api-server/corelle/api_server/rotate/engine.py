import numpy as N
import quaternion as Q
from pg_viewtils import reflect_table
from click import secho
from decimal import Decimal
from sqlalchemy.sql import select
from sqlalchemy.dialects.postgresql import array, insert

from .math import cart2sph, sph2cart, euler_to_quaternion, quaternion_to_euler
from ..query import get_sql
from ..database import db

__model = reflect_table(db, "model")
__plate = reflect_table(db, "plate")
__rotation = reflect_table(db, "rotation")
__rotation_cache = reflect_table(db, "rotation", schema="cache")

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


def add_to_cache(cache_args, q):
    # Fetches a sequence of rotations per unit time
    (model_name, plate_id, time) = cache_args

    rval = None
    if q is not None:
        rval = array([q.w, q.x, q.y, q.z])
    stmt = select([__model.c.id, plate_id, time, rval]).where(
        __model.c.name == model_name
    )
    conn.execute(
        insert(__rotation_cache)
        .from_select(["model_id", "plate_id", "t_step", "rotation"], stmt)
        .on_conflict_do_update(
            constraint=__rotation_cache.primary_key, set_=dict(rotation=rval)
        )
    )
    return q


def get_from_cache(cache_args):
    (model_name, plate_id, time) = cache_args

    tbl = __rotation_cache.join(__model, __model.c.id == __rotation_cache.c.model_id)
    res = conn.execute(
        select([__rotation_cache.c.rotation])
        .select_from(tbl)
        .where(__model.c.name == model_name)
        .where(__rotation_cache.c.plate_id == plate_id)
        .where(__rotation_cache.c.t_step == time)
    ).scalar()
    if res is not None:
        return N.quaternion(*res)
    return None


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
    model_name,
    plate_id,
    time,
    verbose=False,
    depth=0,
    rowset=None,
    safe=True,
):
    """Core function to rotate a plate to a time by accumulating quaternions"""
    time = float(time)
    cache_args = (model_name, plate_id, time)
    cached_val = get_from_cache(cache_args)
    if cached_val is not None:
        return cached_val

    __cache = lambda q: add_to_cache(cache_args, q)

    prefix = " " * depth
    if verbose:
        secho(prefix + str(plate_id))

    if plate_id is None or plate_id == 0:
        return __cache(N.quaternion(1, 0, 0, 0))

    params = dict(plate_id=plate_id, model_name=model_name, time=time)

    row = None
    pairs = []
    if rowset:
        for ix, p in enumerate(rowset):
            if p.plate_id == plate_id and p.r1_step <= time:
                pairs = [p]
                # Remove this row from the rowset (prevents weird recursion errors)
                rowset = rowset[:ix] + rowset[ix + 1 :]
                break
    else:
        # Fall back to fetching the data ourselves
        pairs = db.execute(__sql, **params).fetchall()
    if len(pairs) == 0:
        return __cache(None)
    if verbose:
        for i, pair in enumerate(pairs):
            color = "green" if i == 0 else "white"
            secho(prefix + f"{pair.plate_id} → {pair.ref_plate_id}", fg=color)

    row = pairs[0]

    q1 = euler_to_quaternion(row.r1_rotation)

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

    if not row.interpolated:
        # We have an exact match!
        # Just a precautionary guard, this should be assured by our SQL
        assert N.allclose(float(row.r1_step), time)
        return __cache(base * q1)

    ## Interpolated rotations

    # Rotation for Q2 timestep
    q2 = euler_to_quaternion(row.r2_rotation)

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
__model_rotation_pairs = get_sql("rotation-pairs-for-model")
__active_plates_sql = get_sql("active-plates-at-time")
__model_plates_sql = get_sql("plates-for-model")
__plate_time_ranges = get_sql("plate-time-ranges")


def plates_for_model(model):
    """Returns a list of plate IDs for a given model"""
    return [k[0] for k in conn.execute(__model_plates_sql, model_name=model)]


def get_all_rotations(
    model, time, verbose=False, active_only=True, plates=None, safe=True, rowset=None
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

    if rowset is None:
        _rowset = conn.execute(
            __tstep_rotation_pairs, time=time, model_name=model
        ).fetchall()
    else:
        _rowset = [
            r
            for r in rowset
            if (r.r1_step == time and r.r2_step is None)
            or (r.r1_step < time and (r.r2_step or -1) > time)
        ]

    if safe:
        check_model_id(model)
    for plate_id in plates:
        q = get_rotation(
            model, plate_id, time, verbose=verbose, rowset=_rowset, safe=False
        )
        if q is None:
            continue
        if N.isnan(q.w):
            continue
        yield plate_id, q


def get_rotation_series(model, *times, **kwargs):
    # Pre-compute plates for speed...
    # LOL this actually makes things slower
    check_model_id(model)

    plate_ages = conn.execute(
        __plate_time_ranges,
        model_name=model,
    ).fetchall()

    rowset = conn.execute(
        __model_rotation_pairs,
        model_name=model,
        early_age=float(max(times)),
        late_age=float(min(times)),
    ).fetchall()
    for t in times:
        t = float(t)
        plates = [p.id for p in plate_ages if p.old_lim > t and p.young_lim < t]
        kwargs["plates"] = plates
        r = get_all_rotations(model, t, safe=False, rowset=rowset, **kwargs)
        yield dict(rotations=list(r), time=t)


def get_plate_rotations(model, plate_id, verbose=False):
    time_step = 1
    time_range = (0, 500)
    time_steps = range(0, 500, 1)
    return ((get_rotation(model, plate_id, t), t) for t in time_steps)
