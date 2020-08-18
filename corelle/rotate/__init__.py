import numpy as N
import quaternion as Q
from pg_viewtils import reflect_table, relative_path
from click import secho

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


def get_rotation(*args, **kwargs):
    loops = []
    for i in range(100):
        # Try 100 times
        try:
            return __get_rotation([], loops, *args, **kwargs)
        except LoopError as err:
            loops.append(err.plate_id)


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


# Cache this expensive, recursive function.
def get_rotation(model_name, plate_id, time, verbose=False, depth=0):
    time = float(time)
    cache_args = (model_name, plate_id, time)
    if cache_args in cache:
        return cache[cache_args]

    __cache = lambda q: build_cache(q, cache_args)

    # Make sure our model id actually exists
    id = model_id(model_name)
    if id is None:
        raise RotationError("Unknown model id")

    prefix = " " * depth
    if verbose:
        secho(prefix + str(plate_id))

    if plate_id is None or plate_id == 0:
        return __cache(N.quaternion(1, 0, 0, 0))

    __sql = get_sql("rotation-pairs")
    params = dict(plate_id=plate_id, model_name=model_name, time=time)

    pairs = db.execute(__sql, **params).fetchall()
    if len(pairs) == 0:
        return None
    if verbose:
        for i, pair in enumerate(pairs):
            color = "green" if i == 0 else "gray"
            secho(prefix + f"{pair.plate_id} → {pair.ref_plate_id}", fg=color)
    row = pairs[0]

    q1 = euler_to_quaternion(row.r1_rotation)

    base = get_rotation(
        model_name, row.ref_plate_id, time, verbose=verbose, depth=depth + 1
    )
    if base is None:
        return __cache(None)

    r1_step = float(row.r1_step)

    if not row.interpolated:
        # We have an exact match!
        # Just a precautionary guard, this should be assured by our SQL
        assert N.allclose(r1_step, time)
        return __cache(base * q1)

    r2_step = float(row.r2_step)

    ## Interpolated rotations
    q2 = euler_to_quaternion(row.r2_rotation)
    res = Q.slerp(q1, q2, r1_step, r2_step, time)
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


def get_all_rotations(model, time, verbose=False, active_only=True):
    if active_only:
        sql = get_sql("active-plates-at-time")
        results = conn.execute(sql, time=time, model_name=model)
    else:
        sql = get_sql("plates-for-model")
        results = conn.execute(sql, model_name=model)
    for res in results:
        plate_id = res[0]
        q = get_rotation(model, plate_id, time, verbose=verbose)
        if q is None:
            continue
        if N.isnan(q.w):
            continue
        yield plate_id, q


def get_plate_rotations(model, plate_id, verbose=False):
    time_step = 1
    time_range = (0, 500)
    time_steps = range(0, 500, 1)
    return ((get_rotation(model, plate_id, t), t) for t in time_steps)
