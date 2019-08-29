import {Component, useContext} from 'react'
import hyper from '@macrostrat/hyper'
import {Slider, HTMLSelect, FormGroup, Switch, Alignment, NumericInput} from '@blueprintjs/core'
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
  h FormGroup, {label: 'Model', inline: true}, [
    h HTMLSelect, {onChange}, models.map (d)->
      selected = d == model
      h 'option', {value: d, selected}, d
  ]

SelectProjection = (props)->
  {projection, projections, updateState} = useContext(MapSettingsContext)
  {setModel, models} = props
  onChange = (e)->
    lbl = e.currentTarget.value
    p = projections.find (d)->d.id == lbl
    updateState {projection: {$set: p}}
  h FormGroup, {label: 'Projection', inline: true}, [
    h HTMLSelect, {onChange}, projections.map (d)->
      selected = d.func == projection
      h 'option', {value: d.id, selected}, d.id
  ]

MapSettingsPanel = (props)->
  {keepNorthUp, updateState} = useContext MapSettingsContext

  h 'div', [
    h SelectProjection
    h Switch, {
      label: "Keep north up",
      checked: keepNorthUp,
      onChange: -> updateState {$toggle: ['keepNorthUp']}
      alignIndicator: Alignment.RIGHT
    }
  ]

ControlPanel = (props)->
  {setTime, setModel, models} = props
  {time, model} = useContext RotationsContext
  {keepNorthUp} =
  max = 1200
  h 'div.control-panel', [
    h 'h1', "Corelle"
    h SelectModel, {setModel, models}
    h FormGroup, {
      label: 'Reconstruction time'
    }, [
      h NumericInput, {
        min: 0
        max
        className: 'time-input'
        clampValueOnBlur: true
        fill: true
        large: true
        value: time
        rightElement: h 'div.unit-label', 'Ma'
        onValueChange: (v)->
          if setTime?
            setTime(v)
      }
    ]
    h MapSettingsPanel
    h FPSStats
    props.children
  ]

ControlPanel.propTypes = {
  setTime: T.func
  setModel: T.func
}

export default ControlPanel
