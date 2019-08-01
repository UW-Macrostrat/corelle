import pytest
from .rotate import get_all_rotations, quaternion_to_euler

times = [0,2,4,10,30,60,120,240,480, 550, 620]

@pytest.mark.parametrize('time', times)
def test_seton_rotations(time):
    for (plate_id, q) in get_all_rotations("Seton2012", 2):
        if plate_id == 225:
            print(quaternion_to_euler(q))
        assert q is not None
