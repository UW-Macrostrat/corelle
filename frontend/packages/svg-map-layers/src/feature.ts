import h from "@macrostrat/hyper";
import { useContext } from "react";
import { RotationsContext, useRotationsAPI, useRotations } from "./provider";
import {
  MapContext,
  MapCanvasContext,
  FeatureLayer,
} from "@macrostrat/svg-map-components";
import { pathGenerator } from "@corelle/rotations";

function usePathGenerator(plateId, context = null) {
  // Filter out features that are too young
  const { geographyRotator } = useRotations();
  const ctx = useContext(MapContext);

  const { projection } = ctx;

  if (projection == null) console.log("Projection not found");

  if (projection == null || geographyRotator == null) return null;

  const rotate = geographyRotator(plateId);
  if (rotate == null) return null;

  return pathGenerator(projection, rotate, context);
}

function PlateFeature(props) {
  /** An arbitrary feature tied to a plate */
  const { feature, youngLim, oldLim, plateId, ...rest } = props;
  // Filter out features that are too young
  const { time } = useRotations();
  const { inCanvas, context } = useContext(MapCanvasContext);
  const proj = usePathGenerator(plateId, context);

  if (oldLim < time) return null;
  // Filter out features that are too old (unlikely given current models)
  if (youngLim > time) return null;
  if (proj == null) return null;

  const d = proj(feature);
  // Make it work in canvas
  if (inCanvas) {
    return null;
  } else {
    return h("path", { d, ...rest });
  }
}

interface FeatureDatasetProps {
  name: string;
  style?: { [k: string]: any };
  useCanvas?: boolean;
}

// @ts-ignore
const PlateFeatureLayer = function (props: FeatureDatasetProps) {
  const { name, style, useCanvas = true } = props;
  const { model } = useContext<any>(RotationsContext);

  const data: any[] = useRotationsAPI(`/feature/${name}`, { model }) ?? [];

  return h(
    FeatureLayer,
    { className: name, useCanvas, style },
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
    }),
  );
};

export { PlateFeature, PlateFeatureLayer, usePathGenerator };
