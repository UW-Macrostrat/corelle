const Bundler = require('parcel-bundler');
const express = require('express');
const proxy = require('http-proxy-middleware');
const { spawn } = require('child_process');

const port = '3432';
// Run the backend dev server (quits on exiting this script)
const backend = spawn(
  'plates',
  ['serve', '--debug', '-p', port], {
  stdio: ['ignore', 'inherit', 'inherit']
});

let app = express();

let bundler = new Bundler('./index.html');
const apiProxy = proxy({target: `http://0.0.0.0:${port}`});

app.use('/api', apiProxy);
app.use(bundler.middleware());
