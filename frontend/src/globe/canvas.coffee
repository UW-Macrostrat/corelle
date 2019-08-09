import { Stage, Layer, Path } from 'react-konva'
import h from 'react-hyperscript'
import {createElement} from 'react'
import {MapContext} from './context'
import {useContext} from 'react'
import styles from './module.styl'
import Konva from 'konva'

MapCanvas = (props)->
  {children, rest...} = props
  value = useContext(MapContext)
  {width, height} = value
  h Stage, {width, height, className: styles['map-layer'], rest...}, (
     h MapContext.Provider, {value}, children
  )

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
