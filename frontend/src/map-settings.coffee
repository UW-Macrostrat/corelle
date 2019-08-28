import {Component, createContext} from 'react'
import {StatefulComponent} from '@macrostrat/ui-components'
import h from '@macrostrat/hyper'
import {geoOrthographic, geoStereographic, geoGnomonic, geoNaturalEarth1} from 'd3-geo'

projections = [
  {
    id: "Orthographic",
    func: geoOrthographic().precision(0.5).clipAngle(90)
  }
  {
    id: "Stereographic"
    func: geoStereographic().precision(0.5)
  }
  {
    id: "Gnomonic"
    func: geoGnomonic().precision(0.5)
  }
  {
    id: "Natural Earth"
    func: geoNaturalEarth1()
  }
]

MapSettingsContext = createContext {projections}

class MapSettingsProvider extends StatefulComponent
  constructor: ->
    super arguments...
    @state = {
      keepNorthUp: true
      projection: projections[0]
    }
  render: ->
    value = {@state..., projections, updateState: @updateState}
    h MapSettingsContext.Provider, {value}, @props.children

export {MapSettingsProvider, MapSettingsContext}
