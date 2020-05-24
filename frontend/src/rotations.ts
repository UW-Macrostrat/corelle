import {Component, createContext} from 'react';
import h from '@macrostrat/hyper';
import {APIResultView} from '@macrostrat/ui-components';
import T from 'prop-types';
import Quaternion from 'quaternion';
import {quat2euler, sph2cart, cart2sph} from './math';

// Drag to rotate globe
// http://bl.ocks.org/ivyywang/7c94cb5a3accd9913263
// https://stackoverflow.com/questions/16964993/compose-two-rotations-in-d3-geo-projection
// https://www.jasondavies.com/maps/rotate/

const RotationsContext = createContext({rotations: null});

class __RotationsProvider extends Component {
  constructor(props, ctx) {
    super(props, ctx);
    this.plateRotation = this.plateRotation.bind(this);
    this.geographyRotator = this.geographyRotator.bind(this);
    this.rotatedProjection = this.rotatedProjection.bind(this);
  }

  static propTypes = {
    time: T.number.isRequired,
    model: T.string.isRequired,
    rotations: T.arrayOf(T.object)
  }

  render() {
    const {rotations, time, model, models} = this.props;
    const value = {
      rotations,
      model,
      time,
      plateRotation: this.plateRotation,
      rotatedProjection: this.rotatedProjection,
      geographyRotator: this.geographyRotator
    };

    return h(RotationsContext.Provider, {
      value
    }, this.props.children);
  }

  plateRotation(id){
    const {rotations} = this.props;
    const rot = rotations.find(d => d.plate_id === id);
    if ((rot == null)) {
      return null;
    }
    const q = Quaternion(rot.quaternion);
    return q;
  }

  geographyRotator(id){
    const {time} = this.props;
    const identity = arr => arr;
    if (time === 0) {
      return identity;
    }
    const q = this.plateRotation(id);
    if ((q == null)) {
      return identity;
    }
    //angles = quat2euler(q)
    return function(point){
      const vec = sph2cart(point);
      const v1 = q.rotateVector(vec);
      return cart2sph(v1);
    };
  }
    //return geoRotation(angles)

  rotatedProjection(id, projection){
    const {time} = this.props;
    if (time === 0) {
      return projection;
    }
    const q = this.plateRotation(id);
    if ((q == null)) {
      return null;
    }
    const angles = quat2euler(q);
    //console.log angles
    return function() {
      return projection.apply(this, arguments);
    };
  }
}

const RotationsProvider = function(props){
  const {time, children, model} = props;
  return h(APIResultView, {
    route: "/rotate",
    params: {time, model, quaternion: true},
    placeholder: null,
    debounce: 1000
  }, (data)=> {
    return h(__RotationsProvider, {time, model, rotations: data}, children);
  });
};

RotationsProvider.propTypes = __RotationsProvider.propTypes;

export {RotationsProvider, RotationsContext};
