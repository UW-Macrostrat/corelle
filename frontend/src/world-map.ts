import hyper from "@macrostrat/hyper";
import { Component, useContext } from "react";
import { APIResultView } from "@macrostrat/ui-components";
import { max } from "d3-array";
import { ResizeSensor } from "@blueprintjs/core";
import { RotationsContext } from "./rotations";
import { PlateFeature, PlateFeatureDataset } from "@macrostrat/corelle-client";

import {
  Globe,
  MapContext,
  MapCanvasContext,
  FeatureLayer,
} from "@macrostrat/map-components";
import { MapSettingsContext } from "./map-settings";
import chroma from "chroma-js";

import styles from "./main.styl";

const h = hyper.styled(styles);

const PlatePolygon = function (props) {
  // An arbitrary feature tied to a plate
  const { feature, ...rest } = props;
  const { id, properties } = feature;
  const { old_lim, young_lim } = properties;
  return h(PlateFeature, {
    feature,
    oldLim: old_lim,
    youngLim: young_lim,
    plateId: id,
    ...rest,
  });
};

const PlatePolygons = function (props) {
  const { model } = useContext(RotationsContext);
  const { inCanvas, clearCanvas } = useContext(MapCanvasContext);

  return h(
    APIResultView,
    {
      route: "/plates",
      params: { model },
      placeholder: null,
    },
    (data) => {
      if (data == null) {
        return null;
      }

      const style = {
        fill: "rgba(200,200,200, 0.3)",
        stroke: "rgba(200,200,200, 0.8)",
        strokeWidth: 1,
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
  );
};

class WorldMapInner extends Component {
  static contextType = RotationsContext;
  render() {
    const { width, height, keepNorthUp, projection, children } = this.props;
    const { model } = this.context;
    return h(
      Globe,
      {
        keepNorthUp,
        projection: projection.func,
        width,
        height,
        scale: max([width, height]) / 2 - 20,
      },
      children
    );
  }
}

const Background = (props) => {
  const { renderPath } = useContext(MapContext);
  return h("path.background", {
    d: renderPath({ type: "Sphere" }),
    ...props,
  });
};

class WorldMap extends Component {
  static contextType = MapSettingsContext;
  constructor(props) {
    super(props);
    this.onResize = this.onResize.bind(this);
    this.state = {
      width: 1100,
      height: 800,
    };
  }

  onResize(entries) {
    const { width, height } = entries[0].contentRect;
    return this.setState({ width, height });
  }

  render() {
    const { width, height } = this.state;
    const { featureDataset } = this.props;
    const { keepNorthUp, projection } = this.context;
    return h(
      ResizeSensor,
      { onResize: this.onResize },
      h(
        "div.world-map",
        null,
        h(
          WorldMapInner,
          { width, height, margin: 10, keepNorthUp, projection },
          [
            h(PlatePolygons),
            h.if(featureDataset != null)(PlateFeatureDataset, {
              name: featureDataset,
            }),
          ]
        )
      )
    );
  }
}

export { WorldMap };
