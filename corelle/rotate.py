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

class Stack(object):
    def __init__(self):
        self.ids = []
        self.rotations = []
        self.loops = []

    def push(self, row, rotation):
        if row.ref_plate_id in ids:
            # There is a loop! we need to go back to before the loop
            # Go back to the start of the loop
            self.truncate_before(row.ref_plate_id)
        self.ids.append(row.ref_plate_id)
        self.rotations.append(rotation)

    def truncate_before(self, id):
        ix = self.ids.index(id)
        self.loops.append(self.ids[ix])
        self.ids = self.ids[:ix]
        self.rotations = self.rotations[:ix]
        self.items = self.items[:ix]

    def next_id(self):
        return self.ids[-1]


# Cache this expensive, recursive function.
@lru_cache(maxsize=5000)
def __get_rotation(stack, model_query, plate_id, time, depth=0, verbose=False):
    time = float(time)
    # Fetches a sequence of rotations per unit time

    base_query = model_query.filter(__rotation.c.plate_id==plate_id)
    _t = __rotation.c.t_step
    rotations_before = base_query.filter(_t <= time).order_by(desc(_t))
    rotations_after = base_query.filter(_t > time).order_by(_t)

    prev_step = None
    rotation = None
    for r in rotations_before:
        if stack.is_loop(r.ref_plate_id):
            # We don't want to get into an endless loop
            continue
        q_before = euler_to_quaternion([
            float(i) for i in [r.latitude,r.longitude,r.angle]
        ])

        base = __get_rotation(stack, model_query, stack.next_id(), time)
        if r.t_step == time:
            # The rotation is simply q_before

        prev_step = float(r.t_step)
        break

    if not prev_step:
        return None

    for r in rotations_after:
        if rotation is not None:
            # We don't need to modify our rotation
            break
        if stack.is_loop(r.ref_plate_id):
            continue
        q_after = euler_to_quaternion([
            float(i) for i in [r.latitude,r.longitude,r.angle]
        ])
        # Proportion of time between steps elapsed
        proportion = (time-prev_step)/(float(r.t_step)-prev_step)
        rotation = q_before*(1-proportion) + q_after*proportion


    stack.push(rotation, q)
    return __get_rotation(stack, model_query, stack.next_id(), time)



    rotations = res.fetchall()
    assert len(rotations) <= 2

    if len(rotations) == 0:
        return None

    transform = N.quaternion(1,0,0,0)

    if verbose:
        print(" "*depth, plate_id)

    for i,r in enumerate(rotations):
        base = N.quaternion(1,0,0,0)
        t_step = float(r.t_step)
        if i == 1:
            # We are on the second step
            assert t_step > time
            t_step = time

        if r.ref_plate_id:
            # This rotation is based on another plate
            base = get_rotation(
                model_name,
                r.ref_plate_id,
                t_step,
                depth=depth+1,
                verbose=verbose)

        # Rotate the plate to the base rotation (for the end of time period)
        q = euler_to_quaternion([
            float(i) for i in [r.latitude,r.longitude,r.angle]
        ])
        q *= base

        if t_step > time:
            # Proportion of time between steps elapsed
            proportion = (time-float(r.prev_step))/(float(r.t_step)-float(r.prev_step))
            q = transform*(1-proportion) + q*proportion
        # relative = rotation/transform
        # reduced_angle = Q.as_rotation_vector(relative)*proportion
        # rotation = Q.from_rotation_vector(reduced_angle)*transform

        transform = q

    return transform

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
