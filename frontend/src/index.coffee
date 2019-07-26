import {render} from 'react-dom'
import h from '@macrostrat/hyper'

import {WorldMap} from './world-map'

div = document.createElement("div")
document.body.appendChild(div)
render(h(WorldMap), div)
