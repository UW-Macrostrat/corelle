"""
Tests of rotations using PostGIS functions (to support on-database transformations with cached rotations)
"""

from corelle.math.util import unit_vector
import numpy as N
import quaternion as Q
from corelle.engine.database import db
from geoalchemy2.shape import to_shape
from geoalchemy2.elements import WKBElement
from corelle.math import sph2cart, cart2sph

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


def swing_twist_decomposition_old(q):
    """An old and non-working version of the swing-twist decomposition, which
    has a lot of description of the overall structure of the algorithm."""
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

    assert N.allclose(N.degrees(swing_q.angle()), pole_rotation_angle)

    # print("Pole rotation angle:", pole_rotation_angle)
    # # Sanity check: the angle between the original pole and new pole
    # # should be less than or equal to the overall rotation angle
    # assert (
    #     pole_rotation_angle <= N.degrees(N.abs(q.angle())) + 1e-6
    # )  # Allow for floating point error

    # Sanity check 2: pole was rotated along a meridian
    assert N.allclose(90 - new_pole_sph[1], pole_rotation_angle)

    # Decompose the quaternion rotation into two rotations (swing-twist decomposition)
    # 1. Rotation around the geographic pole
    # 2. Rotation to move pole to a new location

    swing_axis = unit_vector(*swing_q.vec)
    swing_angle = swing_q.angle()

    swing_q = Q.from_rotation_vector(swing_angle * swing_axis)

    # Check that the rotation axis for the "swing" is indeed on the equator
    assert N.allclose(swing_q.z, 0)
    # Check that the swing angle is correct
    # assert N.allclose(swing_q.angle(), swing_angle)

    # Check that the swing angle is equivalent to the latitude (from north) of the new pole
    assert N.allclose(N.degrees(swing_angle), 90 - cart2sph(new_pole)[1])

    # Get rotation component around new pole (the "twist")
    twist_q = q * swing_q.inverse()

    # Check that the swing and twist rotations can be composed back to the original
    assert N.allclose(q, twist_q * swing_q)

    return swing_q, twist_q


def swing_twist_decomposition(q):
    orig_pole = sph2cart(0, 90)
    return decompose_quaternion(q, orig_pole)


def new_pole_location(q):
    orig_pole = sph2cart(0, 90)
    return Q.rotate_vectors(q, orig_pole)


def rotate_postgis_ob_tran(point, q):
    orig_pole = sph2cart(0, 90)
    twist_q, swing_q = decompose_quaternion(q, orig_pole)

    new_pole_sph = cart2sph(new_pole_location(q))
    # Step 2: Rotate around the new pole to a final angular position
    # Apply the twist rotation
    twisted = Q.rotate_vectors(twist_q, unit_vector(1, 0, 0))
    twist_angle = N.degrees(twist_q.angle())

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

    twist = N.array([q.w, 0, 0, q.z]) * N.sign(q.z)

    norm = N.linalg.norm(twist)

    if norm == 0:
        twist = identity_quaternion
    else:
        twist /= norm

    # Step 2: Rotate around the new pole to a final angular position

    # Get angle of twist quaternion
    twist_angle = 2 * N.arccos(twist[0])

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
