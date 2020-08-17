import pkg from "./package.json";
import typescript from "@rollup/plugin-typescript";
const deps = { ...pkg.dependencies, ...pkg.peerDependencies };

//https://2ality.com/2017/02/babel-preset-env.html

const extensions = [".js", ".ts", ".tsx", ".d.ts"];

export default {
  input: "index.ts", // our source file
  preserveModules: true,
  output: [
    {
      dir: pkg.module,
      format: "esm",
      sourcemap: true,
    },
  ],
  external: Object.keys(deps),
  plugins: [typescript()],
};
