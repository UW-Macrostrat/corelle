import { useState, useContext } from "react";
import { WorldMap } from "./world-map";
import ControlPanel from "./control-panel";
import h from "@macrostrat/hyper";
import { RotationsProvider } from "@macrostrat/corelle-client";
import { MapSettingsProvider } from "./map-settings";
import { Spinner } from "@blueprintjs/core";
import {
  APIProvider,
  APIContext,
  useAPIResult,
} from "@macrostrat/ui-components";

function App(props) {
  const [state, setState] = useState({
    time: 0,
    model: "Seton2012",
    featureDataset: "ne_110m_land",
  });

  const { baseURL } = useContext(APIContext);
  const models = useAPIResult<string[]>("/model", null, (data: any) =>
    data.map((d) => d.name)
  );
  const featureDatasets = useAPIResult<string[]>("/feature");

  if (models == null || featureDatasets == null) {
    return h(Spinner);
  }

  const setTime = (time) => setState({ ...state, time });
  const setModel = (model) => setState({ ...state, model });

  const { time, model, featureDataset } = state;
  return h("div", [
    h(RotationsProvider, { model, time, endpoint: baseURL, debounce: 1000 }, [
      h(WorldMap, { featureDataset }),
      h(ControlPanel, {
        setTime,
        setModel,
        featureDataset,
        featureDatasets,
        setFeatureDataset: (v) => this.setState({ featureDataset: v }),
        models,
      }),
    ]),
  ]);
}

const WrappedApp = ({ baseURL, ...props }) =>
  h(APIProvider, { baseURL }, h(MapSettingsProvider, null, h(App, props)));

export default WrappedApp;
