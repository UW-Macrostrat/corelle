from os import path, listdir
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pg_viewtils import run_sql_file, relative_path

db = create_engine("postgresql:///plate-rotations")
create_session = sessionmaker(bind=db)

__drop_tables = "DROP TABLE model, plate, rotation CASCADE"

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

