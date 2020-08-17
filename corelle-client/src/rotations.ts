import { createContext, useContext, PropsWithChildren } from "react";
import h from "@macrostrat/hyper";
import { useAPIResult } from "@macrostrat/ui-components";
import Quaternion from "quaternion";
import { sph2cart, cart2sph } from "./math";
import join from "url-join";

// Drag to rotate globe
// http://bl.ocks.org/ivyywang/7c94cb5a3accd9913263
// https://stackoverflow.com/questions/16964993/compose-two-rotations-in-d3-geo-projection
// https://www.jasondavies.com/maps/rotate/

const defaultEndpoint = "https://birdnest.geology.wisc.edu/corelle/api";

const RotationsAPIContext = createContext({
  endpoint: defaultEndpoint,
});

const useRotationsAPI = (route, ...args): any[] => {
  const { endpoint } = useContext(RotationsAPIContext);
  return useAPIResult(join(endpoint, route), ...args);
};

const RotationsContext = createContext({ rotations: null });

type RotationOptions = {
  time: number;
  model: string;
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

type P = {
  endpoint: string;
  debounce: number;
} & RotationOptions;

function RotationsProvider(props: PropsWithChildren<P>) {
  const { time, children, model, endpoint, debounce } = props;
  const rotations: any[] = useAPIResult(
    join(endpoint, "/rotate"),
    { time: `${time}`, model, quaternion: "true" },
    { debounce }
  );

  const value = new RotationData({ rotations, model, time });

  return h(
    RotationsAPIContext.Provider,
    { value: { endpoint } },
    h(RotationsContext.Provider, {
      value,
      children,
    })
  );
}

RotationsProvider.defaultProps = {
  endpoint: defaultEndpoint,
  debounce: 1000,
};

export { RotationsProvider, RotationsContext, useRotationsAPI };
