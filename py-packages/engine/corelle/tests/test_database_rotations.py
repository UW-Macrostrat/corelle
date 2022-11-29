"""
Tests of rotations using PostGIS functions (to support on-database transformations with cached rotations)
"""

from dataclasses import dataclass
from corelle.math.util import unit_vector
import numpy as N
import quaternion as Q
from corelle.engine.database import db
from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from geoalchemy2.elements import WKBElement
from corelle.math import euler_to_quaternion, quaternion_to_euler, sph2cart, cart2sph
from pytest import mark
from .utils import get_geojson, get_coordinates
from corelle.engine.rotate import get_plate_id, get_rotation


def test_postgis_noop_rotation():
    identity = [1, 0, 0, 0]

    sql = "SELECT corelle.rotate_geometry(ST_GeomFromText('POINT(0 0)', 4326), :quaternion)"
    # Get the result of the rotation as a WKBElement
    result = db.session.execute(
        sql, params=dict(quaternion=list(N.array(identity, dtype=float)))
    ).scalar()
    # Convert the WKBElement to a Shapely geometry
    geom = to_shape(WKBElement(result))
    assert N.allclose(geom.coords, (0, 0))


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


def rotate_point(point, quaternion):
    # Rotate a point using the PostGIS function
    sql = "SELECT corelle.rotate_geometry(ST_MakePoint(:lon, :lat), :quaternion)"
    # Get the result of the rotation as a WKBElement
    result = db.session.execute(
        sql,
        params=dict(
            lon=point[0],
            lat=point[1],
            quaternion=[quaternion.w, quaternion.x, quaternion.y, quaternion.z],
        ),
    ).scalar()
    # Convert the WKBElement to a Shapely geometry
    geom = to_shape(WKBElement(result))
    return list(geom.coords)


@mark.parametrize("case", cases)
def test_postgis_rotations(case):
    sql = "SELECT corelle.rotate_geometry(ST_GeomFromText('POINT(:x :y)', 4326), :quaternion)"
    q = euler_to_quaternion((*case.pole, case.angle))

    v1 = Q.rotate_vectors(q, sph2cart(*case.start_pos))
    v1 = unit_vector(*v1)
    assert N.allclose(cart2sph(v1), case.end_pos)

    coords = rotate_point(case.start_pos, q)
    assert N.allclose(coords, case.end_pos)


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

    coords = rotate_point(start_point, q)
    # Convert the WKBElement to a Shapely geometry
    assert N.allclose(coords, end_point)


vectors = [
    (1, 4, 0, 0),
    (1, 1, 0, 1),
    (1, 4, 1, 0),
    (4, 0, 1, 1),
]

directions = [(0, 0), (90, 0), (45, 20), (-80, -15), (120, 40)]


@mark.parametrize("vector", vectors)
@mark.parametrize("direction", directions)
def test_postgis_vector_rotation(vector, direction):
    a = N.array(vector).astype(N.float64)
    a /= N.linalg.norm(a)
    q = Q.from_float_array(a)

    vx = sph2cart(*direction)
    vx0 = Q.rotate_vectors(q, vx)

    result = db.session.execute(
        "SELECT corelle.rotate_vector(:vector, :quaternion)::float[]",
        params=dict(quaternion=[q.w, q.x, q.y, q.z], vector=list(vx)),
    ).scalar()
    coords = list(result)
    assert N.allclose(vx0, coords)


@mark.parametrize("vector", vectors)
@mark.parametrize("direction", directions)
def test_arbitrary_vector_rotations(vector, direction):
    a = N.array(vector).astype(N.float64)
    a /= N.linalg.norm(a)
    q = Q.from_float_array(a)

    vx = sph2cart(*direction)
    vx0 = Q.rotate_vectors(q, vx)

    coords = rotate_point(direction, q)
    assert len(coords) == 1
    vx1 = sph2cart(*coords[0])
    assert N.allclose(vx0, vx1)


times = [0, 1, 10, 120, 140, 200]


@mark.parametrize("time", times)
def test_database_against_gplates_web_service(time):
    req = get_geojson("seton2012-gws-request")
    res = get_geojson(f"seton2012-gws-response-{time}")

    now = get_coordinates(req)
    prev = get_coordinates(res)
    assert len(now) == len(prev)

    for c0, ct in zip(now, prev):
        model = "Seton2012"
        plate_id = get_plate_id(c0, model, time)
        q = get_rotation(model, plate_id, time, safe=False)
        p1 = rotate_point(c0, q)
        assert N.allclose(p1, ct, atol=0.01)
