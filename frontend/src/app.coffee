import {Component} from 'react'
import {WorldMap} from './world-map'
import ControlPanel from './control-panel'
import h from '@macrostrat/hyper'
import {RotationsProvider} from './rotations'
import T from 'prop-types'

class App extends Component
  constructor: ->
    super arguments...
    @state = {
      time: 0
      rotations: null
    }

  setTime: (value)=>
    @setState {time: value}

  render: ->
    {time} = @state
    h 'div', [
      h RotationsProvider, {time}, [
        h WorldMap
        h ControlPanel, {time, setTime: @setTime}
      ]
    ]


export default App
