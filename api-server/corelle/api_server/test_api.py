from pytest import fixture
import sys
from os import path
from numpy import allclose

# Get the right directory for corelle_helpers
pth = path.abspath(path.join(path.dirname(__file__), "..", "notebooks"))
sys.path.append(pth)

from corelle_helpers import rotate_features
from .api import app


@fixture
def client():
    with app.test_client() as client:
        yield client


def test_basic_api_access(client):
    rotations = client.get("/api/rotate?model=Wright2013&time=120&quaternion=true").json
    # API call returns GeoJSON format plates
    features = client.get("/api/plates?model=Wright2013").json
    # Rotate our coastline featrues
    rotated_features = list(rotate_features(rotations, features))
    assert len(rotated_features) > 10

def test_reconstruct_api(client):
    args = dict(
        lng=-89.37088151960317,
        lat=43.084235832279795,
        age=500,
        model="Scotese",
        referrer="rockd"
    )
    vals = "&".join([f"{k}={v}" for k,v in args.items()])
    res = client.get("/api/reconstruct?"+vals).json

    assert res["type"] == "FeatureCollection"
    assert len(res["features"]) == 1 
    coords = res["features"][0]["geometry"]["coordinates"]
    assert allclose(coords, [-84.17949814030625, -21.341188167880905])