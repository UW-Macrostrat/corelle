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
    }

  componentDidMount: ->
    try
      @getModelData()
    catch
      console.log "Could not get model data"

  getModelData: ->
    {get} = @context
    data = await get "/model"
    models = data.map (d)->d.name
    @setState {models}

  setTime: (value)=>
    @setState {time: value}

  setModel: (value)=>
    @setState {model: value}

  render: ->
    {time, model, models} = @state
    h 'div', [
      h RotationsProvider, {model, time}, [
        h WorldMap
        h ControlPanel, {setTime: @setTime, setModel: @setModel, models}
      ]
    ]

WrappedApp = (props)->
  h APIProvider, {baseURL}, (
    h MapSettingsProvider, null, (
      h App, props
    )
  )

export default WrappedApp
