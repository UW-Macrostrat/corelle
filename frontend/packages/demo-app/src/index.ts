import "core-js/stable";
import "regenerator-runtime/runtime";
import { FocusStyleManager } from "@blueprintjs/core";
import "@blueprintjs/core/lib/css/blueprint.css";

FocusStyleManager.onlyShowFocusOnTabs();
import { createRoot } from "react-dom/client";
import h from "@macrostrat/hyper";
import App from "./app";

let baseURL = import.meta.env.VITE_CORELLE_API_URL ?? "https://rotate.macrostrat.org/api";

const div = document.getElementById("root")

const root = createRoot(div);

root.render(h(App, { baseURL }));
