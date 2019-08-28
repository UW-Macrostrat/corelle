import {Component, useContext} from 'react'
import hyper from '@macrostrat/hyper'
import {Slider, HTMLSelect, FormGroup, Switch} from '@blueprintjs/core'
import {RotationsContext} from './rotations'
import styles from './main.styl'
import T from 'prop-types'
import FPSStats from "react-fps-stats"
import {MapSettingsContext} from './map-settings'

h = hyper.styled(styles)

SelectModel = (props)->
  {model} = useContext(RotationsContext)
  {setModel, models} = props
  onChange = (e)->
    setModel(e.currentTarget.value)
  h FormGroup, {label: 'Model'}, [
    h HTMLSelect, {onChange}, models.map (d)->
      selected = d == model
      h 'option', {value: d, selected}, d
  ]

MapSettingsPanel = (props)->
  {keepNorthUp, updateState} = useContext MapSettingsContext

  h Switch, {
    label: "Keep north up",
    checked: keepNorthUp,
    onChange: -> updateState {$toggle: ['keepNorthUp']}
  }


ControlPanel = (props)->
  {setTime, setModel, models} = props
  {time, model} = useContext RotationsContext
  {keepNorthUp} =
  max = 500
  h 'div.control-panel', [
    h 'h1', "Corelle Demo"
    h SelectModel, {setModel, models}
    h Slider, {
      min: 0,
      max,
      initialValue: 0
      labelStepSize: max/5
      labelRenderer: (val)->
        if val == max
          return null
        if val == 0
          return "now"
        "#{val} Ma"
      value: time,
      onChange: (v)->
        if setTime?
          setTime(v)
    }
    h MapSettingsPanel
    h FPSStats
    props.children
  ]

ControlPanel.propTypes = {
  setTime: T.func
  setModel: T.func
}

export default ControlPanel
