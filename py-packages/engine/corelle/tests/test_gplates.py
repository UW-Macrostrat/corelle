import pytest
import numpy as N

from corelle.math import quaternion_to_euler, euler_equal
from corelle.engine.rotate import get_rotation, rotate_point

from .utils import get_geojson, get_coordinates, fixture_file


def test_against_web_service(gplates_web_service_testcase):
    case = gplates_web_service_testcase
    for c0, ct in zip(case.current, case.rotated):
        p1 = rotate_point(c0, case.model, case.time)
        assert N.allclose(p1, ct, atol=0.01)


def test_against_gplates_web_service_africa():
    time = 140
    req = get_geojson("seton2012-gws-request-africa")
    res = get_geojson(f"seton2012-gws-response-africa-{time}")

    now = get_coordinates(req)
    prev = get_coordinates(res)
    assert len(now) == len(prev)

    for c0, ct in zip(now, prev):
        p1 = rotate_point(c0, "Seton2012", time)
        assert N.allclose(p1, ct, atol=0.01)


def check_seton2012_rotation(time, *row):
    plate_id = int(row[0])
    if plate_id != 802:
        return
    try:
        lat = float(row[1])
        lon = float(row[2])
        angle = float(row[3])
    except ValueError as err:
        # Indeterminate rotation, i.e. no rotation at all
        return
    rot = get_rotation("Seton2012", plate_id, time)
    v = quaternion_to_euler(rot)
    assert euler_equal(v, (lon, lat, angle))


times = [10, 100]
### Test against all GPlates rotations ###
@pytest.mark.parametrize("time", times)
def test_all_gplates(time):
    """
    Test against all GPlates rotations at a given time step
    """
    with fixture_file(f"Seton2012-rotations-{time}Ma.csv") as f:
        for row in f:
            v = row.split(",")
            check_seton2012_rotation(time, *v)
