"""
This mini-module is essentially the equivalent of the Javascript `@macrostrat/corelle`
library, for rotating plates provided by a Corelle rotations server.
"""
import sys
import os
import numpy as N
import quaternion as Q
from shapely.ops import transform
from shapely.geometry import shape
from collections.abc import Iterable
from pandas import DataFrame, isna

# Add corelle to our path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from corelle.rotate.math import cart2sph, sph2cart


def rotate_point(q, point):
    if isinstance(point[0], Iterable):
        raise TypeError("Function is not vectorized")
        return point
    v0 = sph2cart(*point)
    q = N.quaternion(*q)
    v1 = Q.rotate_vectors(q, v0)
    return cart2sph(v1)


def rotate_geometry(q, geometry):
    """Rotate a geometry by a quaternion"""
    return transform(lambda x, y: rotate_point(q, (x, y)), geometry)


def rotate_features(
    rotations, features, plate_id=lambda f: f["properties"]["plate_id"]
):
    """Rotate features by a set of instantaneous rotations"""
    rot_index = {v["plate_id"]: v["quaternion"] for v in rotations}

    for f in features:
        q = rot_index.get(plate_id(f))
        if q is None:
            continue
        yield rotate_geometry(q, shape(f["geometry"]))


def rotate_dataframe(df, rotations, time=None):
    """Rotate a GeoPandas GeoDataFrame. This function expects a
    quaternion and geometry column."""

    def rotate_row(row):
        # This bit actually does the rotation
        return rotate_geometry(row.quaternion, row.geometry)

    rot = DataFrame.from_dict(rotations)
    if time is not None:
        rot["time"] = time
    res = df.merge(rot, on="plate_id")
    res["geometry"] = res.apply(rotate_row, axis=1)
    res.drop(columns=["quaternion"], inplace=True)
    return res
