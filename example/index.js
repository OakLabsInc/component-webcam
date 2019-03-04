const { join } = require('path')
const _ = require('lodash')
const QuickgRpc = require('quick-grpc')

async function start () {
  let client = await new QuickgRpc({
    host: process.env.HOST || '0.0.0.0:9101',
    basePath: join(__dirname, '..')
  })
  let webcam = await client.webcam()
  webcam.info(undefined, function (err, { webcams }) {
    console.log('* WEBCAMS:', JSON.stringify(webcams, null, 2))
  })
}

start()