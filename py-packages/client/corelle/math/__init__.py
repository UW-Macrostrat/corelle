import numpy as N
import quaternion as Q
from .util import unit_vector


def sph2cart(lon, lat):
    _lon = N.radians(lon)
    _lat = N.radians(lat)
    x = N.cos(_lat) * N.cos(_lon)
    y = N.cos(_lat) * N.sin(_lon)
    z = N.sin(_lat)
    return unit_vector(x, y, z)


def cart2sph(unit_vec):
    (x, y, z) = unit_vec
    lat = N.arcsin(z)
    lon = N.arctan2(y, x)
    return N.degrees(lon), N.degrees(lat)


def euler_to_quaternion(euler_pole):
    lon, lat, angle = [float(i) for i in euler_pole]
    angle = N.radians(angle)
    if angle < 0:
        angle += 2 * N.pi
    w = N.cos(angle / 2)
    v = sph2cart(lon, lat) * N.sin(angle / 2)
    return N.quaternion(w, *v)


def quaternion_to_euler(q):
    angle = 2 * N.arccos(q.w)
    lon, lat = cart2sph(q.vec / N.sin(angle / 2))
    return lon, lat, N.degrees(angle)


def euler_equal(a1, a2):
    a2 = list(a2)
    a1 = list(a1)
    if N.sign(a1[1]) != N.sign(a2[1]):
        a2[1] *= -1
        a2[0] += 180
        if a2[0] > 180:
            a2[0] -= 360
        a2[2] *= -1
    return N.allclose(a1, a2, atol=0.001)
