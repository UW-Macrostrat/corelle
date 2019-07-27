import hyper from '@macrostrat/hyper'
import React, {Component} from 'react'
import {min} from 'd3-array'
import {select} from 'd3-selection'
import {geoNaturalEarth1} from 'd3-geo'
import {ComposableMap, ZoomableGroup, Geographies, Geography, Graticule} from 'react-simple-maps'
import {ResizeSensor} from '@blueprintjs/core'
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

class WorldMapInner extends Component
  projection: (width, height, config)->
    return geoNaturalEarth1()
      .rotate([-10,-52,0])
      .scale(config.scale)
      .clipExtent(config.extent)

  render: ->
    {width, height} = @props
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
      <ZoomableGroup center={[10,52]} style={{cursor: "move"}}>
        <Graticule />
        <Geographies geography="/api/plates">
          {(geographies, projection) => geographies.map (geography, i)=>
            <Geography
              key={i}
              geography={geography}
              projection={projection}
              style={{
                default: {
                  fill: "#ECEFF1",
                  stroke: "#607D8B",
                  strokeWidth: 0.75,
                  outline: "none",
                },
                hover: {
                  fill: "#607D8B",
                  stroke: "#607D8B",
                  strokeWidth: 0.75,
                  outline: "none",
                },
                pressed: {
                  fill: "#FF5722",
                  stroke: "#607D8B",
                  strokeWidth: 0.75,
                  outline: "none",
                },
              }}
            />
          }
        </Geographies>
      </ZoomableGroup>
    </ComposableMap>


export {WorldMap}
