import { Stage, Layer, Path } from 'react-konva'
import h from 'react-hyperscript'
import {createElement} from 'react'
import {MapContext} from './context'
import {useContext} from 'react'
import styles from './module.styl'
import Konva from 'konva'

MapCanvas = (props)->
  {width, height} = useContext(MapContext)
  h Stage, {width, height, className: styles['map-layer'], props...}

MapCanvas.Layer = (props)->
  createElement Layer, props

MapCanvas.Path = (props)->
  {geometry, rest...} = props
  data = null
  if geometry?
    {renderPath} = useContext(MapContext)
    data = renderPath geometry
  h Path, {data, rest...}

export {MapCanvas}
