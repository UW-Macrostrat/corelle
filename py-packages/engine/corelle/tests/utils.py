import json
from dataclasses import dataclass
from macrostrat.utils import relative_path
from pytest import fixture

# Test against gplates web service data
def fixture_file(filename):
    fn = relative_path(__file__, "fixtures", filename)
    return open(fn, "r")


def get_geojson(key):
    with fixture_file(key + ".geojson") as f:
        return json.load(f)


def get_coordinates(fc):
    """
    Get the coordinates from a feature collection
    """
    return fc["features"][0]["geometry"]["coordinates"][0]
