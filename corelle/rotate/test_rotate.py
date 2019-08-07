import numpy as N
import quaternion as Q
import pytest
from .util import vector, unit_vector
from .math import sph2cart, cart2sph, euler_to_quaternion, quaternion_to_euler
from . import rotate_point

equal = N.allclose

def is_pure_quaternion(q):
    """
    A _pure quaternion_ is has a _real component_ (i.e.
    the first component) of zero. This is a fancy way
    of saying that it is _just a vector_.
    """
    return q.w == 0

def test_quaternion_identity():
    v1 = vector(0,0,1)
    identity = N.quaternion(1,0,0,0)
    # Numerical construction of quaternion
    q = N.quaternion(0,*v1)

    assert identity.angle() == 0

    assert equal(q.vec, v1)
    assert is_pure_quaternion(q)
    v2 = q*identity
    assert equal(v1,v2.vec)

def test_vector_recovery():
    assert equal(
        vector(1,0,0),
        sph2cart(0,0))

def test_cartesian_recovery():
    v = unit_vector(1.2,4,2.5)
    assert equal(v, sph2cart(*cart2sph(v)))

r = [(25, 80, 32), (22,-10,-20), (-80, 120, 5.2)]
@pytest.mark.parametrize("angles", r)
def test_euler_recovery(angles):
    a2 = list(quaternion_to_euler(euler_to_quaternion(angles)))
    if N.sign(angles[0]) != N.sign(a2[0]):
        a2[0] *= -1
        a2[1] += 180
        if a2[1] > 180:
            a2[1] -= 360
        a2[2] *= -1

    assert Q.allclose(angles, tuple(a2), atol=0.001)

def test_quaternion_angle_recovery():
    axis = sph2cart(r[1],r[0])
    angle = N.radians(r[2])
    q1 = quaternion.from_rotation_vector(axis*angle)

    assert equal(q1.angle(), angle)
    assert q1.w == N.cos(q1.angle()/2)
    assert equal(q1.vec, axis*N.sin(angle/2))
    assert N.allclose(quaternion_to_euler(q1), r)

def test_quaternion_equivalence():
    q = euler_to_quaternion(r)
    angle = 2*N.arccos(q.w)
    assert equal(N.degrees(angle), r[-1])

def test_rotate_now():
    point = [90, -50]
    new_point = rotate_point(point, "Seton2012", 0)
    assert N.allclose(point, new_point)
