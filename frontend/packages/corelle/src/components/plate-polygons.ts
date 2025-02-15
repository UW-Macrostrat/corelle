import h from "@macrostrat/hyper";
import { useContext } from "react";
import { FeatureLayer } from "@macrostrat/svg-map-components";
import { PlateFeature } from "./feature";
import { RotationsContext, useRotationsAPI } from "./provider";

function usePlatePolygons(modelOverride: string | null = null) {
  const { model } = useContext<any>(RotationsContext);
  console.log(model);
  return useRotationsAPI("/plates", { model: modelOverride ?? model });
}

function PlatePolygon(props) {
  // An arbitrary feature tied to a plate
  const { feature, ...rest } = props;
  const { id, properties } = feature;
  const { old_lim, young_lim, plate_id } = properties;
  return h(PlateFeature, {
    feature,
    oldLim: old_lim,
    youngLim: young_lim,
    plateId: plate_id ?? id,
    ...rest,
  });
}

function PlatePolygons(props: { style: any }) {
  const data: any[] = usePlatePolygons();
  if (data == null) {
    return null;
  }

  const style = {
    fill: "rgba(200,200,200, 0.3)",
    stroke: "rgba(200,200,200, 0.8)",
    strokeWidth: 1,
    ...(props.style ?? {}),
  };

  return h(
    FeatureLayer,
    {
      useCanvas: true,
      className: "plates",
      style,
    },
    data.map((feature, i) => h(PlatePolygon, { key: i, feature }))
  );
}

export { PlatePolygons, usePlatePolygons };
