import Bundler from 'parcel-bundler';
import express from 'express';
import proxy from 'http-proxy-middleware';
import { spawn } from 'child_process';

const port = 3432;
const mainPort = 5000;
// Run the backend dev server (quits on exiting this script)
const backend = spawn(
  'plates',
  ['serve', '--debug', '-p', port], {
  stdio: ['ignore', 'inherit', 'inherit']
});

let app = express();

let bundler = new Bundler('./index.html', {
  // Scope hoisting interferes with CSS bundling apparently
  //scopeHoist: true,
  detailedReport: true
});
const apiProxy = proxy({target: `http://127.0.0.1:${port}`});

app.use('/api', apiProxy);
app.use(bundler.middleware());

app.listen(mainPort, ()=>{
  console.log(`Corelle test app listening on port ${mainPort}`);
});