#!/usr/bin/env python
from corelle_helpers import rotate_features, rotate_geometry
import numpy as N
from requests import get

rotations = get(
    "https://birdnest.geology.wisc.edu/corelle/api/rotate?model=Wright2013&time=120&quaternion=true"
).json()

# API call returns GeoJSON format plates
res = get("https://birdnest.geology.wisc.edu/corelle/api/plates?model=Wright2013")
features = res.json()

# Rotate our coastline featrues
rotated_features = list(rotate_features(rotations, features))
