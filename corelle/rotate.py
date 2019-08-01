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
    pass

class Stack(object):
    def __init__(self, loops=[]):
        self.ids = []
        self.loops = loops

def get_rotation(model_name, plate_id, time, **kwargs):
    model_id = db.execute(
        __model.select(__model.c.name == model_name)).scalar()

    model_query = __rotation.select().where(__model.c.id == model_id)

    stack = Stack()
    for i in range(100):
        # Try 100 times
        try:
            return __get_rotation(stack, model_query, plate_id, time, **kwargs)
        except LoopError as err:
            loops = stack.loops
            stack = Stack(loops = loops)

# Cache this expensive, recursive function.
@lru_cache(maxsize=5000)
def __get_rotation(stack, model_query, plate_id, time, depth=0, verbose=False):
    time = float(time)
    # Fetches a sequence of rotations per unit time

    base_query = model_query.where(__rotation.c.plate_id==plate_id)
    _t = __rotation.c.t_step
    rotations_before = base_query.where(_t <= time).order_by(desc(_t))
    rotations_after = base_query.where(_t > time).order_by(_t)

    rotation = None
    for r in db.execute(rotations_before):
        if r.ref_plate_id in stack.loops:
            # We don't want to get into an endless loop
            continue
        if r.ref_plate_id in stack.ids:
            stack.loops.append(r.ref_plate_id)
            raise LoopError("We have found an infinite loop")
        base = N.quaternion(1,0,0,0)
        if r.ref_plate_id is not None:
            base = __get_rotation(stack, model_query, r.ref_plate_id, time)

        q_before = euler_to_quaternion([
            float(i) for i in [r.latitude,r.longitude,r.angle]
        ])*base

        if r.t_step == time:
            rotation = q_before
            # The rotation is simply q_before
        prev_step = float(r.t_step)

    for r in db.execute(rotations_after):
        if rotation is not None:
            break
        if r.ref_plate_id in stack.loops:
            # We don't want to get into an endless loop
            continue
        if r.ref_plate_id in stack.ids:
            stack.loops.append(r.ref_plate_id)
            raise LoopError("We have found an infinite loop")
        base = N.quaternion(1,0,0,0)
        if r.ref_plate_id is not None:
            base = __get_rotation(stack, model_query, r.ref_plate_id, time)

        q_after = euler_to_quaternion([
            float(i) for i in [r.latitude,r.longitude,r.angle]
        ])*base
        # Proportion of time between steps elapsed
        proportion = (time-prev_step)/(float(r.t_step)-prev_step)
        rotation = q_before*(1-proportion) + q_after*proportion

    stack.ids.append(plate_id)
    if rotation is None:
        rotation = N.quaternion(1,0,0,0)
    return rotation

def get_all_rotations(model, time):
    fn = relative_path(__file__, 'query', 'active-plates-at-time.sql')
    sql = text(open(fn).read())
    results = conn.execute(sql, time=time, model_name=model)
    for res in results:
        plate_id = res[0]
        q = get_rotation(model, plate_id, time)
        if N.isnan(q.w):
            continue
        yield plate_id, q

def build_cache():
    pass
