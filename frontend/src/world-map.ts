import hyper from "@macrostrat/hyper";
import { Component, useContext } from "react";
import { max } from "d3-array";
import { ResizeSensor } from "@blueprintjs/core";
import {
  PlateFeatureLayer,
  RotationsContext,
  PlatePolygons,
} from "@macrostrat/corelle";
import { Globe, MapContext } from "@macrostrat/map-components";
import "@macrostrat/map-components/dist/esm/index.css";

import { MapSettingsContext } from "./map-settings";
import chroma from "chroma-js";

import * as styles from "./main.module.styl";

const h = hyper.styled(styles);

class WorldMapInner extends Component<any, any> {
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

function Background(props) {
  const { renderPath } = useContext(MapContext);
  return h("path.background", {
    d: renderPath({ type: "Sphere" }),
    ...props,
  });
}

class WorldMap extends Component<any, any> {
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
            h.if(featureDataset != null)(PlateFeatureLayer, {
              name: featureDataset,
              style: {
                fill: "#E9FCEA",
                stroke: chroma("#E9FCEA").darken(0.3),
              },
            }),
          ]
        )
      )
    );
  }
}

export { WorldMap };
