import React, { Component } from "react"
import { geoOrthographic } from "d3-geo"
import { timer } from "d3"

import {
  ComposableMap,
  ZoomableGroup,
  Geographies,
  Geography,
} from "react-simple-maps"

class Globe extends Component {
  constructor() {
    super()
    this.state = {
      rotation: [0,0,0],
    }
    this.projection = this.projection.bind(this)
    this.startAnimation = this.startAnimation.bind(this)
  }
  projection() {
    return geoOrthographic()
      .translate([ 800 / 2, 800 / 2 ])
      .rotate(this.state.rotation)
      .scale(200)
      .clipAngle(90)
      .precision(.1)
  }
  startAnimation() {
    const rotation = [this.state.rotation[0] + 0.18, this.state.rotation[1] - 0.06, 0]
    this.setState({ rotation })
  }
  componentDidMount() {
    this.autorotation = timer(this.startAnimation)
  }
  render() {
    return (
      <ComposableMap width={800} height={800} projection={this.projection}>
        <ZoomableGroup>
          <Geographies
            geography={"/api/plates"}
            disableOptimization
            >
            {(geos, proj) =>
              geos.map((geo, i) =>
                <Geography
                  key={`${geo.properties.ISO_A3}-${i}`}
                  geography={geo}
                  projection={proj}
                  round
                />
              )
            }
          </Geographies>
        </ZoomableGroup>
      </ComposableMap>
    )
  }
}

export default Globe
