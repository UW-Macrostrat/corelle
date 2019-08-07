import pytest
import json
from pg_viewtils import relative_path
from os import path
import numpy as N
from .rotate import get_rotation, get_all_rotations, quaternion_to_euler

# Test against gplates web service data
def get_fixture(key):
    fn = relative_path(__file__, '..', 'test-data', key+'.geojson')
    with open(fn,'r') as f:
        return json.load(f)

def get_coordinates(fc):
    """
    Get the coordinates from a feature collection
    """
    return fc['features'][0]['geometry']['coordinates'][0][0]

req = get_fixture("seton2012-gws-request")
times = [140,200]
@pytest.mark.parametrize("time", times)
def test_against_gplates(time):
    res = get_fixture("seton2012-gws-response-140")

    now = get_coordinates(req)
    prev = get_coordinates(res)
    assert len(now) == len(prev)

    for c0,ct in zip(now, prev):
        pass

    assert True
