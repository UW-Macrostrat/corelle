import hyper from '@macrostrat/hyper'
import React, {Component, useContext} from 'react'
import {min} from 'd3-array'
import {select} from 'd3-selection'
import {geoStereographic} from 'd3-geo'
import {ComposableMap, ZoomableGroup, Geographies, Geography, Graticule} from 'react-simple-maps'
import {ResizeSensor} from '@blueprintjs/core'
import {RotationsContext} from './rotations'
import styles from './main.styl'

h = hyper.styled(styles)

class WorldMap extends Component
  constructor: ->
    super arguments...
    @state = {
      width: 1100,
      height: 800
    }

  onResize: (entries)=>
    {width, height} = entries[0].contentRect
    @setState {width, height}

  render: ->
    {width, height} = @state
    h ResizeSensor, {onResize: @onResize}, (
      h 'div.world-map', null, (
        h WorldMapInner, {width, height}
      )
    )

PlatePolygon = (props)->
  {geography, projection} = props
  {rotatedProjection} = useContext(RotationsContext) or {}
  {id} = geography
  if not rotatedProjection?
    return null
  projection = rotatedProjection(id, projection)
  if not projection?
    return null
  h Geography, {key: id, geography, projection, className: 'plate-polygon'}


class WorldMapInner extends Component
  @contextType: RotationsContext
  projection: (width, height, config)->
    return geoStereographic()
      .center([0,0])
      .scale(config.scale)
      #.clipExtent(config.clipExtent)

  render: ->
    {width, height} = @props
    {model} = @context
    <ComposableMap
      projection={this.projection}
      projectionConfig={{
        scale: 600,
        clipExtent: [[0,0],[width, height]]
      }}
      width={width}
      height={height}
      style={{
        width: "100%",
        height: "auto",
      }}
      >
      <ZoomableGroup center={[0,0]} style={{cursor: "move"}}>
        <Graticule />{
        h Geographies, {geography: "/api/plates?model=#{model}"}, (geographies, projection)=>
          geographies.map (geography, i)=>
            h PlatePolygon, {key: i, geography, projection}
      }</ZoomableGroup>
    </ComposableMap>


export {WorldMap}
