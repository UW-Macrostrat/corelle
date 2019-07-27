import {WorldMap} from './world-map'
import hyper from '@macrostrat/hyper'
import {Slider} from '@blueprintjs/core'
import styles from './main.styl'

h = hyper.styled(styles)

ControlPanel = ->
  h 'div.control-panel', [
    h 'h1', "Corelle"
    h Slider, {min: 0, max: 2000}
  ]

App = ->
  h 'div', [
    h WorldMap
    h ControlPanel
  ]

export default App
