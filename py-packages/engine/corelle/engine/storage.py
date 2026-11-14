from sqlalchemy import MetaData, Table, text

_model_id = text("SELECT id FROM corelle.model WHERE name = :name")


def model_id(conn, name):
    return conn.execute(_model_id, dict(name=name)).scalar()


def reflect_table(conn, name):
    return Table(name, MetaData(), schema="corelle", autoload_with=conn)
