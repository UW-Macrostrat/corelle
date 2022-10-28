from os import path, listdir, environ
from sqlalchemy.exc import ProgrammingError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from macrostrat.utils import relative_path
from macrostrat.database import Database

conn_string = environ.get("CORELLE_DB", "postgresql:///plate-rotations")
db = Database(conn_string)


def initialize(drop=False):
    # Run all SQL in the `sql` directory
    dn = relative_path(__file__, "sql")
    if drop:
        try:
            db.execute("DROP SCHEMA corelle CASCADE")
        except ProgrammingError:
            pass

    for file in sorted(listdir(dn)):
        if not file.endswith(".sql"):
            continue
        fn = path.join(dn, file)
        db.exec_sql(fn)
