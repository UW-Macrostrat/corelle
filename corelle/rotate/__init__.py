import numpy as N
import quaternion as Q
from pg_viewtils import reflect_table, relative_path
from .math import cart2sph, sph2cart, euler_to_quaternion, quaternion_to_euler
from ..query import get_sql
from ..database import db

__model = reflect_table(db, 'model')
__plate = reflect_table(db, 'plate')
__rotation = reflect_table(db, 'rotation')

conn = db.connect()

class UndefinedRotationError(Exception):
    def __init__(self, plate_id, time):
        super().__init__(self, f"No rotation found for plate {plate_id} at time {time}")
        self.plate_id = plate_id
        self.time = time

class LoopError(Exception):
    def __init__(self, plate_id):
        super().__init__(self, f"Plate {plate_id} caused an infinite loop")
        self.plate_id = plate_id

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

# Cache this expensive, recursive function.
def __get_rotation(stack, loops, model_name, plate_id, time, verbose=False, depth=0):
    time = float(time)
    cache_args = (model_name, plate_id, time)
    if cache_args in cache:
        return cache[cache_args]

    if verbose:
        print((" "*depth)[1:], plate_id, time)

    if plate_id is None or plate_id == 0:
        return N.quaternion(1,0,0,0)

    __sql = get_sql("rotation-pairs")
    params = dict(
        plate_id = plate_id,
        model_name = model_name,
        time = time)

    def __cache(q):
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

    pairs = db.execute(__sql, **params).fetchall()
    if len(pairs) == 0:
        return None
        #raise UndefinedRotationError(plate_id, time)
    row = pairs[0]

    q1 = euler_to_quaternion(row.r1_rotation)

    base = __get_rotation(
        stack+[row.plate_id],
        loops, model_name,
        row.ref_plate_id, time,
        verbose=verbose,
        depth=depth+1)
    if base is None:
        base = N.quaternion(1,0,0,0)

    if not row.interpolated:
        # Just a precautionary guard, this should be assured by our SQL
        assert row.r1_step == time
        return __cache(base*q1)

    ## Interpolated rotations
    q2 = euler_to_quaternion(row.r2_rotation)
    res = Q.slerp(q1, q2, float(row.r1_step), float(row.r2_step), float(time))
    return __cache(res)


def plates_for_model(model):
    sql = get_sql('plates-for-model')
    for row in conn.execute(sql, model_name=model):
        yield row[0]

def rotate_point(point, model, time):
    if time == 0:
        return point
    sql = get_sql('plate-for-point')
    plate_id = conn.execute(sql,
        lon=point[0],
        lat=point[1],
        model_name=model,
        time=time).scalar()
    if plate_id is None: return None
    q = get_rotation(model, plate_id, time)
    v0 = sph2cart(*point)
    v1 = Q.rotate_vectors(q, v0)
    return cart2sph(v1)

def get_all_rotations(model, time, verbose=False):
    sql = get_sql('active-plates-at-time')
    results = conn.execute(sql, time=time, model_name=model)
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
    time_range = (0,500)
    time_steps = range(0,500,1)
    return ((get_rotation(model, plate_id, t), t) for t in time_steps)
