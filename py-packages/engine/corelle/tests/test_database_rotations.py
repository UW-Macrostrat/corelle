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


def rotate_point(point, quaternion, func="corelle.rotate_geometry"):
    # Rotate a point using the PostGIS function
    sql = f"SELECT {func}(ST_SetSRID(ST_MakePoint(:lon, :lat), 4326), :quaternion)"
    # Get the result of the rotation as a WKBElement
    result = db.session.execute(
        sql,
        params=dict(
            lon=point[0],
            lat=point[1],
            quaternion=[quaternion.w, quaternion.x, quaternion.y, quaternion.z],
        ),
    ).scalar()
    assert result is not None
    # Convert the WKBElement to a Shapely geometry
    geom = to_shape(WKBElement(result))
    return list(geom.coords)


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


def rotate_with_ob_tran(start_pos, lon_p, lat_p, lon_0):
    proj_string = f"+proj=ob_tran +o_proj=longlat +o_lon_p={lon_p}r +o_lat_p={lat_p}r +lon_0={lon_0}r"
    sql = "SELECT ST_Transform(ST_SetSRID(ST_MakePoint(:x, :y), 4326), :proj_string)"
    # Get the result of the rotation as a WKBElement
    with db.session_scope() as session:
        result = session.execute(
            sql,
            params=dict(
                x=start_pos[0],
                y=start_pos[1],
                proj_string=proj_string,
            ),
        ).scalar()
    # Convert the WKBElement to a Shapely geometry
    geom = to_shape(WKBElement(result))
    return list(geom.coords)


def rotate_postgis_ob_tran(point, q):
    # Step 1: Take the pole and rotate it along a meridian
    # to a new location (pole is at some point on the equator)

    # Check that we can recover the angle including sign from the quaternion
    # angle = 2 * N.arccos(q.w)
    # assert N.allclose(angle, N.radians(case.angle))

    # Find new pole location
    orig_pole = sph2cart(0, 90)
    new_pole = Q.rotate_vectors(q, orig_pole)
    new_pole_sph = cart2sph(new_pole)

    pole_rotation_angle = N.degrees(N.arccos(N.dot(orig_pole, new_pole)))

    print("Pole rotation angle:", pole_rotation_angle)
    # Sanity check: the angle between the original pole and new pole
    # should be less than or equal to the overall rotation angle
    assert (
        pole_rotation_angle <= N.degrees(N.abs(q.angle())) + 1e-6
    )  # Allow for floating point error

    # Sanity check 2: pole was rotated along a meridian
    assert N.allclose(90 - new_pole_sph[1], pole_rotation_angle)

    # Decompose the quaternion rotation into two rotations (swing-twist decomposition)
    # 1. Rotation around the geographic pole
    # 2. Rotation to move pole to a new location

    swing_axis = unit_vector(*N.cross(orig_pole, new_pole))
    swing_angle = N.arccos(N.dot(orig_pole, new_pole))

    swing_q = Q.from_rotation_vector(swing_angle * swing_axis)

    # Check that the rotation axis for the "swing" is indeed on the equator
    assert N.allclose(swing_q.z, 0)
    # Check that the swing angle is equivalent to the latitude (from north) of the new pole
    assert N.allclose(N.degrees(swing_angle), 90 - cart2sph(new_pole)[1])

    # Get rotation component around new pole (the "twist")
    twist_q = q * swing_q.inverse()

    # Check that two rotations can be composed back to the original
    assert N.allclose(q, swing_q * twist_q)

    # Step 2: Rotate around the new pole to a final angular position

    # Apply the twist rotation
    twisted = Q.rotate_vectors(twist_q, unit_vector(1, 0, 0))
    twist_angle = N.degrees(N.arctan2(twisted[1], twisted[0]))

    print("New pole:", new_pole_sph)

    # For some reason, changing the longitude of the north pole causes the entire manifold to be shifted
    # by that amount. I think this is a PROJ quirk? So we need to subtract this to rotate everything back into alignment.
    lon_0 = new_pole_sph[0] - twist_angle
    print("Twist angle:", twist_angle)
    print("Lon_0:", lon_0)

    return rotate_with_ob_tran(
        point,
        N.radians(new_pole_sph[0]),
        N.radians(new_pole_sph[1]),
        N.radians(lon_0),
    )


def rotate_postgis_simplified(point, q):
    # Step 1: Take the pole and rotate it along a meridian
    # to a new location (pole is at some point on the equator)

    # Find new pole location
    # new_pole = q * N.quaternion(0, 0, 0, 1) * q.inverse()
    q1 = N.quaternion(
        -q.z,
        q.y,
        -q.x,
        q.w,
    )
    new_pole = q1 * q.inverse()

    lon_p = N.arctan2(new_pole.y, new_pole.x)
    lat_p = N.arcsin(new_pole.z)

    # Pole rotation angle
    lon_s = lon_p + N.pi / 2

    half_angle = N.arccos(new_pole.z) / 2

    swing_q_inv = N.quaternion(
        -N.cos(half_angle),
        N.cos(lon_s) * N.sin(half_angle),
        N.sin(lon_s) * N.sin(half_angle),
        0,
    )

    # Get rotation component around new pole (the "twist")
    twist_q = q * swing_q_inv

    # Step 2: Rotate around the new pole to a final angular position

    twisted = twist_q * N.quaternion(0, 1, 0, 0) * twist_q.inverse()
    twist_angle = N.arctan2(twisted.y, twisted.x)

    # For some reason, changing the longitude of the north pole causes the entire manifold to be shifted
    # by that amount. I think this is a PROJ quirk? So we need to subtract this to rotate everything back into alignment.
    lon_0 = lon_p - twist_angle

    return rotate_with_ob_tran(point, lon_p, lat_p, lon_0)


def rotate_python(point, quaternion):
    pt = sph2cart(*point)
    v1 = Q.rotate_vectors(quaternion, pt)
    return cart2sph(unit_vector(*v1))


def corelle_rotate_geometry(point, quaternion):
    return rotate_point(point, quaternion, func="corelle.rotate_geometry")


def corelle_rotate_geometry_pointwise(point, quaternion):
    return rotate_point(point, quaternion, func="corelle.rotate_geometry_pointwise")


postgis_rotation_functions = [
    "corelle.rotate_geometry",
    "corelle.rotate_geometry_pointwise",
]

rotation_functions = [
    corelle_rotate_geometry,
    corelle_rotate_geometry_pointwise,
    rotate_postgis_ob_tran,
    rotate_postgis_simplified,
    rotate_python,
]


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
