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

import "./app.styl";
import { useElementSize } from "@macrostrat/ui-components";

function WorldMapInner(props) {
  const { width, height, keepNorthUp, projection, children } = props;
  const { model } = useContext(RotationsContext);

  if (width == null || height == null) return null;

  const minScale = Math.min(width, height) / 2 - 20;
  const baseScale = Math.max(width, height) / 2 - 20;
  const maxScale = baseScale * 2;

  return h(
    Globe,
    {
      keepNorthUp,
      projection: projection.func,
      width,
      height,
      margin: 0,
      scale: baseScale,
      zoomScaleExtent: [minScale, maxScale],
      allowZoom: true,
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
    h(WorldMapInner, { width, height, keepNorthUp, projection }, [
      h(PlatePolygons),
      h.if(featureDataset != null)(PlateFeatureLayer, {
        name: featureDataset,
        style: {
          fill: "#E9FCEA",
          stroke: "#c9d5c9",
        },
      }),
    ]),
  );
}

export { WorldMap };
