import {Component, useContext} from 'react'
import hyper from '@macrostrat/hyper'
import {Slider, HTMLSelect, FormGroup, Switch, Alignment, NumericInput} from '@blueprintjs/core'
import {RotationsContext} from './rotations'
import styles from './main.styl'
import T from 'prop-types'
import {MapSettingsContext} from './map-settings'

h = hyper.styled(styles)

Select = (props)->
  {label, value, options, onChange} = props
  onChange ?= ->
  h FormGroup, {label, inline: true}, [
    h HTMLSelect, {
      onChange: (e)->onChange(e.currentTarget.value)
    }, options.map (d)->
      h 'option', {
        value: d
        selected: d == value
      }, d
  ]

SelectModel = (props)->
  {model: value} = useContext(RotationsContext)
  {setModel: onChange, models: options} = props
  h Select, {onChange, options, value, label: 'Model'}

SelectFeatureDataset = (props)->
  {
    setFeatureDataset: onChange,
    featureDataset: value,
    featureDatasets: options
  } = props
  h Select, {onChange, options, value, label: 'Features'}

SelectProjection = (props)->
  {
    projection,
    projections,
    updateState
  } = useContext(MapSettingsContext)
  options = projections.map (d)->d.id
  value = projection.id
  onChange = (value)->
    p = projections.find (d)->d.id == value
    updateState {projection: {$set: p}}
  h Select, {onChange, options, value, label: 'Projection'}

MapSettingsPanel = (props)->
  {keepNorthUp, updateState} = useContext MapSettingsContext
  h 'div', [
    h SelectProjection
    h Switch, {
      label: "Keep north up",
      checked: keepNorthUp,
      onChange: -> updateState {$toggle: ['keepNorthUp']}
      alignIndicator: Alignment.RIGHT
    }
  ]

ControlPanel = (props)->
  {setTime, setModel, models, featureDatasets, featureDataset, setFeatureDataset} = props
  {time, model} = useContext RotationsContext
  max = 1200
  h 'div.control-panel', [
    h 'div.header', [
      h 'h1', null, (
        h 'a', {href: "https://github/UW-Macrostrat/Corelle"}, "Corelle"
      )
      h 'p', "Simple plate rotations."
    ]
    h SelectModel, {setModel, models}
    h SelectFeatureDataset, {setFeatureDataset, featureDataset, featureDatasets}
    h FormGroup, {
      label: 'Reconstruction time'
    }, [
      h NumericInput, {
        min: 0
        max
        className: 'time-input'
        clampValueOnBlur: true
        fill: true
        large: true
        value: time
        rightElement: h 'div.unit-label', 'Ma'
        onValueChange: (v)->
          if setTime?
            setTime(v)
      }
    ]
    h MapSettingsPanel
    #h FPSStats
    props.children
    h 'p.credits', [
      h 'a', {href: 'https://davenquinn.com'}, "Daven Quinn"
      ", 2019"
    ]
  ]

ControlPanel.propTypes = {
  setTime: T.func
  setModel: T.func
}

export default ControlPanel
