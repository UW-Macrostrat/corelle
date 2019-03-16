import numpy as N
import quaternion
from .util import vector, unit_vector

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
