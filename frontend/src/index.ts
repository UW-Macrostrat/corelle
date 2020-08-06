import "@macrostrat/ui-components/init";
import { render } from "react-dom";
import h from "@macrostrat/hyper";
import App from "./app";

const div = document.createElement("div");
document.body.appendChild(div);
render(h(App), div);
