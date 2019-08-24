from os import path, listdir, environ
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from pg_viewtils import run_sql_file, relative_path

conn_string = environ.get("CORELLE_DB", "postgresql:///plate-rotations")
db = create_engine(conn_string)
create_session = sessionmaker(bind=db)

__drop_tables = """
DROP TABLE IF EXISTS
model, plate, plate_polygon, rotation
CASCADE
"""

def initialize(drop=False):
    # Run all SQL in the `sql` directory
    dn = relative_path(__file__,'sql')
    if drop:
        db.execute(__drop_tables)

    session = create_session()

    for file in sorted(listdir(dn)):
        if not file.endswith(".sql"): continue
        fn = path.join(dn, file)
        run_sql_file(session, fn)
