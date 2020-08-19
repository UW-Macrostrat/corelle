from flask import Flask
from flask_restful import Resource, Api
from flask_restful.reqparse import RequestParser
from sqlalchemy import text
from simplejson import loads, JSONEncoder

from .database import db
from .query import get_sql
from .rotate import get_rotation, get_all_rotations, get_plate_rotations, rotate_point

app = Flask(__name__)
app.config["RESTFUL_JSON"] = dict(cls=JSONEncoder)
api = Api(app)

conn = db.connect()


class Help(Resource):
    def get(self):
        return {"routes": []}


def get_plate_polygons(model):
    """
    Uncached version of modern plate polygons query
    """
    q = get_sql("modern-plate-polygons")
    results = conn.execute(q, model_name=model)
    for row in results:
        props = dict(row)
        geom = loads(props.pop("geometry"))
        yield dict(
            id=props["plate_id"], type="Feature", properties=props, geometry=geom
        )


def get_plate_polygons_cached(model):
    q = get_sql("modern-plate-polygons-cached")
    return conn.execute(q, model_name=model).scalar()


class ModelResource(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser = RequestParser()
        self.parser.add_argument("model", type=str, required=True)


class AllFeatures(Resource):
    def get(self):
        q = text("SELECT DISTINCT dataset_id FROM cache.feature")
        return [r[0] for r in conn.execute(q)]


class Features(ModelResource):
    def get(self, dataset):
        args = self.parser.parse_args()
        q = get_sql("feature-dataset-cached")
        return conn.execute(q, model_name=args["model"], dataset=dataset).scalar()


class ModernPlates(ModelResource):
    def get(self):
        args = self.parser.parse_args()
        return get_plate_polygons_cached(args["model"])


def base_parser():
    r = RequestParser()
    r.add_argument("plate_id", type=int)
    r.add_argument("model", type=str, required=True)
    r.add_argument("quaternion", type=bool, default=False)
    return r


class RotationsResource(Resource):
    def __init__(self):
        super().__init__()
        self.parser = base_parser()

    def reducer(self, q, args):
        if args["quaternion"]:
            return dict(quaternion=[q.w, q.x, q.y, q.z])
        return dict(axis=list(q.vec), angle=q.angle())


class Rotation(RotationsResource):
    def __init__(self):
        super().__init__()
        self.parser.add_argument("time", required=True)

    def reducer(self, q, args, plate_id):
        res = super().reducer(q, args)
        res["plate_id"] = plate_id
        return res

    def get(self):
        args = self.parser.parse_args()

        if args["plate_id"]:
            return self.get_single(args)

        return list(self.get_all(args))

    def get_all(self, args):
        for (plate_id, q) in get_all_rotations(args["model"], args["time"]):
            yield self.reducer(q, args, plate_id)

    def get_single(self, args):
        plate_id = args["plate_id"]
        q = get_rotation(args["model"], plate_id, args["time"])
        return self.reducer(q, args, plate_id)


class Pole(ModelResource):
    """
    Get poles for plate(s)
    """

    def __init__(self):
        super().__init__()
        self.parser.add_argument("plate_id", type=int, required=True)

    def get(self):
        args = self.parser.parse_args()
        id = args["plate_id"]
        return list(self.get_single(id, args))

    def get_single(self, id, args):
        for q, t_step in get_plate_rotations(args["model"], id):
            yield self.reducer(q, args, t_step)

    def reducer(self, q, args, t_step):
        res = super().reducer(q, args)
        res["t_step"] = t_step
        return res


class Model(Resource):
    def get(self):
        results = conn.execute("SELECT id, name, min_age, max_age FROM model")
        return [dict(r) for r in results]


class Point(ModelResource):
    def __init__(self):
        super().__init__()
        self.parser.add_argument("data", type=str, required=True)
        self.parser.add_argument("time", required=True)
        self.parser.add_argument("include_failures", type=bool, default=False)

    def get(self):
        args = self.parser.parse_args()
        points = args.data.split()
        out_points = []
        for p in points:
            [lon, lat] = p.split(",")
            pt = [float(lon), float(lat)]
            res = rotate_point(pt, args["model"], args["time"])
            if res is not None:
                res = dict(type="Feature", geometry=dict(type="Point", coordinates=res))
                out_points.append(res)
            else:
                if args["include_failures"]:
                    out_points.append(None)
        return out_points


api.add_resource(Help, "/api")
api.add_resource(ModernPlates, "/api/plates")
api.add_resource(Rotation, "/api/rotate")
api.add_resource(AllFeatures, "/api/feature")
api.add_resource(Features, "/api/feature/<string:dataset>")
api.add_resource(Pole, "/api/pole")
api.add_resource(Point, "/api/point")
api.add_resource(Model, "/api/model")
