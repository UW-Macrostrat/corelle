import pytest
from .rotate import get_rotation, get_all_rotations, quaternion_to_euler

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
