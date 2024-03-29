from os import environ
from sqlalchemy.exc import ProgrammingError
from macrostrat.utils import relative_path
from macrostrat.database import Database, run_sql
from pathlib import Path

conn_string = environ.get("CORELLE_DB", "postgresql:///plate-rotations")
db = Database(conn_string)


def initialize(drop=False):
    # Run all SQL in the `sql` directory
    dn = Path(relative_path(__file__, "schema"))
    if drop:
        try:
            db.engine.execute("DROP SCHEMA corelle CASCADE")
        except ProgrammingError:
            pass

    files = sorted(dn.glob("*.sql"))

    for file in files:
        db.run_sql(Path(dn) / file, has_server_binds=False)
