import pytest
import json
from pg_viewtils import relative_path
from os import path
import numpy as N
from .rotate import get_rotation, get_all_rotations, rotate_point
from .rotate.math import quaternion_to_euler

# Test against gplates web service data
def get_fixture(key):
    fn = relative_path(__file__, '..', 'test-data', key+'.geojson')
    with open(fn,'r') as f:
        return json.load(f)

def get_coordinates(fc):
    """
    Get the coordinates from a feature collection
    """
    return fc['features'][0]['geometry']['coordinates'][0]

times = [0,1,10,120,140,200]
@pytest.mark.parametrize("time", times)
def test_against_gplates(time):
    req = get_fixture("seton2012-gws-request")
    res = get_fixture(f"seton2012-gws-response-{time}")

    now = get_coordinates(req)
    prev = get_coordinates(res)
    assert len(now) == len(prev)

    for c0,ct in zip(now, prev):
        p1 = rotate_point(c0, "Seton2012", time)
        assert N.allclose(p1,ct, atol=0.01)

def test_africa_against_gplates():
    time = 140
    req = get_fixture("seton2012-gws-request-africa")
    res = get_fixture(f"seton2012-gws-response-africa-{time}")

    now = get_coordinates(req)
    prev = get_coordinates(res)
    assert len(now) == len(prev)

    for c0,ct in zip(now, prev):
        p1 = rotate_point(c0, "Seton2012", time)
        assert N.allclose(p1,ct, atol=0.01)
