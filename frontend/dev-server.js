/*
This dev server supports local development.
For development in a Docker containerized setting,
parcel should be run directly.
*/
// TODO: this may not run with Parcel 2
import Bundler from "parcel";
import express from "express";
import { createProxyMiddleware } from "http-proxy-middleware";
import path from "path";
import { spawn } from "child_process";

const port = 3432;
const mainPort = 5000;
// Run the backend dev server (quits on exiting this script)
const backend = spawn("corelle", ["serve", "--debug", "-p", port], {
  stdio: ["ignore", "inherit", "inherit"],
});

let app = express();

process.env.CORELLE_API_BASE_URL = `http://127.0.0.1:${port}/api`

let bundler = new Bundler("./index.html", {
  // Scope hoisting interferes with CSS bundling apparently
  //scopeHoist: true,
  detailedReport: true,
});
const apiProxy = createProxyMiddleware({ target: `http://127.0.0.1:${port}` });

app.use("/api", apiProxy);
app.use(bundler.middleware());

app.listen(mainPort, () => {
  console.log(`Corelle test app listening on port ${mainPort}`);
});

bundler.on("buildEnd", () => {
  console.log(`Frontend is built and available on port ${mainPort}`);
});
