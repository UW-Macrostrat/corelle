import { createContext } from "react";
import { useImmutableState } from "@macrostrat/ui-components";
import h from "@macrostrat/hyper";
import {
  geoOrthographic,
  geoStereographic,
  geoGnomonic,
  geoNaturalEarth1,
} from "d3-geo";

// Animate these projection transformations
// https://bl.ocks.org/mbostock/3711652

const projections = [
  {
    id: "Orthographic",
    func: geoOrthographic().precision(0.5).clipAngle(90),
  },
  {
    id: "Stereographic",
    func: geoStereographic().precision(0.5),
  },
  {
    id: "Gnomonic",
    func: geoGnomonic().precision(0.5),
  },
  {
    id: "Natural Earth",
    func: geoNaturalEarth1(),
  },
];

const MapSettingsContext = createContext({ projections });

function MapSettingsProvider({ children }) {
  const [state, updateState] = useImmutableState({
    keepNorthUp: true,
    projection: projections[0],
  });

  const value = { ...state, projections, updateState };
  return h(MapSettingsContext.Provider, { value }, children);
}

export { MapSettingsProvider, MapSettingsContext };
