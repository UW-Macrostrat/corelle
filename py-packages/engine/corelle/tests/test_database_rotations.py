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
from corelle.math import euler_to_quaternion, sph2cart, cart2sph
from pytest import mark
from corelle.engine.rotate import get_plate_id, get_rotation
from .rotation_testing_functions import (
    rotation_functions,
    postgis_rotation_functions,
    swing_twist_decomposition,
)


def test_postgis_noop_rotation():
    identity = [1, 0, 0, 0]

    sql = "SELECT corelle.rotate_geometry(ST_GeomFromText('POINT(0 0)', 4326), :quaternion)"
    # Get the result of the rotation as a WKBElement
    result = db.session.execute(
        sql, params=dict(quaternion=list(N.array(identity, dtype=float)))
    ).scalar()
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
    # First, a no-op rotation
    RotationTestCase(pole=(0, 0), angle=0, start_pos=(42, 20), end_pos=(42, 20)),
    RotationTestCase(
        pole=(0, 90),
        angle=90,
        start_pos=(0, 0),
        end_pos=(90, 0),
    ),
    RotationTestCase(
        pole=(0, 90),
        angle=-90,
        start_pos=(0, 0),
        end_pos=(-90, 0),
    ),
    RotationTestCase(
        pole=(0, 0),
        angle=45,
        start_pos=(0, 0),
        end_pos=(0, 0),
    ),
    RotationTestCase(
        pole=(0, 0),
        angle=90,
        start_pos=(2, 0),
        end_pos=(0, 2),
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
    if case.angle == 0:
        assert result is None
    else:
        q1 = euler_to_quaternion(N.degrees([float(i) for i in result]))
        assert Q.allclose(q, q1, atol=1e-6)
        # assert N.allclose(N.degrees([float(i) for i in result]), euler)


@mark.parametrize("func", rotation_functions)
@mark.parametrize("case", cases)
@mark.parametrize("inverse", [False, True])
def test_postgis_rotations(func, case, inverse):
    q = euler_to_quaternion((*case.pole, case.angle))
    if inverse:
        start_pos, end_pos = case.end_pos, case.start_pos
        q = q.inverse()
    else:
        start_pos, end_pos = case.start_pos, case.end_pos

    coords = func(start_pos, q)
    assert N.allclose(coords, end_pos)


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


@mark.parametrize("func", postgis_rotation_functions)
@mark.parametrize("geom", geometries)
def test_postgis_geometry_rotation(func, geom):
    q = euler_to_quaternion((0, 90, 45))
    sql = f"SELECT {func}(ST_GeomFromText(:geom, 4326), :quaternion)"
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
def test_postgis_geometry_rotation_invalid(geom):
    q = euler_to_quaternion((0, 90, 45))
    sql = f"SELECT corelle.rotate_geometry(ST_GeomFromText(:geom, 4326), :quaternion)"
    with db.session_scope() as session:
        g0 = wkt.loads(geom)
        result = session.execute(
            sql, params=dict(geom=geom, quaternion=[q.w, q.x, q.y, q.z])
        ).scalar()
        assert result is not None
        geom = to_shape(WKBElement(result))
        assert geom.is_valid


def _rotate_geom(geom, q, func="corelle.rotate_geometry"):
    sql = f"SELECT {func}(ST_GeomFromText(:geom, 4326), :quaternion)"
    with db.session_scope() as session:
        result = session.execute(
            sql, params=dict(geom=geom, quaternion=[q.w, q.x, q.y, q.z])
        ).scalar()
        assert result is not None
        return to_shape(WKBElement(result))


@mark.parametrize("geom", geometries)
def compare_rotation_functions(geom):
    q = euler_to_quaternion((0, 90, 45))
    f1 = _rotate_geom(geom, q, "corelle.rotate_geometry")
    f2 = _rotate_geom(geom, q, "corelle.rotate_geometry_pointwise")
    assert f1.almost_equals(f2)


# Right now this doesn't work with the Proj implementation
@mark.parametrize("func", postgis_rotation_functions)
@mark.parametrize("geom", geometries)
def test_inverse_rotation(geom, func):
    q = euler_to_quaternion((0, 90, 45))
    sql = f"""SELECT {func}(
        {func}(ST_GeomFromText(:geom, 4326), :quaternion),
        corelle.invert_rotation(:quaternion)
    )"""
    with db.session_scope() as session:
        # Check validity of the input geometry
        g0 = wkt.loads(geom)
        result = session.execute(
            sql, params=dict(geom=geom, quaternion=[q.w, q.x, q.y, q.z])
        ).scalar()
        assert result is not None
        geom = to_shape(WKBElement(result))
        assert geom.is_valid

        print(g0.wkt, geom.wkt)

        # Check that the geometry is the same as the original
        assert g0.almost_equals(geom)


def make_quaternion(*arr):
    a = N.array(arr).astype(N.float64)
    a /= N.linalg.norm(a)
    return Q.from_float_array(a)


quaternions = [
    make_quaternion(*q)
    for q in [
        (1, 4, 0, 0),
        (1, 1, 0, 1),
        (1, 4, 1, 0),
        (4, 0, 1, 1),
    ]
]

directions = [(0, 0), (90, 0), (45, 20), (-80, -15), (120, 40)]


def quaternion_norm(q):
    return N.sqrt(N.sum(q * q))


def test_identity_quaternion_norm():
    q = make_quaternion(1, 0, 0, 0)
    assert q.norm() == 1


identity_quaternion = Q.from_float_array([1, 0, 0, 0])


def decompose_quaternion(q, direction):  # pragma: no cover
    """Decompose a quaternion into a rotation around a given direction.
    Returns:
        twist: The rotation around the direction
        swing: The rotation around the plane perpendicular to the direction
    """
    ra = q.vec
    # Projection of the quaternion vector along direction
    prod = N.dot(ra, direction)
    proj = prod * direction

    twist = Q.from_float_array(N.hstack((q.w, proj)) * N.sign(prod))
    if twist.norm() == 0:
        return identity_quaternion, q
    twist = twist.normalized()

    swing = q * twist.conjugate()
    assert N.allclose(swing.vec.dot(direction), 0)
    assert N.allclose(unit_vector(*twist.vec), direction)

    return twist, swing


def quaternion_decomposition(q):
    x_axis = N.array([1, 0, 0])
    y_axis = N.array([0, 1, 0])
    z_axis = N.array([0, 0, 1])

    x, rest = decompose_quaternion(q, x_axis)
    y, rest_1 = decompose_quaternion(rest, y_axis)

    assert rest.vec.dot(x_axis) == 0
    assert rest_1.vec.dot(y_axis) == 0
    # assert rest_1.vec.dot(x_axis) == 0
    # assert rest_1.vec.dot(z_axis) == N.linalg.norm(rest_1.vec)
    # z, rest = decompose_quaternion(rest, z_axis)
    return x, y, rest_1


@mark.parametrize("q", quaternions)
def test_quaternion_decomposition(q):
    """Test that the quaternion decomposition into x, y, and z-axis rotations"""

    assert N.allclose(q.norm(), 1)

    # Decompose the quaternion into x, y, and z-axis rotations
    x, y, z = quaternion_decomposition(q)

    reconstituted = z * y * x

    # Check that the decomposition is correct
    assert N.allclose(q, reconstituted)


@mark.parametrize("q", quaternions)
def test_swing_twist_decomposition(q):
    """Test that the quaternion decomposition into 'swing' and 'twist' components is correct."""
    swing, twist = swing_twist_decomposition(q)
    assert N.allclose(twist * swing, q)


@mark.parametrize("q", quaternions)
@mark.parametrize("direction", directions)
def test_postgis_vector_rotation(q, direction):
    vx = sph2cart(*direction)
    vx0 = Q.rotate_vectors(q, vx)

    result = db.session.execute(
        "SELECT corelle.rotate_vector(:vector, :quaternion)::float[]",
        params=dict(quaternion=[q.w, q.x, q.y, q.z], vector=list(vx)),
    ).scalar()
    coords = list(result)
    assert N.allclose(vx0, coords)


@mark.parametrize("q", quaternions)
@mark.parametrize("direction", directions)
@mark.parametrize("func", rotation_functions)
def test_arbitrary_vector_rotations(q, direction, func):
    vx = sph2cart(*direction)
    vx0 = Q.rotate_vectors(q, vx)

    coords = func(direction, q)
    if len(coords) == 1:
        coords = coords[0]
    vx1 = sph2cart(*coords)
    assert N.allclose(vx0, vx1)


@mark.parametrize("func", rotation_functions)
def test_database_against_web_service(gplates_web_service_testcase, func):
    case = gplates_web_service_testcase
    assert len(case.current) == len(case.rotated)
    for c0, ct in zip(case.current, case.rotated):
        plate_id = get_plate_id(c0, case.model, case.time)
        q = get_rotation(case.model, plate_id, case.time, safe=False)
        p1 = func(c0, q)
        assert N.allclose(p1, ct, atol=0.01)
