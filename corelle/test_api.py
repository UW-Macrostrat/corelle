from pytest import fixture
import sys
from os import path

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
