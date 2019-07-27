import {Component, createContext} from 'react'
import h from 'react-hyperscript'
import {APIResultView, APIContext} from '@macrostrat/ui-components'
import T from 'prop-types'

RotationsContext = createContext {rotations: null}

class __RotationsProvider extends Component
  @propTypes: {
    time: T.number.isRequired
    rotations: T.arrayOf(T.object)
  }
  render: ->
    {rotations, time} = @props
    h RotationsContext.Provider, {rotations, time}, @props.children

RotationsProvider = (props)->
  {time, children} = props
  h APIResultView, {
    route: "/api/rotate",
    params: {time, quaternion: true}
    placeholder: null
    minInterval: 1000
  }, (data)=>
    h __RotationsProvider, {time, rotations: data}, children

RotationsProvider.propTypes = __RotationsProvider.propTypes

export {RotationsProvider, RotationsContext}
