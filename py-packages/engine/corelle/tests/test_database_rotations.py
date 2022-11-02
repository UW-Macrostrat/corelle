"""
Tests of rotations using PostGIS functions (to support on-database transformations with cached rotations)
"""

from dataclasses import dataclass
from corelle.math.util import unit_vector
import numpy as N
import quaternion as Q
from shapely import wkt
from corelle.engine.database import db
from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from geoalchemy2.elements import WKBElement
from corelle.math import euler_to_quaternion, quaternion_to_euler, sph2cart, cart2sph
from pytest import mark


def test_postgis_noop_rotation():
    identity = [1, 0, 0, 0]

    sql = "SELECT corelle.rotate_geometry(ST_GeomFromText('POINT(0 0)', 4326), :quaternion)"
    # Get the result of the rotation as a WKBElement
    result = db.session.execute(sql, params=dict(quaternion=identity)).scalar()
    # Convert the WKBElement to a Shapely geometry
    geom = to_shape(WKBElement(result))
    assert N.allclose(N.array(geom.coords), (0, 0))


@dataclass
class RotationTestCase:
    pole: tuple
    angle: float
    start_pos: tuple
    end_pos: tuple


cases = [
    RotationTestCase(
        pole=(0, 0),
        angle=45,
        start_pos=(0, 0),
        end_pos=(0, 0),
    ),
    RotationTestCase(
        pole=(0, 90),
        angle=90,
        start_pos=(0, 0),
        end_pos=(90, 0),
    ),
    RotationTestCase(
        pole=(0, 90),
        angle=120,
        start_pos=(0, 0),
        end_pos=(120, 0),
    ),
    RotationTestCase(
        pole=(90, 0),
        angle=45,
        start_pos=(0, 0),
        end_pos=(0, -45),
    ),
]


@mark.parametrize("case", cases)
def test_postgis_euler_recovery(case):
    sql = "SELECT corelle.quaternion_to_euler(:quaternion)"
    euler = (*case.pole, case.angle)
    q = euler_to_quaternion(euler)
    result = db.session.execute(
        sql, params=dict(quaternion=[q.w, q.x, q.y, q.z])
    ).scalar()
    assert N.allclose(N.degrees(N.array(result)), euler)


@mark.parametrize("case", cases)
def test_postgis_rotations(case):
    sql = "SELECT corelle.rotate_geometry(ST_GeomFromText('POINT(:x :y)', 4326), :quaternion)"
    q = euler_to_quaternion((*case.pole, case.angle))

    v1 = Q.rotate_vectors(q, sph2cart(*case.start_pos))
    v1 = unit_vector(*v1)
    assert N.allclose(cart2sph(v1), case.end_pos)

    result = db.session.execute(
        sql,
        params=dict(
            x=case.start_pos[0], y=case.start_pos[1], quaternion=[q.w, q.x, q.y, q.z]
        ),
    ).scalar()
    geom = to_shape(WKBElement(result))
    assert N.allclose(list(geom.coords), case.end_pos)


# Test a rotation by an Euler angle using the PostGIS function
def test_postgis_euler_rotation():
    pole = (0, 90)
    angle = 45
    start_point = (0, 0)
    end_point = (45, 0)

    euler = (*pole, angle)
    # Confirm that this rotation works in Python
    q = euler_to_quaternion(euler)
    euler1 = quaternion_to_euler(q)
    assert N.allclose(euler, euler1)

    p1 = sph2cart(*start_point)
    p1a = cart2sph(p1)
    assert N.allclose(p1a, start_point)
    v1 = Q.rotate_vectors(q, p1)
    v1 = unit_vector(*v1)
    assert N.allclose(cart2sph(v1), end_point)

    sql = "SELECT corelle.rotate_geometry(ST_GeomFromText('POINT(0 0)', 4326), :quaternion)"
    # Get the result of the rotation as a WKBElement
    result = db.session.execute(
        sql, params=dict(quaternion=[q.w, q.x, q.y, q.z])
    ).scalar()
    # Convert the WKBElement to a Shapely geometry
    geom = to_shape(WKBElement(result))
    assert N.allclose(list(geom.coords), end_point)


geometries = [
    "POINT(0 0)",
    "LINESTRING(0 0, 1 1)",
    "POLYGON((0 0, 0 1, 1 1, 1 0, 0 0))",
    "POLYGON((0 0, 0 1, 1 1, 1 0, 0 0), (0.25 0.25, 0.25 0.75, 0.75 0.75, 0.75 0.25, 0.25 0.25))",
    "MULTIPOINT(0 0, 1 1)",
    "MULTILINESTRING((0 0, 1 1), (2 2, 3 3))",
    "MULTIPOLYGON(((0 0, 0 1, 1 1, 1 0, 0 0)), ((2 2, 2 3, 3 3, 3 2, 2 2)))",
    "MULTIPOLYGON(((0 0, 0 1, 1 1, 1 0, 0 0), (0.25 0.25, 0.25 0.75, 0.75 0.75, 0.75 0.25, 0.25 0.25)), ((2 2, 2 3, 3 3, 3 2, 2 2)))",
]


@mark.parametrize("geom", geometries)
def test_postgis_geometry_rotation(geom):
    q = euler_to_quaternion((0, 90, 45))
    sql = "SELECT corelle.rotate_geometry(ST_GeomFromText(:geom, 4326), :quaternion)"
    with db.session_scope() as session:
        # Check validity of the input geometry
        assert wkt.loads(geom).is_valid

        result = session.execute(
            sql, params=dict(geom=geom, quaternion=[q.w, q.x, q.y, q.z])
        ).scalar()
        geom = to_shape(WKBElement(result))
        print(geom.wkt)
        assert geom.is_valid


@mark.parametrize("geom", geometries)
def test_inverse_rotation(geom):
    q = euler_to_quaternion((0, 90, 45))
    sql = "SELECT corelle.rotate_geometry(corelle.rotate_geometry(ST_GeomFromText(:geom, 4326), :quaternion), corelle.invert_rotation(:quaternion))"
    with db.session_scope() as session:
        # Check validity of the input geometry
        g0 = wkt.loads(geom)
        result = session.execute(
            sql, params=dict(geom=geom, quaternion=[q.w, q.x, q.y, q.z])
        ).scalar()
        geom = to_shape(WKBElement(result))
        assert geom.is_valid

        # Check that the geometry is the same as the original
        assert g0.almost_equals(geom)
