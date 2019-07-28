import numpy as N
import quaternion as Q
from sqlalchemy import text
from pg_viewtils import reflect_table
from functools import lru_cache
from time import sleep
from pg_viewtils import relative_path


from .util import unit_vector
from .database import db

__plate = reflect_table(db, 'plate')
__rotation = reflect_table(db, 'rotation')

def sph2cart(lat, lon):
    _lon = N.radians(lon)
    _lat = N.radians(lat)
    x = N.cos(_lon)
    y = N.sin(_lon)
    z = N.sin(_lat)
    return unit_vector(x,y,z)

def euler_to_quaternion(euler_pole):
    lat, lon, angle = [float(i) for i in euler_pole]
    angle = N.radians(angle)
    v = sph2cart(lat,lon)
    return N.quaternion(angle, *v)

conn = db.connect()

# Cache this expensive, recursive function.
@lru_cache(maxsize=50000)
def get_rotation(model_name, plate_id, time, depth=0, verbose=False):
    fn = relative_path(__file__, 'query', 'rotation-sequence.sql')
    sql = text(open(fn).read())
    res = conn.execute(sql, model_name=model_name, plate_id=plate_id, time=time)
    rotations = res.fetchall()

    transform = N.quaternion(1,0,0,0)

    if verbose:
        print(" "*depth, plate_id)
    for r in rotations:
        if r.ref_plate_id:
            base = get_rotation(
                    model_name,
                    r.ref_plate_id,
                    r.t_end,
                    depth=depth+1)
        else:
            base = N.quaternion(1,0,0,0)

        q = euler_to_quaternion([
            float(i) for i in r.euler_angle
        ])
        transform *= base*q

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
