import {Component, createContext, useContext} from 'react'
import {findDOMNode} from 'react-dom'
import T from 'prop-types'
import h from './hyper'
import {MapContext} from './context'
import {drag} from 'd3-drag'
import {select, event as currentEvent, mouse} from 'd3-selection'

class DraggableOverlay extends Component
  @contextType: MapContext
  render: ->
    {width, height} = @context
    h 'rect.drag-overlay', {width, height}

  dragStarted: (pos)=>
    console.log "Started"
    console.log currentEvent
    @startPosition = pos

  dragged: (pos)=>
    console.log currentEvent
    currentPosition = pos

  dragEnded: (pos)=>
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
