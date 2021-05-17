/*
 * decaffeinate suggestions:
 * DS102: Remove unnecessary code created because of implicit returns
 * DS207: Consider shorter variations of null checks
 * Full docs: https://github.com/decaffeinate/decaffeinate/blob/master/docs/suggestions.md
 */
import { useContext } from "react";
import hyper from "@macrostrat/hyper";
import {
  HTMLSelect,
  FormGroup,
  Switch,
  Alignment,
  NumericInput,
} from "@blueprintjs/core";
import { RotationsContext } from "@macrostrat/corelle";
import * as styles from "./main.module.styl";
import { MapSettingsContext } from "./map-settings";

const h = hyper.styled(styles);

const Select = function (props) {
  let { label, value, options, onChange } = props;
  if (onChange == null) {
    onChange = function () {};
  }
  return h(FormGroup, { label, inline: true }, [
    h(
      HTMLSelect,
      {
        onChange(e) {
          return onChange(e.currentTarget.value);
        },
        value,
      },
      options.map((d) =>
        h(
          "option",
          {
            value: d,
          },
          d
        )
      )
    ),
  ]);
};

const SelectModel = function (props) {
  const { model: value } = useContext(RotationsContext);
  const { setModel: onChange, models: options } = props;
  return h(Select, { onChange, options, value, label: "Model" });
};

const SelectFeatureDataset = function (props) {
  const {
    setFeatureDataset: onChange,
    featureDataset: value,
    featureDatasets: options,
  } = props;
  return h(Select, { onChange, options, value, label: "Features" });
};

const SelectProjection = function (props) {
  const { projection, projections, updateState } = useContext(
    MapSettingsContext
  );
  const options = projections.map((d) => d.id);
  const value = projection.id;
  const onChange = function (value) {
    const p = projections.find((d) => d.id === value);
    return updateState({ projection: { $set: p } });
  };
  return h(Select, { onChange, options, value, label: "Projection" });
};

const MapSettingsPanel = function (props) {
  const { keepNorthUp, updateState } = useContext(MapSettingsContext);
  return h("div", [
    h(SelectProjection),
    h(Switch, {
      label: "Keep north up",
      checked: keepNorthUp,
      onChange() {
        return updateState({ $toggle: ["keepNorthUp"] });
      },
      alignIndicator: Alignment.RIGHT,
    }),
  ]);
};

type ControlPanelProps = {
  setTime(n: number): void;
  setModel(n: number): void;
  [k: string]: any;
};

const ControlPanel = function (props: ControlPanelProps) {
  const {
    setTime,
    setModel,
    models,
    featureDatasets,
    featureDataset,
    setFeatureDataset,
  } = props;
  const { time, model } = useContext(RotationsContext);
  const max = 1200;
  return h("div.control-panel", [
    h("div.header", [
      h(
        "h1",
        null,
        h("a", { href: "https://github.com/UW-Macrostrat/Corelle" }, "Corelle")
      ),
      h("p", "Simple plate rotations."),
    ]),
    h(SelectModel, { setModel, models }),
    h(SelectFeatureDataset, {
      setFeatureDataset,
      featureDataset,
      featureDatasets,
    }),
    h(
      FormGroup,
      {
        label: "Reconstruction time",
      },
      [
        h(NumericInput, {
          min: 0,
          max,
          className: "time-input",
          clampValueOnBlur: true,
          fill: true,
          large: true,
          value: time,
          rightElement: h("div.unit-label", "Ma"),
          onValueChange(v) {
            if (setTime != null) {
              return setTime(v);
            }
          },
        }),
      ]
    ),
    h(MapSettingsPanel),
    //h FPSStats
    props.children,
    h("p.credits", [
      h("a", { href: "https://davenquinn.com" }, "Daven Quinn"),
      ", 2019–2020",
    ]),
  ]);
};

export default ControlPanel;
