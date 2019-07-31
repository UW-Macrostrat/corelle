import numpy as N
import quaternion
from .util import vector, unit_vector
from .rotate import sph2cart, cart2sph, euler_to_quaternion, quaternion_to_euler

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

r = (25, 80, 32)

def test_euler_recovery():
    assert equal(r, quaternion_to_euler(euler_to_quaternion(r)))

def test_quaternion_angle_recovery():
    axis = sph2cart(r[1],r[0])
    angle = N.radians(r[2])
    q1 = quaternion.from_rotation_vector(axis*angle)

    assert equal(q1.angle(), angle)
    assert q1.w == N.cos(q1.angle()/2)
    assert equal(q1.vec, axis*N.sin(angle/2))

def test_quaternion_equivalence():
    q = euler_to_quaternion(r)
    angle = 2*N.arccos(q.w)
    assert equal(N.degrees(angle), r[-1])
