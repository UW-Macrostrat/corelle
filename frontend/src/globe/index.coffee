import React, {Component, createContext, useContext} from 'react'
import {StatefulComponent} from '@macrostrat/ui-components'
import T from 'prop-types'
import h from './hyper'
import {MapContext} from './context'
import {DraggableOverlay} from './drag-interaction'
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

    projection = geoStereographic()
      .center([0,0])
      .scale(@props.width/2)

    @state = {
      projection
    }

  updateProjection: (newProj)=>
    console.log "Updating projection"
    console.log(newProj == @state.projection)
    #v = Object.assign({}, newProj)
    @updateState {projection: {$set: newProj}}

  contextValue: ->
    {width, height} = @props
    {projection} = @state
    {updateProjection} = @
    renderPath = geoPath(projection)
    {projection, renderPath, width, height, updateProjection}

  render: ->
    {width, height, children} = @props
    h MapContext.Provider, {value: @contextValue()}, [
      h 'svg.globe', {width, height}, [
        h Background, {fill: 'dodgerblue'}
        h Graticule
        children
        h DraggableOverlay
      ]
    ]


export {Globe, MapContext}
