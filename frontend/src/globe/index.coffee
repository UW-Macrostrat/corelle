import React, {Component, createContext, useContext, createRef} from 'react'
import {findDOMNode} from 'react-dom'
import {StatefulComponent} from '@macrostrat/ui-components'
import T from 'prop-types'
import h from './hyper'
import {MapContext} from './context'
import {DraggableOverlay} from './drag-interaction'
import {min, max} from 'd3-array'
import {geoStereographic, geoOrthographic, geoGraticule, geoPath} from 'd3-geo'
import styles from './module.styl'
import FPSStats from "react-fps-stats"

GeoPath = (props)->
  {geometry, rest...} = props
  d = null
  if geometry?
    {renderPath} = useContext(MapContext)
    d = renderPath geometry
  h 'path', {d, rest...}

class Background extends Component
  @contextType: MapContext
  render: ->
    h GeoPath, {
      geometry: {type: 'Sphere'},
      className: 'background',
      @props...
    }

Graticule = (props)->
  graticule = geoGraticule()
    .step [10,10]
    .extent [
        [-180,-80]
        [180,80 + 1e-6]
      ]
  h GeoPath, {
    className: 'graticule',
    geometry: graticule(),
    props...
  }

class Globe extends StatefulComponent
  @propTypes: {
    #projection: T.func.isRequired,
    width: T.number,
    height: T.number
  }

  constructor: (props)->
    super(props)

    @mapElement = createRef()

    projection = geoOrthographic()
      .center([0,0])
      .clipAngle(90)
      .precision(0.5)

    @state = {
      projection
      canvasContexts: new Set([])
    }

  componentDidUpdate: (prevProps)=>
    {width, height} = @props
    return if prevProps.width == width and prevProps.height == height
    {projection} = @state
    maxSize = min [width, height]
    console.log width, height
    newProj = projection.scale(maxSize/2)
      .translate([width/2, height/2])
    @updateProjection newProj

  updateProjection: (newProj)=>
    @updateState {projection: {$set: newProj}}

  componentWillUpdate: =>
    {canvasContexts} = @state
    {width, height} = @props
    canvasContexts.forEach (ctx)->
      ctx.clearRect(0, 0, width, height)
      ctx.beginPath()

  dispatchEvent: (evt)=>
    v = findDOMNode(@)
    el = v.getElementsByClassName(styles.map)[0]
    # Simulate an event directly on the map's DOM element
    {clientX, clientY} = evt

    e1 = new Event "mousedown", {clientX, clientY}
    e2 = new Event "mouseup", {clientX, clientY}

    el.dispatchEvent(e1)
    el.dispatchEvent(e2)

  registerCanvasContext: (ctx)=>
    console.log "Registering canvas context"
    ctx.beginPath()
    @updateState {canvasContexts: {$add: [ctx]}}
  deregisterCanvasContext: =>
    @updateState {canvasContexts: {$remove: [ctx]}}

  componentDidMount: =>
    @componentDidUpdate.call(@,arguments)

  render: ->
    {width, height, children, rest...} = @props

    {projection} = @state
    actions = do => {
      updateProjection,
      dispatchEvent,
      registerCanvasContext,
      deregisterCanvasContext
      } = @
    renderPath = geoPath(projection)
    value = {projection, renderPath, width, height, actions...}

    h MapContext.Provider, {value}, [
      h 'svg.globe', {width, height, rest...}, [
        h 'g.map', {ref: @mapElement}, [
          h Background, {fill: 'dodgerblue'}
          h Graticule
          children
        ]
        h DraggableOverlay
      ]
      h FPSStats
    ]


export {Globe, MapContext}
