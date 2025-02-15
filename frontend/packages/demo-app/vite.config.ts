import {defineConfig} from "vite";
// import * as path from "node:path";
// import * as fs from "node:fs";
//
// // Walk up the directory tree until we find an `.env` file
// const maxParents = 3;
// let envDir = __dirname;
// for (let i = 0; i < maxParents; i++) {
//   const envPath = path.join(envDir, ".env");
//   if (fs.existsSync(envPath)) {
//     envDir = envPath;
//     break;
//   }
//   envDir = path.resolve(path.join(envDir, ".."));
// }
//
export default defineConfig({
  resolve: {
    conditions: ["source"],
  },
  //envDir,
});
