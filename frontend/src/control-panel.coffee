import {Component, useContext} from 'react'
import hyper from '@macrostrat/hyper'
import {Slider, HTMLSelect, FormGroup} from '@blueprintjs/core'
import {RotationsContext} from './rotations'
import styles from './main.styl'
import T from 'prop-types'

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

ControlPanel = (props)->
  {setTime, setModel, models} = props
  {time, model} = useContext RotationsContext
  max = 500
  h 'div.control-panel', [
    h 'h1', "Corelle"
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
    props.children
  ]

ControlPanel.propTypes = {
  setTime: T.func
  setModel: T.func
}

export default ControlPanel
