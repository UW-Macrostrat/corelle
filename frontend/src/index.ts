import "core-js/stable";
import "regenerator-runtime/runtime";
import { FocusStyleManager } from "@blueprintjs/core";
import "@blueprintjs/core/lib/css/blueprint.css";
import "@macrostrat/ui-components/lib/esm/index.css";

FocusStyleManager.onlyShowFocusOnTabs();
import { render } from "react-dom";
import h from "@macrostrat/hyper";
import App from "./app";

let baseURL = process.env.CORELLE_API_BASE_URL || "https://rotate.macrostrat.org/api";

const div = document.createElement("div");
document.body.appendChild(div);
render(h(App, { baseURL }), div);
