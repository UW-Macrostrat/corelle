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

    __before = get_sql("rotations-before")
    __after = get_sql("rotations-after")
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

    def __get_row_rotation(row):

        if row.ref_plate_id in loops:
            # We don't want to get into an endless loop
            raise LoopError(row.ref_plate_id)
        if row.ref_plate_id in stack:
            ix = stack.index(row.ref_plate_id)
            raise LoopError(stack[ix])

        q = euler_to_quaternion([row.latitude,row.longitude,row.angle])
        if q is None: return None

        base = __get_rotation(
            stack+[row.plate_id],
            loops, model_name,
            row.ref_plate_id, time,
            verbose=verbose,
            depth=depth+1)
        if base is None:
            base = N.quaternion(1,0,0,0)
        return q*base

    rotation = None
    rows = db.execute(__before, **params).fetchall()
    prev_step = 0
    q_before = None
    for r in rows:
        try:
            q_before = __get_row_rotation(r)
        except LoopError as err:
            if err.plate_id == r.ref_plate_id:
                continue
            else:
                print("Raising err")
                raise err

        if q_before is None:
            return None

        if r.t_step == time:
            return __cache(q_before)
            # The rotation is simply q_before
        prev_step = float(r.t_step)
        r0 = r.ref_plate_id
        break

    if q_before is None:
        q_before = N.quaternion(1,0,0,0)

    rows = db.execute(__after, **params).fetchall()
    for r in rows:
        try:
            q_after = __get_row_rotation(r)
        except LoopError as err:
            if err.plate_id == r.ref_plate_id:
                continue
            else:
                raise err
        # Proportion of time between steps elapsed
        # Interpolate between these two rotors (GPlates uses this linear interpolation)
        res = Q.slerp(q_before,q_after, float(prev_step), float(r.t_step), float(time))
        return __cache(res)

    return None

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
