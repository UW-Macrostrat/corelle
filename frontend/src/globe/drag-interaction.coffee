import {Component, createContext, useContext} from 'react'
import {findDOMNode} from 'react-dom'
import T from 'prop-types'
import h from './hyper'
import {MapContext} from './context'
import {drag} from 'd3-drag'
import {select, event as currentEvent} from 'd3-selection'

class DraggableOverlay extends Component
  @contextType: MapContext
  render: ->
    {width, height} = @context
    h 'rect.drag-overlay', {width, height}

  dragStarted: =>
    console.log "Started"
    console.log currentEvent

  dragged: =>
    console.log currentEvent

  dragEnded: =>
    console.log currentEvent

  componentDidMount: ->
    {width, height} = @context
    el = select(findDOMNode(@))
    @drag = drag()
      .on("start", @dragStarted)
      .on("drag", @dragged)
      .on("end", @dragEnded)

    @drag(el)

export {DraggableOverlay}
