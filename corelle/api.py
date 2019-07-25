from flask import Flask
from flask_restful import Resource, Api
from pg_viewtils import relative_path
from sqlalchemy import text
from simplejson import loads, JSONEncoder

from .database import db

app = Flask(__name__)
app.config['RESTFUL_JSON'] = dict(cls=JSONEncoder)
api = Api(app)

conn = db.connect()

class Help(Resource):
    def get(self):
        return {'routes': []}

def get_plate_polygons():
    fn = relative_path(__file__, 'query', 'modern-plate-polygons.sql')
    sql = text(open(fn).read())
    results = conn.execute(sql)
    for row in results:
        props = dict(row)
        geom = loads(props.pop("geometry"))
        yield dict(
            id = props['plate_id'],
            type = 'Feature',
            properties = props,
            geometry = geom)

class ModernPlates(Resource):
    def get(self):
        return list(get_plate_polygons())

api.add_resource(Help, '/')
api.add_resource(ModernPlates, "/plates")
