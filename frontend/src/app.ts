/*
 * decaffeinate suggestions:
 * DS001: Remove Babel/TypeScript constructor workaround
 * DS102: Remove unnecessary code created because of implicit returns
 * DS206: Consider reworking classes to avoid initClass
 * Full docs: https://github.com/decaffeinate/decaffeinate/blob/master/docs/suggestions.md
 */
import {Component} from 'react';
import {WorldMap} from './world-map';
import ControlPanel from './control-panel';
import h from '@macrostrat/hyper';
import {RotationsProvider} from './rotations';
import {MapSettingsProvider} from './map-settings';
import T from 'prop-types';
import {APIProvider, APIContext} from '@macrostrat/ui-components';

let baseURL = process.env.PUBLIC_URL || "";
baseURL += "/api";

class App extends Component {
  static initClass() {
    this.contextType = APIContext;
  }
  constructor(props) {
    super(props);

    this.setTime = this.setTime.bind(this);
    this.setModel = this.setModel.bind(this);
    this.state = {
      time: 0,
      rotations: null,
      model: "Seton2012",
      models: ["Seton2012"],
      featureDataset: "ne_110m_land",
      featureDatasets: ["ne_110m_land"]
    };

  }

  componentDidMount() {
    try {
      this.getModelData();
      return this.getFeatureDatasets();
    } catch (error) {
      return console.log("Could not get model data");
    }
  }

  async getModelData() {
    const {get} = this.context;
    const data = await get("/model");
    const models = data.map(d => d.name);
    return this.setState({models});
  }

  async getFeatureDatasets() {
    const {get} = this.context;
    const data = await get("/feature");
    return this.setState({featureDatasets: data});
  }

  setTime(value){
    return this.setState({time: value});
  }

  setModel(value){
    return this.setState({model: value});
  }

  render() {
    const {time, model, models, featureDataset, featureDatasets} = this.state;
    return h('div', [
      h(RotationsProvider, {model, time}, [
        h(WorldMap, {featureDataset}),
        h(ControlPanel, {
          setTime: this.setTime,
          setModel: this.setModel,
          featureDataset,
          featureDatasets,
          setFeatureDataset: v=> this.setState({featureDataset: v}),
          models
        })
      ])
    ]);
  }
}
App.initClass();

const WrappedApp = props => h(APIProvider, {baseURL}, (
  h(MapSettingsProvider, null, (
    h(App, props)
  ))
)
);

export default WrappedApp;
