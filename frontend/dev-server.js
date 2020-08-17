/*
This dev server supports local development.
For development in a Docker containerized setting,
parcel should be run directly.
*/
import Bundler from "parcel-bundler";
import express from "express";
import proxy from "http-proxy-middleware";
import path from "path";
import { spawn } from "child_process";

const port = 3432;
const mainPort = 5000;
// Run the backend dev server (quits on exiting this script)
const backend = spawn("corelle", ["serve", "--debug", "-p", port], {
  stdio: ["ignore", "inherit", "inherit"],
});

spawn("npm", ["run", "dev"], {
  stdio: ["ignore", "inherit", "inherit"],
  cwd: path.resolve(__dirname, "..", "corelle-client"),
});

let app = express();

let bundler = new Bundler("./index.html", {
  // Scope hoisting interferes with CSS bundling apparently
  //scopeHoist: true,
  detailedReport: true,
});
const apiProxy = proxy({ target: `http://127.0.0.1:${port}` });

app.use("/api", apiProxy);
app.use(bundler.middleware());

app.listen(mainPort, () => {
  console.log(`Corelle test app listening on port ${mainPort}`);
});

bundler.on("buildEnd", () => {
  console.log(`Frontend is built and available on port ${mainPort}`);
});
