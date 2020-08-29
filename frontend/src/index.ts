import "@macrostrat/ui-components/init";
import { render } from "react-dom";
import h from "@macrostrat/hyper";
import App from "./app";

let baseURL = process.env.PUBLIC_URL || "";
baseURL += "/api";

const div = document.createElement("div");
document.body.appendChild(div);
render(h(App, { baseURL }), div);
