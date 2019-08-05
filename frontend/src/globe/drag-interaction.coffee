import {Component, createContext, useContext} from 'react'
import {findDOMNode} from 'react-dom'
import T from 'prop-types'
import h from './hyper'
import {MapContext} from './context'
import {drag} from 'd3-drag'
import {select, event as currentEvent, mouse} from 'd3-selection'
#import {sph2cart} from '../math'
import Q from 'quaternion'

to_degrees = 180 / Math.PI
to_radians = Math.PI / 180

sph2cart = ( coord )->
	lon = coord[0] * to_radians
	lat = coord[1] * to_radians
	x = Math.cos(lat) * Math.cos(lon)
	y = Math.cos(lat) * Math.sin(lon)
	z = Math.sin(lat)
	return [x, y, z]

euler2quat = (e)->
  # Euler to quaternion function with Euler angles as
  # yaw, pitch, and roll.
  roll = .5 * e[0] * to_radians
  pitch = .5 * e[1] * to_radians
  yaw = .5 * e[2] * to_radians

  sr = Math.sin(roll)
  cr = Math.cos(roll)
  sp = Math.sin(pitch)
  cp = Math.cos(pitch)
  sy = Math.sin(yaw)
  cy = Math.cos(yaw)

  qi = sr*cp*cy - cr*sp*sy
  qj = cr*sp*cy + sr*cp*sy
  qk = cr*cp*sy - sr*sp*cy
  qr = cr*cp*cy + sr*sp*sy

  return [qr, qi, qj, qk]

quat2euler = (t)->
  [ Math.atan2(2 * (t[0] * t[1] + t[2] * t[3]), 1 - 2 * (t[1] * t[1] + t[2] * t[2])) * to_degrees,
    Math.asin(Math.max(-1, Math.min(1, 2 * (t[0] * t[2] - t[3] * t[1])))) * to_degrees,
    Math.atan2(2 * (t[0] * t[3] + t[1] * t[2]), 1 - 2 * (t[2] * t[2] + t[3] * t[3])) * to_degrees ]

quatMultiply = (q1, q2)->
  a = q1[0]
  b = q1[1]
  c = q1[2]
  d = q1[3]
  e = q2[0]
  f = q2[1]
  g = q2[2]
  _h = q2[3]
  return [
    a*e - b*f - c*g - d*_h,
    b*e + a*f + c*_h - d*g,
    a*g - b*_h + c*e + d*f,
    a*_h + b*g - c*f + d*e]

class DraggableOverlay extends Component
  @contextType: MapContext
  constructor: ->
    super arguments...
    @state = {mousePosition: null}
  render: ->
    {width, height, renderPath} = @context
    {mousePosition} = @state
    h 'g.drag-overlay', [
      h 'rect.drag-mouse-target', {width, height}
      h.if(mousePosition?) 'path.mouse-position', {
        d: renderPath(mousePosition)
      }
    ]

  dragStarted: (pos)=>
    @setState {mousePosition: {type: "Point", coordinates: pos}}
    @startPosition = sph2cart(pos)

  dragged: (currentPos)=>
    {projection, updateProjection} = @context
    r0 = projection.rotate()

    q0 = euler2quat(r0)
    v1 = sph2cart(currentPos)
    q1 = Q.fromBetweenVectors(@startPosition,v1).toVector()
    t = quatMultiply(q0, q1)
    r1 = quat2euler(t)
    console.log r0, r1
    updateProjection(projection.rotate(r1))

  dragEnded: (pos)=>
    @setState {mousePosition: null}
    console.log currentEvent

  componentDidMount: ->
    {width, height, projection} = @context
    mousePos = (func)-> ->
      pos = projection.invert(mouse(@))
      func(pos)

    el = select(findDOMNode(@))
    @drag = drag()
      .on "start", mousePos(@dragStarted)
      .on "drag", mousePos(@dragged)
      .on "end", mousePos(@dragEnded)

    @drag(el)

export {DraggableOverlay}
