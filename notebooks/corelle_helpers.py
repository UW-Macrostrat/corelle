"""
This tiny library is essentially the equivalent of the Javascript `@macrostrat/corelle`
library, for rotating plates provided by the Corelle API.
"""
import sys
import os
import numpy as N
import quaternion as Q
from shapely.ops import transform
from shapely.geometry import shape
from collections.abc import Iterable

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


def rotator(q):
    return lambda x, y: rotate_point(q, (x, y))


def rotate_geometry(q, geometry):
    """Rotate a geometry by a quaternion"""
    return transform(rotator(q), geometry)


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
