/*
 * decaffeinate suggestions:
 * DS001: Remove Babel/TypeScript constructor workaround
 * DS102: Remove unnecessary code created because of implicit returns
 * DS206: Consider reworking classes to avoid initClass
 * DS207: Consider shorter variations of null checks
 * Full docs: https://github.com/decaffeinate/decaffeinate/blob/master/docs/suggestions.md
 */
import hyper from '@macrostrat/hyper';
import React, {Component, useContext, createElement} from 'react';
import {APIResultView} from '@macrostrat/ui-components';
import {min, max} from 'd3-array';
import {select} from 'd3-selection';
import {geoStereographic, geoTransform} from 'd3-geo';
import {ResizeSensor, Popover, Spinner} from '@blueprintjs/core';
import {RotationsContext} from './rotations';
import {Globe, MapContext} from './globe';
import {geoPath} from 'd3-geo';
import {MapCanvasContext, CanvasLayer} from './globe/canvas-layer';
import {MapSettingsContext} from './map-settings';
import chroma from 'chroma-js';

import styles from './main.styl';

const h = hyper.styled(styles);

const FeatureLayer = function(props){
  let {useCanvas, ...rest} = props;
  if (useCanvas == null) { useCanvas = true; }
  if (useCanvas) {
    return h(CanvasLayer, rest);
  }
  return h('g', rest);
};

const PlateFeature = function(props){
  // An arbitrary feature tied to a plate
  let proj;
  const {feature, youngLim, oldLim, plateId, ...rest} = props;
  // Filter out features that are too young
  const {geographyRotator, time} = useContext(RotationsContext) || {};
  if (geographyRotator == null) { return null; }
  if (oldLim < time) { return null; }
  // Filter out features that are too old (unlikely given current models)
  if (youngLim > time) { return null; }
  const {projection} = useContext(MapContext);
  const rotate = geographyRotator(plateId);

  const trans = geoTransform({
    point(lon,lat){
      const [x,y] = rotate([lon,lat]);
      return this.stream.point(x,y);
    }
  });

  const stream = s => // This ordering makes no sense but whatever
  // https://stackoverflow.com/questions/27557724/what-is-the-proper-way-to-use-d3s-projection-stream
  trans.stream(projection.stream(s));

  // Make it work in canvas
  const {inCanvas, context} = useContext(MapCanvasContext);
  if (inCanvas) {
    if (context != null) {
      proj = geoPath({stream}, context);
      proj(feature);
    }
    return null;
  }

  // Combined projection
  proj = geoPath({stream});
  const d = proj(feature);

  return h('path', {d, ...rest});
};

const PlatePolygon = function(props){
  // An arbitrary feature tied to a plate
  const {feature, ...rest} = props;
  const {id, properties} = feature;
  const {old_lim, young_lim} = properties;
  return h(PlateFeature, {feature, oldLim: old_lim, youngLim: young_lim, plateId: id, ...rest});
};

const PlatePolygons = function(props){
  const {model} = useContext(RotationsContext);
  const {inCanvas, clearCanvas} = useContext(MapCanvasContext);

  return h(APIResultView, {
    route: "/plates",
    params: {model},
    placeholder: null
  }, data=> {
    if (data == null) { return null; }

    const style = {
      fill: 'rgba(200,200,200, 0.3)',
      stroke: 'rgba(200,200,200, 0.8)',
      strokeWidth: 1
    };

    return h(FeatureLayer, {
      useCanvas: true,
      className: 'plates',
      style
    }, data.map((feature, i) => h(PlatePolygon, {key: i, feature})));
});
};

const PlateFeatureDataset = function(props){
  const {name} = props;
  const {model} = useContext(RotationsContext);
  return h(APIResultView, {
    route: `/feature/${name}`,
    params: {model},
    placeholder: null
  }, data=> {
    if (data == null) { return null; }

    const style = {
      fill: '#E9FCEA',
      stroke: chroma('#E9FCEA').darken().hex(),
      strokeWidth: 1
    };

    return h(FeatureLayer, {className: name, useCanvas: true, style}, data.map(function(feature, i){
      const {id, properties} = feature;
      const {plate_id, old_lim, young_lim} = properties;
      return h(PlateFeature, {
        key: i,
        feature,
        plateId: plate_id,
        oldLim: old_lim,
        youngLim: young_lim
      });}));
});
};

class WorldMapInner extends Component {
  static initClass() {
    this.contextType = RotationsContext;
  }
  render() {
    const {width, height, margin, marginRight, keepNorthUp, projection, children} = this.props;
    const {model} = this.context;
    return h(Globe, {
      keepNorthUp,
      projection: projection.func,
      width,
      height,
      scale: (max([width,height])/2)-20
    }, children);
  }
}
WorldMapInner.initClass();


class WorldMap extends Component {
  static initClass() {
    this.contextType = MapSettingsContext;
  }
  constructor() {
    {
      // Hack: trick Babel/TypeScript into allowing this before super.
      if (false) { super(); }
      let thisFn = (() => { return this; }).toString();
      let thisName = thisFn.match(/return (?:_assertThisInitialized\()*(\w+)\)*;/)[1];
      eval(`${thisName} = this;`);
    }
    this.onResize = this.onResize.bind(this);
    super(...arguments);
    this.state = {
      width: 1100,
      height: 800
    };
  }

  onResize(entries){
    const {width, height} = entries[0].contentRect;
    return this.setState({width, height});
  }

  render() {
    const {width, height} = this.state;
    const {featureDataset} = this.props;
    const {keepNorthUp, projection} = this.context;
    return h(ResizeSensor, {onResize: this.onResize}, (
      h('div.world-map', null, (
        h(WorldMapInner, {width, height, margin: 10, keepNorthUp, projection}, [
          h(PlatePolygons),
          h.if(featureDataset != null)(PlateFeatureDataset, {name: featureDataset})
        ])
      ))
    )
    );
  }
}
WorldMap.initClass();

export {WorldMap};
