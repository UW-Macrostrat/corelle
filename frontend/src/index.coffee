import "@macrostrat/ui-components/init"
import {render} from 'react-dom'
import h from '@macrostrat/hyper'
import App from './app'

div = document.createElement("div")
document.body.appendChild(div)
render(h(App), div)
