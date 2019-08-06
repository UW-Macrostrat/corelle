import React, {Component, createContext, useContext, createRef} from 'react'
import {StatefulComponent} from '@macrostrat/ui-components'
import T from 'prop-types'
import h from './hyper'
import {MapContext} from './context'
import {DraggableOverlay} from './drag-interaction'
import {max} from 'd3-array'
import {geoStereographic, geoOrthographic, geoGraticule, geoPath} from 'd3-geo'

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
  {renderPath} = useContext(MapContext)
  graticule = geoGraticule()
    .step [10,10]
    .extent [
        [-180,-80]
        [180,80 + 1e-6]
      ]
  console.log "Rendering"
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
    maxSize = max [@props.width, @props.height]

    projection = geoOrthographic()
      .center([0,0])
      .scale(maxSize/2)
      .translate([@props.width/2, @props.height/2])

    @state = {
      projection
    }

  updateProjection: (newProj)=>
    @updateState {projection: {$set: newProj}}

  dispatchEvent: (evt)=>
    # Simulate an event directly on the map's DOM element
    @mapElement.dispatchEvent(evt)

  contextValue: ->
    {width, height} = @props
    {projection} = @state
    actions = do => {updateProjection, dispatchEvent} = @
    renderPath = geoPath(projection)
    {projection, renderPath, width, height, actions...}

  render: ->
    {width, height, children} = @props
    h MapContext.Provider, {value: @contextValue()}, [
      h 'svg.globe', {width, height}, [
        h 'g.map', {ref: @mapElement}, [
          h Background, {fill: 'dodgerblue'}
          h Graticule
          h DraggableOverlay
          children
        ]
      ]
    ]


export {Globe, MapContext}
