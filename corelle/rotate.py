import numpy as N
import quaternion as Q
from sqlalchemy import text
from pg_viewtils import reflect_table
from .database import db
from functools import lru_cache

__plate = reflect_table(db, 'plate')
__rotation = reflect_table(db, 'rotation')

def euler_to_quaternion(euler_pole):
    angles = N.radians(euler_pole)
    return Q.from_euler_angles(angles)

conn = db.connect()

@lru_cache(maxsize=5000)
def get_rotation(plate_id, time, depth=0):
    _ = "SELECT (rotation_sequence(:plate_id, :time)).*"
    res = conn.execute(text(_), plate_id=plate_id, time=time)
    rotations = res.fetchall()

    transform = N.quaternion(1,0,0,0)

    for r in rotations:
        if r.ref_plate_id:
            print(" "*depth, plate_id, r.ref_plate_id)
            base = get_rotation(
                    r.ref_plate_id, time,
                    depth = depth + 1
                )
        else:
            base = N.quaternion(1,0,0,0)
        q = euler_to_quaternion([
            float(i) for i in r.euler_angle
        ])
        transform *= base*q
    return transform

def build_cache():
    pass


