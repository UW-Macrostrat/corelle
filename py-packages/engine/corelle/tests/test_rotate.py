import numpy as N
import quaternion as Q
import pytest
from corelle.math.util import vector, unit_vector
from corelle.math import (
    sph2cart,
    cart2sph,
    euler_to_quaternion,
    quaternion_to_euler,
    euler_equal,
)

from corelle.engine.rotate import rotate_point

equal = N.allclose


def is_pure_quaternion(q):
    """
    A _pure quaternion_ is has a _real component_ (i.e.
    the first component) of zero. This is a fancy way
    of saying that it is _just a vector_.
    """
    return q.w == 0


def test_quaternion_identity():
    v1 = vector(0, 0, 1)
    identity = N.quaternion(1, 0, 0, 0)
    # Numerical construction of quaternion
    q = N.quaternion(0, *v1)

    assert identity.angle() == 0

    assert equal(q.vec, v1)
    assert is_pure_quaternion(q)
    v2 = q * identity
    assert equal(v1, v2.vec)


def test_vector_recovery():
    assert equal(vector(1, 0, 0), sph2cart(0, 0))


def test_cartesian_recovery():
    v = unit_vector(1.2, 4, 2.5)
    assert equal(v, sph2cart(*cart2sph(v)))


def test_quaternion_composition():
    """Compose two rotations"""
    vert = unit_vector(0, 0, 1)
    q1 = Q.from_rotation_vector(vert * N.radians(90))
    q2 = Q.from_rotation_vector(vert * N.radians(-30))
    qc = q1 * q2
    assert N.allclose(N.degrees(qc.angle()), 60)


r = [(80, 25, 32), (-10, 22, -20), (120, -80, 5.2)]


@pytest.mark.parametrize("angles", r)
def test_euler_recovery(angles):
    a2 = quaternion_to_euler(euler_to_quaternion(angles))
    assert euler_equal(angles, a2)


@pytest.mark.parametrize("angles", r)
def test_quaternion_angle_recovery(angles):
    axis = sph2cart(angles[0], angles[1])
    angle = N.radians(angles[2])
    q1 = Q.from_rotation_vector(axis * angle)

    assert equal(N.abs(q1.angle()), N.abs(angle))
    assert equal(q1.w, N.cos(q1.angle() / 2))
    assert equal(q1.vec, axis * N.sin(angle / 2))
    assert euler_equal(quaternion_to_euler(q1), angles)


@pytest.mark.parametrize("angles", r)
def test_quaternion_equivalence(angles):
    q = euler_to_quaternion(angles)
    # Make sure sign is the same
    angle = N.degrees(2 * N.arccos(q.w))
    assert equal(N.abs(angle), N.abs(angles[-1]), atol=0.001)


def test_rotate_now():
    point = [90, -50]
    new_point = rotate_point(point, "Seton2012", 0)
    assert N.allclose(point, new_point)
