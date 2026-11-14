from functools import cache
from os import environ
from pathlib import Path

from macrostrat.database import Database
from macrostrat.utils import relative_path
from sqlalchemy.exc import ProgrammingError


def database_url():
    return environ.get("CORELLE_DB", "postgresql:///plate-rotations")


def get_database(url=None) -> Database:
    """The database for the CLI and the server; engine functions take a connection."""
    return _database(url or database_url())


@cache
def _database(url):
    # Pre-ping replaces pooled connections the server has dropped.
    return Database(url, pool_pre_ping=True)


def initialize(db=None, drop=False):
    db = db or get_database()
    dn = Path(relative_path(__file__, "schema"))
    if drop:
        try:
            db.run_sql("DROP SCHEMA corelle CASCADE")
        except ProgrammingError:
            pass

    for file in sorted(dn.glob("*.sql")):
        db.run_sql(file, has_server_binds=False)
