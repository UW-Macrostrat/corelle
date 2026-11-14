from dataclasses import dataclass
from pytest import fixture
from corelle.engine.database import get_database
from .utils import get_coordinates, get_geojson


@fixture(scope="session")
def conn():
    with get_database().engine.connect() as conn:
        yield conn


@dataclass
class ModelRotationFixture:
    model: str
    time: int
    current: list[list[float]]
    rotated: list[list[float]]


times = [0, 1, 10, 120, 140, 200]


@fixture(params=times, scope="session")
def gplates_web_service_testcase(request) -> ModelRotationFixture:
    time = request.param
    return ModelRotationFixture(
        "Seton2012",
        time,
        get_coordinates(get_geojson("seton2012-gws-request")),
        get_coordinates(get_geojson(f"seton2012-gws-response-{time}")),
    )
