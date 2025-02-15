import pkg from "./package.json";
import resolve from "@rollup/plugin-node-resolve";
import babel from "@rollup/plugin-babel";
const deps = { ...pkg.dependencies, ...pkg.peerDependencies };
const extensions = [".ts"];
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
    resolve({ extensions, module: true }),
    babel({
      extensions,
      exclude: "node_modules/**",
      babelHelpers: "bundled",
    }),
  ],
};
