import React, {Component, createContext, useContext} from 'react'
import {StatefulComponent} from '@macrostrat/ui-components'
import T from 'prop-types'
import h from './hyper'
import {MapContext} from './context'
import {geoStereographic, geoGraticule, geoPath} from 'd3-geo'

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

  render: ->
    {width, height} = @props
    projection = geoStereographic()
      .center([0,0])
      .scale(width)

    renderPath = geoPath(projection)

    h MapContext.Provider, {value: {projection, renderPath}}, [
      h 'svg.globe', {width, height}, [
        h Background, {fill: 'dodgerblue'}
        h Graticule
      ]
    ]


export {Globe}
