import h from "@macrostrat/hyper";
import { useContext, useRef } from "react";
import {
  PlateFeatureLayer,
  RotationsContext,
  PlatePolygons,
  PlateFeature,
} from "@macrostrat/corelle";
import { Globe, MapContext } from "@macrostrat/svg-map-components";

import { MapSettingsContext } from "./map-settings";
import chroma from "chroma-js";

import "./app.styl";
import { useElementSize } from "@macrostrat/ui-components";

function WorldMapInner(props) {
  const { width, height, keepNorthUp, projection, children } = props;
  const { model } = useContext(RotationsContext);
  return h(
    Globe,
    {
      keepNorthUp,
      projection: projection.func,
      width,
      height,
      scale: Math.max(width, height) / 2 - 20,
    },
    children,
  );
}

function Background(props) {
  const { renderPath } = useContext(MapContext);
  return h("path.background", {
    d: renderPath({ type: "Sphere" }),
    ...props,
  });
}

function WorldMap({ featureDataset }: { featureDataset: any }) {
  const { keepNorthUp, projection } = useContext<any>(MapSettingsContext);
  const ref = useRef(null);
  const { width, height } = useElementSize(ref) ?? {};
  return h(
    "div.world-map",
    { ref },
    h(WorldMapInner, { width, height, keepNorthUp, projection, margin: 10 }, [
      h(PlatePolygons),
      h.if(featureDataset != null)(PlateFeatureLayer, {
        name: featureDataset,
        style: {
          fill: "#E9FCEA",
          stroke: chroma("#E9FCEA").darken(0.3),
        },
      }),
    ]),
  );
}

export { WorldMap };
