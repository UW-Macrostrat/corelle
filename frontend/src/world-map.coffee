import hyper from '@macrostrat/hyper'
import React, {Component, useContext, createElement} from 'react'
import {APIResultView} from '@macrostrat/ui-components'
import {min} from 'd3-array'
import {select} from 'd3-selection'
import {geoStereographic, geoTransform} from 'd3-geo'
import {ComposableMap, ZoomableGroup, Geographies, Geography, Graticule} from 'react-simple-maps'
import {ResizeSensor, Popover, Spinner} from '@blueprintjs/core'
import {RotationsContext} from './rotations'
import {Globe, MapContext} from './globe'
import {geoPath} from 'd3-geo'
import {MapCanvas} from './globe/canvas'
import {Path, Text} from 'react-konva'

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

PlateFeature = (props)->
  # An arbitrary feature tied to a plate
  {feature, youngLim, oldLim, plateId, rest...} = props
  # Filter out features that are too young
  {geographyRotator, time} = useContext(RotationsContext) or {}
  return null unless geographyRotator?
  return null if oldLim < time
  # Filter out features that are too old (unlikely given current models)
  return null if youngLim > time
  {projection} = useContext(MapContext)
  rotate = geographyRotator plateId

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
  d = proj feature
  console.log d
  h Path, {data: d, x: 0, y: 0, rest...}

PlatePolygon = (props)->
  # An arbitrary feature tied to a plate
  {feature, rest...} = props
  {id, properties} = feature
  {old_lim, young_lim} = properties
  h PlateFeature, {feature, oldLim: old_lim, youngLim: young_lim, plateId: id, rest...}

PlatePolygons = (props)->
  {model} = useContext(RotationsContext)
  console.log model
  h APIResultView, {
    route: "/api/plates",
    params: {model},
    placeholder: null
  }, (data)=>
    return null unless data?
    console.log data
    h MapCanvas, [
      h MapCanvas.Layer, null, data.map (feature, i)->
        h PlatePolygon, {key: i, feature}
    ]

PlateFeatureDataset = (props)->
  {name} = props
  {model} = useContext(RotationsContext)
  h APIResultView, {
    route: "/api/feature/#{name}",
    params: {model},
    placeholder: null
  }, (data)=>
    return null unless data?
    console.log data
    h MapCanvas, [
      h MapCanvas.Layer, {className: name}, data.map (feature, i)->
        {id, properties} = feature
        {plate_id, old_lim, young_lim} = properties
        h PlateFeature, {
          key: i,
          feature,
          plateId: plate_id,
          oldLim: old_lim,
          youngLim: young_lim
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
      h PlatePolygons
      h PlateFeatureDataset, {name: 'ne_110m_land'}
    ]


export {WorldMap}
