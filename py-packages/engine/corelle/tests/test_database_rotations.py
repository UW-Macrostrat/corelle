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
from .rotation_testing_functions import rotation_functions, postgis_rotation_functions


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
    start_pos, end_pos = case.start_pos, case.end_pos
    if inverse:
        start_pos, end_pos = case.end_pos, case.start_pos
        q = q.inverse()

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
@mark.parametrize("func", rotation_functions)
def test_arbitrary_vector_rotations(vector, direction, func):
    a = N.array(vector).astype(N.float64)
    a /= N.linalg.norm(a)
    q = Q.from_float_array(a)

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
