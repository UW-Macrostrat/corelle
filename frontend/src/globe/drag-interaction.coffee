import {Component, createContext, useContext} from 'react'
import {findDOMNode} from 'react-dom'
import T from 'prop-types'
import h from './hyper'
import {MapContext} from './context'
import {drag} from 'd3-drag'
import {select, event as currentEvent, mouse} from 'd3-selection'
import {sph2cart, quat2euler, euler2quat, quatMultiply, quaternion} from './math'
import Q from 'quaternion'

###
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
###

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
    {projection} = @context
    @setState {mousePosition: {type: "Point", coordinates: pos}}
    @p0 = sph2cart(pos)
    @q0 = euler2quat(projection.rotate())

  dragged: (currentPos)=>
    {projection, updateProjection} = @context
    p1 = sph2cart(currentPos)
    q1 = quaternion(@p0, p1)
    res = quatMultiply( @q0, q1 )
    r1 = quat2euler(res)
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
