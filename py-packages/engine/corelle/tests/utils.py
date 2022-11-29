import json

from macrostrat.utils import relative_path


# Test against gplates web service data
def fixture(filename):
    fn = relative_path(__file__, "fixtures", filename)
    return open(fn, "r")


def get_geojson(key):
    with fixture(key + ".geojson") as f:
        return json.load(f)


def get_coordinates(fc):
    """
    Get the coordinates from a feature collection
    """
    return fc["features"][0]["geometry"]["coordinates"][0]
