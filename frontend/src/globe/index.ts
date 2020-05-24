/*
 * decaffeinate suggestions:
 * DS001: Remove Babel/TypeScript constructor workaround
 * DS102: Remove unnecessary code created because of implicit returns
 * DS206: Consider reworking classes to avoid initClass
 * DS207: Consider shorter variations of null checks
 * Full docs: https://github.com/decaffeinate/decaffeinate/blob/master/docs/suggestions.md
 */
import React, {Component, createContext, useContext, createRef, createElement} from 'react';
import {findDOMNode} from 'react-dom';
import {StatefulComponent} from '@macrostrat/ui-components';
import T from 'prop-types';
import h from './hyper';
import {MapContext} from './context';
import {DraggableOverlay} from './drag-interaction';
import {min, max} from 'd3-array';
import {geoStereographic, geoOrthographic, geoGraticule, geoPath} from 'd3-geo';
import styles from './module.styl';

const GeoPath = function(props){
  const {geometry, ...rest} = props;
  let d = null;
  if (geometry != null) {
    const {renderPath} = useContext(MapContext);
    d = renderPath(geometry);
  }
  return h('path', {d, ...rest});
};

class Background extends Component {
  static initClass() {
    this.contextType = MapContext;
  }
  render() {
    return h(GeoPath, {
      geometry: {type: 'Sphere'},
      className: 'background',
      ...this.props
    });
  }
}
Background.initClass();

const Graticule = function(props){
  const graticule = geoGraticule()
    .step([10,10])
    .extent([
        [-180,-80],
        [180,80 + 1e-6]
      ]);
  return h(GeoPath, {
    className: 'graticule',
    geometry: graticule(),
    ...props
  });
};

class Globe extends StatefulComponent {
  static initClass() {
    this.propTypes = {
      projection: T.func.isRequired,
      width: T.number.isRequired,
      height: T.number.isRequired,
      keepNorthUp: T.bool,
      allowDragging: T.bool,
      setupProjection: T.func,
      modifyProjection: T.func,
      scale: T.number,
      translate: T.arrayOf(T.number)
    };
    this.defaultProps = {
      keepNorthUp: false,
      allowDragging: true,
      projection: geoOrthographic()
        .clipAngle(90)
        .precision(0.5),
      setupProjection(projection, {width, height, scale, translate}){
        if ((scale == null)) {
          const maxSize = min([width, height]);
          scale = maxSize/2;
        }
        if (translate == null) { translate = [width/2, height/2]; }
        return projection.scale(scale)
          .translate(translate);
      },
      modifyProjection(d){ return d; }
    };
  }

  constructor(props){
    {
      // Hack: trick Babel/TypeScript into allowing this before super.
      if (false) { super(); }
      let thisFn = (() => { return this; }).toString();
      let thisName = thisFn.match(/return (?:_assertThisInitialized\()*(\w+)\)*;/)[1];
      eval(`${thisName} = this;`);
    }
    this.componentDidUpdate = this.componentDidUpdate.bind(this);
    this.updateProjection = this.updateProjection.bind(this);
    this.dispatchEvent = this.dispatchEvent.bind(this);
    this.componentDidMount = this.componentDidMount.bind(this);
    super(props);

    this.mapElement = createRef();

    const {projection} = this.props;
    //projection.center(center)

    this.state = {
      projection,
      zoom: 1,
      canvasContexts: new Set([])
    };
  }

  componentDidUpdate(prevProps){
    let projection;
    const {width, height, scale, translate, setupProjection} = this.props;
    const sameDimensions = (prevProps.width === width) && (prevProps.height === height);
    const sameProjection = prevProps.projection === this.props.projection;
    const sameScale = (prevProps.scale === scale) && (prevProps.translate === translate);
    if (sameDimensions && sameProjection && sameScale) { return; }
    if (sameProjection) {
      ({projection} = this.state);
    } else {
      ({projection} = this.props);
    }

    const newProj = setupProjection(projection, {width,height, scale, translate});

    return this.updateProjection(newProj);
  }

  updateProjection(newProj){
    return this.updateState({projection: {$set: newProj}});
  }

  dispatchEvent(evt){
    const v = findDOMNode(this);
    const el = v.getElementsByClassName(styles.map)[0];
    // Simulate an event directly on the map's DOM element
    const {clientX, clientY} = evt;

    const e1 = new Event("mousedown", {clientX, clientY});
    const e2 = new Event("mouseup", {clientX, clientY});

    el.dispatchEvent(e1);
    return el.dispatchEvent(e2);
  }

  componentDidMount() {
    return this.componentDidUpdate.call(this,arguments);
  }

  render() {
    let {width, height, children, keepNorthUp, allowDragging, projection, ...rest} = this.props;
    const initialScale = projection.scale() || 500;

    ({projection} = this.state);
    const actions = (() => { let dispatchEvent, updateProjection, updateState;
    return ({
      updateState,
      updateProjection,
      dispatchEvent
      } = this); })();
    const renderPath = geoPath(projection);
    const value = {projection, renderPath, width, height, ...actions};

    const xmlns = "http://www.w3.org/2000/svg";
    const viewBox = `0 0 ${width} ${height}`;

    return h(MapContext.Provider, {value}, [
      createElement('svg', {className: 'globe', xmlns, width, height, viewBox, ...rest}, [
        h('g.map', {ref: this.mapElement}, [
          h(Background, {fill: 'dodgerblue'}),
          h(Graticule),
          children
        ]),
        h.if(allowDragging)(DraggableOverlay, {keepNorthUp, initialScale})
      ])
    ]);
  }
}
Globe.initClass();


export {Globe, MapContext};
