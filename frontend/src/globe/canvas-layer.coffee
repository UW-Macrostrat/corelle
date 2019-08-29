import {Component, createContext, useContext, createRef, createElement} from 'react'
import {findDOMNode} from 'react-dom'
import T from 'prop-types'
import h from './hyper'
import {MapContext} from './context'
import {geoPath} from 'd3-geo'
import {memoize} from 'underscore'

# https://philna.sh/blog/2018/09/27/techniques-for-animating-on-the-canvas-in-react/

MapCanvasContext = createContext {context: null, inCanvas: false}

class CanvasLayer extends Component
  @contextType: MapContext
  constructor: ->
    super arguments...
    @canvas = createRef()

  render: ->
    # https://medium.com/dev-shack/clicking-and-dragging-svg-with-react-and-d3-js-5639cd0c3c3b
    {width, height} = @context
    {children, style} = @props

    context = null
    {current: el} = @canvas
    if el?
      context = el.getContext("2d")

    value = {context, inCanvas: true}

    dpr = window.devicePixelRatio or 1
    if context?
      style ?= {}
      {fill, stroke, strokeWidth} = style
      fill ?= "rgba(200,200,200,0.5)"
      stroke ?= "#444"
      context.lineWidth = strokeWidth or 1
      context.strokeStyle = stroke
      context.fillStyle = fill
      context.setTransform(dpr, 0, 0, dpr, 0, 0)
      context.beginPath()

    style = {width, height}

    # hack for safari to display div
    xmlns = "http://www.w3.org/1999/xhtml"
    h MapCanvasContext.Provider, {value}, (
      createElement 'foreignObject', {width, height}, [
        createElement 'canvas', {
          xmlns,
          width: width*dpr,
          height: height*dpr,
          style,
          ref: @canvas
        }
        children
      ]
    )

  componentDidMount: ->
    {projection} = @context
    {feature, fill, stroke} = @props
    dpr = window.devicePixelRatio or 1
    el = @canvas.current
    ctx = el.getContext("2d")
    ctx.lineJoin = "round"
    ctx.lineCap = "round"

  componentDidUpdate: =>
    {current: el} = @canvas
    return if not el?
    context = el.getContext("2d")
    context.fill()
    context.stroke()

export {CanvasLayer, MapCanvasContext}
