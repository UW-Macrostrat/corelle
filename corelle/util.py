import numpy as N

def vector(*args):
    return N.array(args)

def unit_vector(*args):
    v = vector(args)
    return v/N.linalg.norm(v)
