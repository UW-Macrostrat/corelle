from flask import Flask
from flask_restful import Resource, Api
from flask_restful.reqparse import RequestParser
from pg_viewtils import relative_path
from sqlalchemy import text
from simplejson import loads, JSONEncoder

from .database import db
from .rotate import get_rotation, get_all_rotations

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

r = RequestParser()
r.add_argument('plate_id', type=int)
r.add_argument('time', required=True)
r.add_argument('quaternion', type=bool, default=False)

class Rotation(Resource):
    def get(self):
        args = r.parse_args()
        if args['plate_id']:
            return self.get_single(args)

        return list(self.get_all(args))

    def get_all(self, args):
        for (plate_id, q) in get_all_rotations(args['time']):
            yield self.reducer(q, plate_id, args)

    def get_single(self, args):
        plate_id = args['plate_id']
        q = get_rotation(plate_id, args['time'])
        return self.reducer(q, plate_id, args)

    def reducer(self, q, plate_id, args):
        if args['quaternion']:
            res = dict(quaternion=[q.w, q.x, q.y, q.z])
        else:
            res = dict(
                axis=list(q.vec),
                angle=q.angle())
        res['plate_id'] = plate_id
        return res


api.add_resource(Help, '/api')
api.add_resource(ModernPlates, "/api/plates")
api.add_resource(Rotation, "/api/rotate")
