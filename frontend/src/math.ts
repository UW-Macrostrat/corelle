import Quaternion from 'quaternion';

// Drag to rotate globe
// http://bl.ocks.org/ivyywang/7c94cb5a3accd9913263
// https://stackoverflow.com/questions/16964993/compose-two-rotations-in-d3-geo-projection
// https://www.jasondavies.com/maps/rotate/

// Should replace with inbuilt quaternion function
const to_degrees = 180 / Math.PI;
const to_radians = Math.PI / 180;
const quat2euler = function(q){
  const {w,x,y,z} = q;
  // Half angle
  const __ang = Math.acos(w);
  const s = Math.sin(__ang);

  const angle = 2 * __ang * to_degrees;
  const lat = Math.asin(z/s) * to_degrees;
  const lon = Math.atan2(y/s,x/s) * to_degrees;

  return [lat, lon, angle];
};

const euler2quat = function(v){
  const [lat, lon, angle] = v.map(d => d*to_radians);
  const w = Math.cos(angle/2);
  const _s = Math.sin(angle/2);
  const [x,y,z] = sph2cart([lon,lat]).map(d => d*_s);
  return new Quaternion(w, x, y, z);
};

var sph2cart = function(point){
  const [lon, lat] = point;
  const _lon = lon * to_radians;
  const _lat = lat * to_radians;
  const vec = [
    Math.cos(_lat)*Math.cos(_lon),
    Math.cos(_lat)*Math.sin(_lon),
    Math.sin(_lat)
  ];

  return vec;
};

const cart2sph = function(vec){
  const [x,y,z] = vec;
  const lat = Math.asin(z) * to_degrees;
  const lon = Math.atan2(y, x) * to_degrees;
  return [lon, lat];
};

export {quat2euler, euler2quat, sph2cart, cart2sph};
