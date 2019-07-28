import {Component, createContext} from 'react'
import h from 'react-hyperscript'
import {APIResultView, APIContext} from '@macrostrat/ui-components'
import T from 'prop-types'
import Quaternion from 'quaternion'

# Drag to rotate globe
# http://bl.ocks.org/ivyywang/7c94cb5a3accd9913263
# https://stackoverflow.com/questions/16964993/compose-two-rotations-in-d3-geo-projection
# https://www.jasondavies.com/maps/rotate/

RotationsContext = createContext {rotations: null}

# Should replace with inbuilt quaternion function
to_degrees = 180 / Math.PI
quat2euler = (q)->
  {w,x,y,z} = q
  return [
    Math.atan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y)) * to_degrees,
    Math.asin(Math.max(-1, Math.min(1, 2 * (w * y - z * x)))) * to_degrees,
    Math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z)) * to_degrees
  ]

class __RotationsProvider extends Component
  @propTypes: {
    time: T.number.isRequired
    model: T.string.isRequired
    rotations: T.arrayOf(T.object)
  }
  render: ->
    {rotations, time, model} = @props
    value = {
      rotations,
      model,
      time,
      plateRotation: @plateRotation
      rotatedProjection: @rotatedProjection
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

  rotatedProjection: (id, projection)=>
    {time} = @props
    if time == 0
      return projection
    q = @plateRotation(id)
    if not q?
      return null
    angles = quat2euler(q)
    return projection.rotate(angles)

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
