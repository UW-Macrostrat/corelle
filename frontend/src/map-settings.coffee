import {Component, createContext} from 'react'
import {StatefulComponent} from '@macrostrat/ui-components'
import h from '@macrostrat/hyper'

MapSettingsContext = createContext {}

class MapSettingsProvider extends StatefulComponent
  constructor: ->
    super arguments...
    @state = {
      keepNorthUp: true
    }
  render: ->
    value = {@state..., updateState: @updateState}
    h MapSettingsContext.Provider, {value}, @props.children


export {MapSettingsProvider, MapSettingsContext}
