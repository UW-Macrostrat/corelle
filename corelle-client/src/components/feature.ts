import h from "@macrostrat/hyper";
import { useContext } from "react";
import { geoTransform, geoPath } from "d3-geo";
import { RotationsContext, useRotationsAPI } from "./provider";

import {
  MapContext,
  MapCanvasContext,
  FeatureLayer,
} from "@macrostrat/map-components";

function PlateFeature(props) {
  /** An arbitrary feature tied to a plate */
  let proj;
  const { feature, youngLim, oldLim, plateId, ...rest } = props;
  // Filter out features that are too young
  const { geographyRotator, time } = useContext(RotationsContext);
  if (geographyRotator == null) {
    return null;
  }
  if (oldLim < time) {
    return null;
  }
  // Filter out features that are too old (unlikely given current models)
  if (youngLim > time) {
    return null;
  }
  const { projection } = useContext(MapContext);
  if (projection == null) return null;

  const rotate = geographyRotator(plateId);

  const trans = geoTransform({
    point(lon, lat) {
      const [x, y] = rotate([lon, lat]);
      return this.stream.point(x, y);
    },
  });

  // This ordering makes no sense but whatever
  const stream = (s) =>
    // https://stackoverflow.com/questions/27557724/what-is-the-proper-way-to-use-d3s-projection-stream
    trans.stream(projection.stream(s));

  // Make it work in canvas
  const { inCanvas, context } = useContext(MapCanvasContext);
  if (inCanvas) {
    if (context != null) {
      proj = geoPath({ stream }, context);
      proj(feature);
    }
    return null;
  }

  // Combined projection
  proj = geoPath({ stream });
  const d = proj(feature);

  return h("path", { d, ...rest });
}

interface FeatureDatasetProps {
  name: string;
  style?: { [k: string]: any };
}

// @ts-ignore
const PlateFeatureLayer = function (props: FeatureDatasetProps) {
  const { name, style } = props;
  const { model } = useContext<any>(RotationsContext);

  const data: any[] = useRotationsAPI(`/feature/${name}`, { model }) ?? [];

  return h(
    FeatureLayer,
    { className: name, useCanvas: true, style },
    data.map(function (feature, i) {
      const { id, properties } = feature;
      const { plate_id, old_lim, young_lim } = properties;
      return h(PlateFeature, {
        key: i,
        feature,
        plateId: plate_id,
        oldLim: old_lim,
        youngLim: young_lim,
      });
    })
  );
};

export { PlateFeature, PlateFeatureLayer };
