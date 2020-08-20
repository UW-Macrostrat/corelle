import Quaternion from "quaternion";
import { sph2cart, cart2sph } from "./math";

// Drag to rotate globe
// http://bl.ocks.org/ivyywang/7c94cb5a3accd9913263
// https://stackoverflow.com/questions/16964993/compose-two-rotations-in-d3-geo-projection
// https://www.jasondavies.com/maps/rotate/

type RotationOptions = {
  time: number;
  model?: string;
};

class RotationData {
  rotations: any = [];
  model: any;
  time: number;
  constructor(options: RotationOptions & { rotations: any[] }) {
    const { rotations, model, time } = options;
    this.rotations = rotations;
    this.model = model;
    this.time = time;
    this.plateRotation = this.plateRotation.bind(this);
    this.geographyRotator = this.geographyRotator.bind(this);
    this.rotatedProjection = this.rotatedProjection.bind(this);
  }

  plateRotation(id) {
    const rot = this.rotations.find((d) => d.plate_id === id);
    if (rot == null) return null;
    const q = Quaternion(rot.quaternion);
    return q;
  }

  geographyRotator(id) {
    const { time } = this;
    const identity = (arr) => arr;
    if (time === 0) {
      return identity;
    }
    const q = this.plateRotation(id);
    if (q == null) {
      return identity;
    }
    //angles = quat2euler(q)
    return function (point) {
      const vec = sph2cart(point);
      const v1 = q.rotateVector(vec);
      return cart2sph(v1);
    };
  }

  rotatedProjection(id, projection) {
    if (this.time === 0) return projection;
    const q = this.plateRotation(id);
    if (q == null) return null;
    return function () {
      return projection.apply(this, arguments);
    };
  }
}

export { RotationData, RotationOptions };
