import numpy as N
import quaternion as Q
from sqlalchemy import text, and_, desc
from pg_viewtils import reflect_table
from functools import lru_cache
from time import sleep
from pg_viewtils import relative_path

from .util import unit_vector
from .database import db

__model = reflect_table(db, 'model')
__plate = reflect_table(db, 'plate')
__rotation = reflect_table(db, 'rotation')

def sph2cart(lon,lat):
    _lon = N.radians(lon)
    _lat = N.radians(lat)
    x = N.cos(_lat)*N.cos(_lon)
    y = N.cos(_lat)*N.sin(_lon)
    z = N.sin(_lat)
    return unit_vector(x,y,z)

def cart2sph(unit_vec):
    (x, y, z) = unit_vec
    lat = N.arcsin(z)
    lon = N.arctan2(y, x)
    return N.degrees(lon), N.degrees(lat)

def euler_to_quaternion(euler_pole):
    lat, lon, angle = [float(i) for i in euler_pole]
    angle = N.radians(angle)
    w = N.cos(angle/2)
    v = sph2cart(lon, lat)*N.sin(angle/2)
    return N.quaternion(w, *v)

def quaternion_to_euler(q):
    angle = 2*N.arccos(q.w)
    lon, lat = cart2sph(q.vec/N.sin(angle/2))
    return lat, lon, N.degrees(angle)

conn = db.connect()

class LoopError(Exception):
    def __init__(self, plate_id):
        super().__init__(self, f"Plate {plate_id} caused an infinite loop")
        self.plate_id = plate_id

class Stack(object):
    def __init__(self, loops=[]):
        self.ids = []
        self.loops = loops

def get_rotation(model_name, plate_id, time, **kwargs):
    model_id = db.execute(
        __model.select(__model.c.name == model_name)).scalar()

    model_query = __rotation.select().where(__model.c.id == model_id)

    loops = []
    for i in range(100):
        # Try 100 times
        try:
            return __get_rotation([], loops, model_query, plate_id, time, **kwargs)
        except LoopError as err:
            loops.append(err.plate_id)

# Cache this expensive, recursive function.
def __get_rotation(stack, loops, model_query, plate_id, time, verbose=False, depth=0):
    time = float(time)
    # Fetches a sequence of rotations per unit time
    if verbose:
        print(" "*depth, plate_id, time)

    if plate_id is None or plate_id == 0:
        return N.quaternion(1,0,0,0)

    base_query = model_query.where(__rotation.c.plate_id==plate_id)
    _t = __rotation.c.t_step
    rotations_before = base_query.where(_t <= time).order_by(desc(_t))
    rotations_after = base_query.where(_t > time).order_by(_t)

    def __get_row_rotation(row):
        if row.ref_plate_id in loops:
            # We don't want to get into an endless loop
            return None
        if row.ref_plate_id in stack:
            ix = stack.index(row.ref_plate_id)
            raise LoopError(stack[ix])

        base = __get_rotation(
            stack+[row.plate_id],
            loops, model_query,
            row.ref_plate_id, row.t_step,
            verbose=verbose,
            depth=depth+1)

        q1 = euler_to_quaternion([
            float(i) for i in [row.latitude,row.longitude,row.angle]
        ])
        return q1 * base

    rotation = None
    rows = db.execute(rotations_before).fetchall()
    prev_step = 0
    q_before = None
    for r in rows:
        q_before = __get_row_rotation(r)
        if q_before is None:
            continue

        if r.t_step == time:
            return q_before
            # The rotation is simply q_before
        prev_step = float(r.t_step)
        break
    q_before = N.quaternion(1,0,0,0)

    rows = db.execute(rotations_after).fetchall()
    for r in rows:
        q_after = __get_row_rotation(r)
        if q_after is None:
            continue
        # Proportion of time between steps elapsed
        proportion = (time-prev_step)/(float(r.t_step)-prev_step)
        try:
            return q_before*(1-proportion) + q_after*proportion
        except TypeError:
            import IPython; IPython.embed(); raise

    return N.quaternion(1,0,0,0)



def get_all_rotations(model, time, verbose=False):
    fn = relative_path(__file__, 'query', 'active-plates-at-time.sql')
    sql = text(open(fn).read())
    results = conn.execute(sql, time=time, model_name=model)
    for res in results:
        plate_id = res[0]
        q = get_rotation(model, plate_id, time, verbose=verbose)
        if N.isnan(q.w):
            continue
        yield plate_id, q

def build_cache():
    pass
