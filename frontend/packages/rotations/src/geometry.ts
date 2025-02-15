import { geoTransform, geoPath, GeoProjection } from "d3-geo";

type RotateFunction = (coords: [number, number]) => [number, number];

export function pathGenerator(
  projection: GeoProjection,
  rotation: RotateFunction,
  canvasContext = null,
) {
  /** Returns a composite of a geo projection and a rotation
   * Optionally, a canvas context can be provided to render to a canvas
   * */
  // Filter out features that are too young
  const trans = geoTransform({
    point(lon, lat) {
      const [x, y] = rotation([lon, lat]);
      return this.stream.point(x, y);
    },
  });

  // This ordering makes no sense but whatever
  const stream = (s) =>
    // https://stackoverflow.com/questions/27557724/what-is-the-proper-way-to-use-d3s-projection-stream
    trans.stream(projection.stream(s));

  return geoPath({ stream }, canvasContext);
}
