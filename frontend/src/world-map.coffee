import hyper from '@macrostrat/hyper'
import React, {Component, useContext} from 'react'
import {APIResultView} from '@macrostrat/ui-components'
import {min} from 'd3-array'
import {select} from 'd3-selection'
import {geoStereographic, geoTransform} from 'd3-geo'
import {ComposableMap, ZoomableGroup, Geographies, Geography, Graticule} from 'react-simple-maps'
import {ResizeSensor, Popover, Spinner} from '@blueprintjs/core'
import {RotationsContext} from './rotations'
import {Globe, MapContext} from './globe'
import {geoPath} from 'd3-geo'

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
  {geography} = props
  {projection} = useContext(MapContext)
  {geographyRotator} = useContext(RotationsContext) or {}
  {id} = geography
  if not geographyRotator?
    return null
  rotate = geographyRotator id

  trans = geoTransform {
    point: (lon,lat)->
      [x,y] = rotate [lon,lat]
      this.stream.point(x,y)
  }

  stream = (s)->
    # This ordering makes no sense but whatever
    # https://stackoverflow.com/questions/27557724/what-is-the-proper-way-to-use-d3s-projection-stream
    trans.stream(projection.stream(s))

  # Combined projection
  proj = geoPath({stream})
  d = proj geography

  h Popover, {content: h("span","Plate #{id}"), targetTagName: 'g', wrapperTagName: 'g'}, [
    h 'path.plate-polygon', {
      key: id, d
    }
  ]


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
    h Globe, {
      projection: this.projection,
      width,
      height
    }, [
      h APIResultView, {
        route: "/api/plates",
        params: {model},
        placeholder: ->h(Spinner, {tagName: 'g'})
      }, (data)=>
        h 'g.plates', data.map (d, i)->
          h PlatePolygon, {key: i, geography: d}
    ]


export {WorldMap}
