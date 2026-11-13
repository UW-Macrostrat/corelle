from pytest import fixture, raises
from numpy import allclose
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from corelle.client import rotate_features
from corelle.engine.storage import conn
from . import app


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
        referrer="rockd",
    )
    vals = "&".join([f"{k}={v}" for k, v in args.items()])
    res = client.get("/api/reconstruct?" + vals).json

    assert res["type"] == "FeatureCollection"
    assert len(res["features"]) == 1
    coords = res["features"][0]["geometry"]["coordinates"]
    assert allclose(coords, [-84.17949814030625, -21.341188167880905])


def test_model_route(client):
    res = client.get("/api/model").json
    assert len(res) > 1
    assert all("id" in m for m in res)
    assert all("name" in m for m in res)
    assert all("min_age" in m for m in res)
    assert all("max_age" in m for m in res)


def test_failed_statement_does_not_poison_later_requests(client):
    """A shared connection left in a failed transaction once broke every route."""
    with raises(DBAPIError):
        conn.execute(text("SELECT 1/0"))
    assert client.get("/api/model").status_code == 200
    res = client.get("/api/point?model=Scotese&time=100&data=-89.4,43.07")
    assert res.status_code == 200


def test_point_route_includes_plate_id(client):
    """PBDB's paleocoordinate updater stores the plate ID from this route."""
    res = client.get(
        "/api/point?model=Scotese&time=100&include_failures=1&data=-89.4,43.07+0,-89"
    ).json
    assert [f["properties"]["plate_id"] for f in res] == [101, 802]
    assert allclose(res[0]["geometry"]["coordinates"], [-50.277, 38.316], atol=0.01)
