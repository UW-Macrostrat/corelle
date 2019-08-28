import {Component, createContext, useContext} from 'react'
import {findDOMNode} from 'react-dom'
import T from 'prop-types'
import h from './hyper'
import {MapContext} from './context'
import {drag} from 'd3-drag'
import {select, event as currentEvent, mouse} from 'd3-selection'
import {sph2cart, quat2euler, euler2quat, quatMultiply, quaternion} from './math'

class DraggableOverlay extends Component
  @contextType: MapContext
  @propTypes: {
    showMousePosition: T.bool
    keepNorthUp: T.bool
  }
  @defaultProps: {
    showMousePosition: true
    pinNorthUp: false
  }
  constructor: ->
    super arguments...
    @state = {mousePosition: null}
  render: ->
    # https://medium.com/dev-shack/clicking-and-dragging-svg-with-react-and-d3-js-5639cd0c3c3b
    {width, height, renderPath} = @context
    {showMousePosition} = @props
    {mousePosition} = @state
    h 'g.drag-overlay', [
      h 'rect.drag-mouse-target', {width, height}
      h.if(mousePosition? and showMousePosition) 'path.mouse-position', {
        d: renderPath(mousePosition)
      }
    ]

  dragStarted: (pos)=>
    {projection} = @context
    @setState {mousePosition: {type: "Point", coordinates: pos}}
    @p0 = sph2cart(pos)
    @q0 = euler2quat(projection.rotate())

  dragged: (currentPos)=>
    {keepNorthUp} = @props
    {projection, updateProjection} = @context
    @q0 = euler2quat(projection.rotate())
    p1 = sph2cart(currentPos)
    q1 = quaternion(@p0, p1)
    res = quatMultiply( @q0, q1 )
    r1 = quat2euler(res)
    if keepNorthUp
      r1 = [r1[0], r1[1], 0]
    return unless r1?
    updateProjection(projection.rotate(r1))

  dragEnded: (pos)=>
    @setState {mousePosition: null}

  componentDidMount: ->
    {width, height, projection, dispatchEvent} = @context
    mousePos = (func)-> ->
      pos = projection.invert(mouse(@))
      func(pos)

    el = select(findDOMNode(@))
    @drag = drag()
      .clickDistance 2
      .on "start", mousePos(@dragStarted)
      .on "drag", mousePos(@dragged)
      .on "end", mousePos(@dragEnded)
    @drag(el)
    el.on 'click', ->
      dispatchEvent currentEvent

export {DraggableOverlay}
