import { createContext, useContext, PropsWithChildren } from "react";
import h from "@macrostrat/hyper";
import { useAPIResult } from "@macrostrat/ui-components";
import join from "url-join";
import { RotationData, RotationOptions } from "../rotations";

// Drag to rotate globe
// http://bl.ocks.org/ivyywang/7c94cb5a3accd9913263
// https://stackoverflow.com/questions/16964993/compose-two-rotations-in-d3-geo-projection
// https://www.jasondavies.com/maps/rotate/

// TODO: this is hardcoded now essentially
const defaultEndpoint = "https://rotate.macrostrat.org/api";

const RotationsAPIContext = createContext({
  endpoint: defaultEndpoint,
});

const useRotationsAPI = (route, ...args): any[] => {
  const { endpoint } = useContext(RotationsAPIContext);
  const uri = join(endpoint, route);
  return useAPIResult(uri, ...args);
};

const defaultRotations = new RotationData({ time: 0, rotations: [] });

const RotationsContext = createContext<RotationData>(defaultRotations);

type P = {
  endpoint?: string;
  debounce: number;
} & RotationOptions;

function RotationsProvider(props: PropsWithChildren<P>) {
  const { time, children, model, endpoint, debounce } = props;
  const rotations: any[] =
    useAPIResult(
      join(endpoint, "/rotate"),
      { time: `${time}`, model, quaternion: "true" },
      { debounce }
    ) ?? [];

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

const useRotations = () => useContext(RotationsContext);

export { RotationsProvider, RotationsContext, useRotationsAPI, useRotations };
