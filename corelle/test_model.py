import pytest
import json
from pg_viewtils import relative_path
from os import path
import numpy as N
from .rotate.engine import (
    get_rotation,
    get_all_rotations,
    get_rotation_series,
    RotationError,
)
from .rotate.math import euler_equal, quaternion_to_euler, euler_to_quaternion


def test_seton_recursion():
    """
    There is a self-referential loop in the Seton2012 plate model
    that we need to make sure our code can handle without infinite
    recursion (which affected our first, naive implementation).
    """
    q = get_rotation("Seton2012", 502, 130)
    assert q is not None


times = [0, 2, 4, 10, 30, 60, 120, 130, 240, 480, 550, 620]


@pytest.mark.parametrize("time", times)
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


times = [2, 5, 9.8, 10]


@pytest.mark.parametrize("time", times)
def test_plate_disappearance(time):
    """
    Plates should not have a valid rotation after their `old_lim`...
    Amendment: actually this is perfectly fine, because different plate polygons
    can appear and disappear at different times. What plates shouldn't have are
    defined rotations outside the time range for which rotations are explicitly defined.
    """
    rotations = get_all_rotations("Seton2012", time, active_only=False)
    plate_ids = [p for p, q in rotations]
    if time <= 9.8:
        assert 922 in plate_ids
    else:
        assert not (922 in plate_ids)


# Test identity
def test_identity():
    time = 10
    plate_id = 1
    q = get_rotation("Seton2012", plate_id, 10)
    q1 = N.quaternion(1, 0, 0, 0)
    assert N.allclose(q, q1)


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
    assert N.allclose(q1, q2)


def test_undefined_model():
    """
    Make sure there is an error when we specify a bad model.
    """
    did_throw = False
    try:
        r = get_rotation("Adsdfs", 10, 10)
    except RotationError as err:
        did_throw = True
    assert did_throw


def test_mongol_okhotsk():
    """
    The Mongol-Okhotsk basin in Seton2012 should not show up prior to 320 Ma
    (its earliest defined rotation time step)
    Amendment: it also should not show up prior to ~200 Ma when the last rotation
    for plate 701 in its reconstruction tree is defined.
    """
    q = get_rotation("Seton2012", 417, 200)
    assert q is not None

    q = get_rotation("Seton2012", 417, 318)
    assert q is None

    q = get_rotation("Seton2012", 417, 322)
    assert q is None


def test_rotation_series():
    """Getting a series of rotation vectors should be as simple as possible"""
    times = N.arange(350, 340, -1)
    res = list(get_rotation_series("Seton2012", *times, verbose=True))
    for time, rot in zip(times, res):
        assert rot["time"] == time
        assert len(rot["rotations"]) == len(
            list(get_all_rotations("Seton2012", float(time)))
        )


@pytest.mark.skip(reason="It's super slow!")
def test_rotation_series_speed():
    """Getting a series of rotation vectors should not take millenia"""
    times = N.arange(350, 0, -1)
    res = list(get_rotation_series("Seton2012", *times))
    assert res[0]["time"] == 350
