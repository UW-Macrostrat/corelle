from flask import Flask
from flask_restful import Resource, Api
from flask_restful.reqparse import RequestParser
from pg_viewtils import relative_path
from sqlalchemy import text
from simplejson import loads, JSONEncoder

from .database import db
from .rotate import get_rotation, get_all_rotations, get_plate_rotations, plates_for_model

app = Flask(__name__)
app.config['RESTFUL_JSON'] = dict(cls=JSONEncoder)
api = Api(app)

conn = db.connect()

class Help(Resource):
    def get(self):
        return {'routes': []}

def get_plate_polygons(model):
    fn = relative_path(__file__, 'query', 'modern-plate-polygons.sql')
    sql = text(open(fn).read())
    results = conn.execute(sql, model_name=model)
    for row in results:
        props = dict(row)
        geom = loads(props.pop("geometry"))
        yield dict(
            id = props['plate_id'],
            type = 'Feature',
            properties = props,
            geometry = geom)

class ModernPlates(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser = RequestParser()
        self.parser.add_argument('model', type=str, required=True)

    def get(self):
        args = self.parser.parse_args()
        return list(get_plate_polygons(args['model']))

def base_parser():
    r = RequestParser()
    r.add_argument('plate_id', type=int)
    r.add_argument('model', type=str, required=True)
    r.add_argument('quaternion', type=bool, default=False)
    return r

class RotationsResource(Resource):
    def __init__(self):
        super().__init__()
        self.parser = base_parser()

    def reducer(self, q, args):
        if args['quaternion']:
            return dict(quaternion=[q.w, q.x, q.y, q.z])
        return dict(
            axis=list(q.vec),
            angle=q.angle())

class Rotation(RotationsResource):
    def __init__(self):
        super().__init__()
        self.parser.add_argument('time', required=True)

    def reducer(self, q, args, plate_id):
        res = super().reducer(q, args)
        res['plate_id'] = plate_id
        return res

    def get(self):
        args =self.parser.parse_args()

        if args['plate_id']:
            return self.get_single(args)

        return list(self.get_all(args))

    def get_all(self, args):
        for (plate_id, q) in get_all_rotations(args['model'], args['time']):
            yield self.reducer(q, args, plate_id)

    def get_single(self, args):
        plate_id = args['plate_id']
        q = get_rotation(args['model_id'], plate_id, args['time'])
        return self.reducer(q, args, plate_id)

class Pole(Resource):
    def __init__(self):
        super().__init__()
        self.parser = base_parser()
    def get(self):
        args = self.parser.parse_args()
        if 'plate_id' in args:
            id = args['plate_id']
            return dict(
                plate_id=id,
                rotations=list(self.get_single(id, args)))
        return list(self.get_all(args))

    def get_single(self, id, args):
        for r in get_plate_rotations(args['model_id'], id):
            yield self.reducer(q, args, r.t_step)

    def get_all(self, id, args):
        plates = plates_for_model(args['model_id'])
        for id in plates:
            yield dict(
                plate_id = id,
                rotations = list(self.get_single(id, args)))

    def reducer(self, q, args, t_step):
        res = super().reducer(q, args)
        res['t_step'] = t_step

class Model(Resource):
    def get(self):
        results = conn.execute("SELECT id, name FROM model")
        return [dict(r) for r in results]

api.add_resource(Help, '/api')
api.add_resource(ModernPlates, "/api/plates")
api.add_resource(Rotation, "/api/rotate")
api.add_resource(Pole, "/api/pole")
api.add_resource(Model, "/api/model")
