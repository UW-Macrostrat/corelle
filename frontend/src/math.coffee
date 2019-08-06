import Quaternion from 'quaternion'

# Drag to rotate globe
# http://bl.ocks.org/ivyywang/7c94cb5a3accd9913263
# https://stackoverflow.com/questions/16964993/compose-two-rotations-in-d3-geo-projection
# https://www.jasondavies.com/maps/rotate/

# Should replace with inbuilt quaternion function
to_degrees = 180 / Math.PI
to_radians = Math.PI / 180
quat2euler = (q)->
  {w,x,y,z} = q
  # Half angle
  __ang = Math.acos(w)
  s = Math.sin(__ang)

  angle = 2 * __ang * to_degrees
  lat = Math.asin(z/s) * to_degrees
  lon = Math.atan2(y/s,x/s) * to_degrees

  return [lat, lon, angle]

euler2quat = (v)->
  [lat, lon, angle] = v.map (d)->d*to_radians
  w = Math.cos(angle/2)
  _s = Math.sin(angle/2)
  [x,y,z] = sph2cart([lon,lat]).map (d)->d*_s
  return new Quaternion(w, x, y, z)

sph2cart = (point)->
  [lon, lat] = point
  _lon = lon * to_radians
  _lat = lat * to_radians
  vec = [
    Math.cos(_lat)*Math.cos(_lon)
    Math.cos(_lat)*Math.sin(_lon)
    Math.sin(_lat)
  ]

  return vec

cart2sph = (vec)->
  [x,y,z] = vec
  lat = Math.asin(z) * to_degrees
  lon = Math.atan2(y, x) * to_degrees
  return [lon, lat]

export {quat2euler, euler2quat, sph2cart, cart2sph}
