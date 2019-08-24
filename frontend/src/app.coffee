import {Component} from 'react'
import {WorldMap} from './world-map'
import ControlPanel from './control-panel'
import h from '@macrostrat/hyper'
import {RotationsProvider} from './rotations'
import T from 'prop-types'
import {get} from 'axios'
import {APIProvider} from '@macrostrat/ui-components'

baseURL = process.env.PUBLIC_URL or ""
baseURL += "/api"

class App extends Component
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
    {data} = await get "#{baseURL}/model"
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
    h App, props
  )

export default App
