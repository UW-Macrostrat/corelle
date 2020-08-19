import pkg from "./package.json";
import typescript from "rollup-plugin-typescript2";
import resolve from "@rollup/plugin-node-resolve";
const deps = { ...pkg.dependencies, ...pkg.peerDependencies };

//https://2ality.com/2017/02/babel-preset-env.html

export default {
  input: "src/index.ts", // our source file
  preserveModules: true,
  output: [
    {
      dir: pkg.module,
      format: "esm",
      sourcemap: true,
    },
    {
      dir: pkg.main,
      format: "cjs",
      sourcemap: true,
    },
  ],
  external: Object.keys(deps),
  plugins: [
    resolve({ extensions: ".ts" }),
    typescript({ useTsconfigDeclarationDir: true }),
  ],
};
