import { createContext } from "react";
import { StatefulComponent } from "@macrostrat/ui-components";
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

class MapSettingsProvider extends StatefulComponent {
  constructor(props) {
    super(props);
    this.state = {
      keepNorthUp: true,
      projection: projections[0],
    };
  }
  render() {
    const value = { ...this.state, projections, updateState: this.updateState };
    return h(MapSettingsContext.Provider, { value }, this.props.children);
  }
}

export { MapSettingsProvider, MapSettingsContext };
