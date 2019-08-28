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
    @state = {
      # The canvas rendering context
      context: null
    }

  render: ->
    # https://medium.com/dev-shack/clicking-and-dragging-svg-with-react-and-d3-js-5639cd0c3c3b
    {width, height} = @context
    {children, style} = @props
    {context} = @state
    value = {context, inCanvas: true}


    if context?
      style ?= {}
      {fill, stroke, strokeWidth} = style
      fill ?= "rgba(200,200,200,0.5)"
      stroke ?= "#444"
      context.lineWidth = strokeWidth or 1
      context.strokeStyle = stroke
      context.fillStyle = fill

    # hack for safari to display div
    xmlns = "http://www.w3.org/1999/xhtml"
    h MapCanvasContext.Provider, {value}, (
      createElement 'foreignObject', {width, height}, [
        createElement 'canvas', {xmlns, width, height, ref: @canvas}
        children
      ]
    )

  componentDidMount: ->
    {projection, registerCanvasContext} = @context
    {feature, fill, stroke} = @props
    el = @canvas.current
    ctx = el.getContext("2d")
    ctx.lineJoin = "round"
    ctx.lineCap = "round"
    registerCanvasContext(ctx)
    @setState {context: ctx}

  componentDidUpdate: =>
    {context} = @state
    return null if not context?
    context.fill()
    context.stroke()

  componentWillUnmount: =>
    {deregisterCanvasContext} = @context
    {context} = @state
    deregisterCanvasContext(context)

export {CanvasLayer, MapCanvasContext}
