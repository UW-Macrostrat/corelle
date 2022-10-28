"""
Tests of rotations using PostGIS functions (to support on-database transformations with cached rotations)
"""

import numpy as N
import quaternion as Q
from corelle.server.database import db
from geoalchemy2 import Geometry
from corelle.math import euler_to_quaternion, sph2cart, cart2sph

# Test a rotation by an Euler angle using the PostGIS function
def test_euler_rotation():
    pole = (0, 90)
    angle = 90
    start_point = (0, 0)
    end_point = (90, 0)

    # Confirm that this rotation works in Python
    q = euler_to_quaternion((*pole, angle))
    p1 = sph2cart(*start_point)
    v1 = Q.rotate_vectors(q, p1)
    assert N.allclose(cart2sph(v1), end_point)

    sql = "SELECT corelle.rotate_geometry(ST_GeomFromText('POINT(0 0)', 4326), :quaternion)"
    result = db.session.execute(sql).scalar()
    assert N.allclose(result.coords[0], end_point)
