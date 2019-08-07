import numpy as N
import quaternion as Q
from .util import unit_vector

def sph2cart(lon,lat):
    _lon = N.radians(lon)
    _lat = N.radians(lat)
    x = N.cos(_lat)*N.cos(_lon)
    y = N.cos(_lat)*N.sin(_lon)
    z = N.sin(_lat)
    return unit_vector(x,y,z)

def cart2sph(unit_vec):
    (x, y, z) = unit_vec
    lat = N.arcsin(z)
    lon = N.arctan2(y, x)
    return N.degrees(lon), N.degrees(lat)

# Yaw should be equivalent to longitude, pitch to latitude, and roll to angle

def euler_to_quaternion(euler_pole):
    lat, lon, angle = [float(i) for i in euler_pole]
    yaw = N.radians(lon)
    pitch = N.radians(lat)
    roll = N.radians(angle)

    cy = N.cos(yaw * 0.5)
    sy = N.sin(yaw * 0.5)
    cp = N.cos(pitch * 0.5)
    sp = N.sin(pitch * 0.5)
    cr = N.cos(roll * 0.5)
    sr = N.sin(roll * 0.5)

    return N.quaternion(
        cy * cp * cr + sy * sp * sr,
        cy * cp * sr - sy * sp * cr,
        sy * cp * sr + cy * sp * cr,
        sy * cp * cr - cy * sp * sr)

def quaternion_to_euler(q):
    roll = N.arctan2(2*(q.w*q.x+q.y*q.z), 1-2*(q.x**2+q.y**2))
    pitch = N.arcsin(2*(q.w*q.y-q.z*q.x))
    yaw = N.arctan2(2*(q.w*q.z+q.x*q.y), 1-2*(q.y**2+q.z**2))
    lat = N.degrees(yaw)
    lon = N.degrees(pitch)
    angle = N.degrees(roll)
    return (lat, lon, angle)
