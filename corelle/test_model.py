import pytest
import json
from pg_viewtils import relative_path
from os import path
import numpy as N
from .rotate import get_rotation, get_all_rotations
from .rotate.math import euler_equal, quaternion_to_euler, euler_to_quaternion

def test_seton_recursion():
    """
    There is a self-referential loop in the Seton2012 plate model
    that we need to make sure our code can handle without infinite
    recursion (which affected the naive implementation).
    """
    q = get_rotation("Seton2012", 502, 130)
    assert q is not None

times = [0,2,4,10,30,60,120, 130, 240,480, 550, 620]

@pytest.mark.parametrize('time', times)
def test_seton_rotations(time):
    for (plate_id, q) in get_all_rotations("Seton2012", time):
        if plate_id == 225:
            print(quaternion_to_euler(q))
        assert q is not None

# In the Seton, 2012 plate model, the parts of the South American plate
# should remain together until at least the Cretaceous
def test_south_america_cretaceous():
    parts = [201, 202, 291, 280]
    rotations = [get_rotation("Seton2012", r, 67) for r in parts]
    for r in rotations[1:]:
        assert N.allclose(r, rotations[0])

def test_south_america_jurassic():
    rotate = lambda x: get_rotation("Seton2012", x, 152)
    assert not N.allclose(rotate(291), rotate(201))
    assert N.allclose(rotate(291), rotate(280))

times = [2,5,10]
@pytest.mark.xfail()
@pytest.mark.parametrize('time', times)
def test_plate_disappearance(time):
    """
    Plates should not have a valid rotation after their `old_lim`...
    """
    for t in times:
        rotations = get_all_rotations("Seton2012", t)
        plate_ids = [p for p,q in rotations]
        if t <= 5:
            assert 322 in plate_ids
        else:
            assert not (322 in plate_ids)

# Test identity
def test_identity():
    time = 10
    plate_id = 1
    q = get_rotation("Seton2012", plate_id, 10)
    q1 = N.quaternion(1,0,0,0)
    assert N.allclose(q,q1)

# Make sure simple rotation is right
def test_simple_rotation():
    time = 10
    plate_id = 701
    euler = (46.19, -87.86, -1.92)
    q = get_rotation("Seton2012", plate_id, time)
    q1 = euler_to_quaternion(euler)
    euler1 = quaternion_to_euler(q)
    assert euler_equal(euler, euler1)
    assert N.allclose(q, q1)

    q2 = get_rotation("Seton2012", 702, 10)
    assert N.allclose(q1,q2)
