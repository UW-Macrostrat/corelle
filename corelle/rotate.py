import numpy as N
import quaternion as Q
from sqlalchemy import text
from pg_viewtils import reflect_table
from .database import db

__plate = reflect_table(db, 'plate')
__rotation = reflect_table(db, 'rotation')

def euler_to_quaternion(euler_pole):
    angles = N.radians(euler_pole)
    return Q.from_euler_angles(angles)

def get_rotation(plate_id, time):
    conn = db.connect()

    _ = "SELECT (rotation_sequence(:plate_id, :time)).*"
    res = conn.execute(text(_), plate_id=plate_id, time=time)

    for plate in plates:
        pass

    print(res.fetchall())


def build_cache():
    pass


