import {Component, createContext} from 'react'
import h from 'react-hyperscript'
import {APIResultView, APIContext} from '@macrostrat/ui-components'
import T from 'prop-types'
import Quaternion from 'quaternion'
import {geoRotation} from 'd3-geo'
import {quat2euler, sph2cart, cart2sph} from './math'

# Drag to rotate globe
# http://bl.ocks.org/ivyywang/7c94cb5a3accd9913263
# https://stackoverflow.com/questions/16964993/compose-two-rotations-in-d3-geo-projection
# https://www.jasondavies.com/maps/rotate/

RotationsContext = createContext {rotations: null}

class __RotationsProvider extends Component
  @propTypes: {
    time: T.number.isRequired
    model: T.string.isRequired
    rotations: T.arrayOf(T.object)
  }
  render: ->
    {rotations, time, model, models} = @props
    value = {
      rotations,
      model,
      time,
      plateRotation: @plateRotation
      rotatedProjection: @rotatedProjection
      geographyRotator: @geographyRotator
    }

    h RotationsContext.Provider, {
      value
    }, @props.children

  plateRotation: (id)=>
    {rotations} = @props
    rot = rotations.find (d)-> d.plate_id == id
    if not rot?
      return null
    q = Quaternion(rot.quaternion)
    return q

  geographyRotator: (id)=>
    {time} = @props
    identity = (arr)->arr
    if time == 0
      return identity
    q = @plateRotation(id)
    if not q?
      return identity
    #angles = quat2euler(q)
    return (point)->
      vec = sph2cart(point)
      v1 = q.rotateVector(vec)
      return cart2sph(v1)
    #return geoRotation(angles)

  rotatedProjection: (id, projection)=>
    {time} = @props
    if time == 0
      return projection
    q = @plateRotation(id)
    if not q?
      return null
    angles = quat2euler(q)
    #console.log angles
    return ->
      projection.apply @, arguments

RotationsProvider = (props)->
  {time, children, model} = props
  h APIResultView, {
    route: "/api/rotate",
    params: {time, model, quaternion: true}
    placeholder: null
    debounce: 1000
  }, (data)=>
    h __RotationsProvider, {time, model, rotations: data}, children

RotationsProvider.propTypes = __RotationsProvider.propTypes

export {RotationsProvider, RotationsContext}
