import { useState, useContext, useEffect, useCallback } from "react";
import { WorldMap } from "./world-map";
import ControlPanel from "./control-panel";
import h from "@macrostrat/hyper";
import { RotationsProvider } from "../corelle-client/src/components";
import { MapSettingsProvider } from "./map-settings";
import { Spinner } from "@blueprintjs/core";
import {
  APIProvider,
  APIContext,
  useAPIResult,
  setQueryString,
  getQueryString,
} from "@macrostrat/ui-components";

const qs = getQueryString();

const initialState = {
  time: qs?.time ?? 0,
  model: qs?.model ?? "Seton2012",
  features: qs?.features ?? "ne_110m_land",
};
function App(props) {
  const [state, setState] = useState(initialState);

  useEffect(() => {
    setQueryString(state);
  }, [state]);

  const setTime = useCallback(
    (time) => setState({ ...state, time }),
    [setState]
  );
  const setModel = useCallback(
    (model) => setState({ ...state, model }),
    [setState]
  );

  const { baseURL } = useContext(APIContext);
  const models = useAPIResult<string[]>("/model", null, (data: any) =>
    data.map((d) => d.name)
  );
  const featureDatasets = useAPIResult<string[]>("/feature");

  if (models == null || featureDatasets == null) {
    return h(Spinner);
  }

  const { time, model, features } = state;

  return h("div", [
    h(RotationsProvider, { model, time, endpoint: baseURL, debounce: 1000 }, [
      h(WorldMap, { featureDataset: features }),
      h(ControlPanel, {
        setTime,
        setModel,
        featureDataset: features,
        featureDatasets,
        setFeatureDataset: (v) => setState({ ...state, features: v }),
        models,
      }),
    ]),
  ]);
}

const WrappedApp = ({ baseURL, ...props }) =>
  h(APIProvider, { baseURL }, h(MapSettingsProvider, null, h(App, props)));

export default WrappedApp;
