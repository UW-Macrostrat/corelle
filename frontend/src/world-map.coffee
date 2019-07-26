import h from '@macrostrat/hyper'
import React, {Component} from 'react'
import {min} from 'd3-array'
import {select} from 'd3-selection'
import {geoAzimuthalEqualArea} from 'd3-geo'
import {ComposableMap, ZoomableGroup, Geographies, Geography, Graticule} from 'react-simple-maps'

class WorldMap extends Component
  projection: (width, height, config)->
    return geoAzimuthalEqualArea()
      .rotate([-10,-52,0])
      .scale(config.scale)

  render: ()->
    <div>
      <ComposableMap
        projection={this.projection}
        projectionConfig={{
          scale: 600,
        }}
        width={980}
        height={551}
        style={{
          width: "100%",
          height: "auto",
        }}
        >
        <ZoomableGroup center={[10,52]}>
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
          <Graticule />
        </ZoomableGroup>
      </ComposableMap>
    </div>


export {WorldMap}
