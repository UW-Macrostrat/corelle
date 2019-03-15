from pg_viewtils import reflect_table
from .database import db

__plate = reflect_table(db, 'plate')
__rotation = reflect_table(db, 'rotation')

def get_rotation(plate_id, time):
    conn = db.connect()

    _ = (__plate.select()
        .where(__plate.c.id==plate_id))
    plate = conn.execute(_)

    res = conn.execute((
        __rotation.select()
        .where(__rotation.c.plate_id==plate_id)
        .order_by(__rotation.c.t_step)))
    euler_pole = (res.latitude, res.longitude, res.angle)

    print(res.fetchall())


def build_cache():
    pass


