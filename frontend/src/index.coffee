import {render} from 'react-dom'
import h from '@macrostrat/hyper'

import Globe from './globe'

div = document.createElement("div")
document.body.appendChild(div)
render(h(Globe), div)
