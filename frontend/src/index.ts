import "@macrostrat/ui-components/init";
import { render } from "react-dom";
import h from "@macrostrat/hyper";
import App from "./app";

let baseURL = process.env.CORELLE_API_BASE_URL || "https://rotate.macrostrat.org/api";

const div = document.createElement("div");
document.body.appendChild(div);
render(h(App, { baseURL }), div);
