import pytest
import json
from pg_viewtils import relative_path
from os import path
import numpy as N
from .rotate import get_rotation, get_all_rotations, rotate_point
from .rotate.math import quaternion_to_euler, euler_equal

# Test against gplates web service data
def fixture(filename):
    fn = relative_path(__file__, "..", "test-data", filename)
    return open(fn, "r")


def get_geojson(key):
    with fixture(key + ".geojson") as f:
        return json.load(f)


def get_coordinates(fc):
    """
    Get the coordinates from a feature collection
    """
    return fc["features"][0]["geometry"]["coordinates"][0]


times = [0, 1, 10, 120, 140, 200]


@pytest.mark.parametrize("time", times)
def test_against_gplates_web_service(time):
    req = get_geojson("seton2012-gws-request")
    res = get_geojson(f"seton2012-gws-response-{time}")

    now = get_coordinates(req)
    prev = get_coordinates(res)
    assert len(now) == len(prev)

    for c0, ct in zip(now, prev):
        p1 = rotate_point(c0, "Seton2012", time)
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
    assert euler_equal(v, (lat, lon, angle))


times = [10, 100]
### Test against all GPlates rotations ###
@pytest.mark.parametrize("time", times)
def test_all_gplates(time):
    """
    Test against all GPlates rotations at a given time step
    """
    with fixture(f"Seton2012-rotations-{time}Ma.csv") as f:
        for row in f:
            v = row.split(",")
            check_seton2012_rotation(time, *v)
