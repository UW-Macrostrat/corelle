import {Component} from 'react'
import hyper from '@macrostrat/hyper'
import {Slider} from '@blueprintjs/core'
import styles from './main.styl'
import T from 'prop-types'

h = hyper.styled(styles)

ControlPanel = (props)->
  {time, setTime} = props
  h 'div.control-panel', [
    h 'h1', "Corelle"
    h Slider, {
      min: 0,
      max: 500,
      initialValue: 0
      labelStepSize: 100
      labelRenderer: (val)->
        if val == 500
          return null
        if val == 0
          return "now"
        "#{val} Ma"
      value: time,
      onChange: setTime or ->
    }
    props.children
  ]

ControlPanel.propTypes = {
  time: T.number.isRequired
  setTime: T.func
}

export default ControlPanel
