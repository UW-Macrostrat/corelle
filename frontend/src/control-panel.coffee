import {Component} from 'react'
import hyper from '@macrostrat/hyper'
import {Slider} from '@blueprintjs/core'
import styles from './main.styl'
import T from 'prop-types'

h = hyper.styled(styles)

ControlPanel = (props)->
  {time, setTime} = props
  max = 500
  h 'div.control-panel', [
    h 'h1', "Corelle"  
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
  time: T.number.isRequired
  setTime: T.func
}

export default ControlPanel
