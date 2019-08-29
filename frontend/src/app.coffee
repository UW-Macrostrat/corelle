import {Component} from 'react'
import {WorldMap} from './world-map'
import ControlPanel from './control-panel'
import h from '@macrostrat/hyper'
import {RotationsProvider} from './rotations'
import {MapSettingsProvider} from './map-settings'
import T from 'prop-types'
import {APIProvider, APIContext} from '@macrostrat/ui-components'

baseURL = process.env.PUBLIC_URL or ""
baseURL += "/api"

class App extends Component
  @contextType: APIContext
  constructor: ->
    super arguments...
    @state = {
      time: 0
      rotations: null
      model: "Seton2012"
      models: ["Seton2012"]
      featureDataset: "ne_110m_land"
      featureDatasets: ["ne_110m_land"]
    }

  componentDidMount: ->
    try
      @getModelData()
      @getFeatureDatasets()
    catch
      console.log "Could not get model data"

  getModelData: ->
    {get} = @context
    data = await get "/model"
    models = data.map (d)->d.name
    @setState {models}

  getFeatureDatasets: ->
    {get} = @context
    data = await get "/feature"
    @setState {featureDatasets: data}

  setTime: (value)=>
    @setState {time: value}

  setModel: (value)=>
    @setState {model: value}

  render: ->
    {time, model, models, featureDataset, featureDatasets} = @state
    h 'div', [
      h RotationsProvider, {model, time}, [
        h WorldMap, {featureDataset}
        h ControlPanel, {
          setTime: @setTime,
          setModel: @setModel,
          featureDataset,
          featureDatasets,
          setFeatureDataset: (v)=>@setState({featureDataset: v}),
          models
        }
      ]
    ]

WrappedApp = (props)->
  h APIProvider, {baseURL}, (
    h MapSettingsProvider, null, (
      h App, props
    )
  )

export default WrappedApp
