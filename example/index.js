const { join } = require('path')
const _ = require('lodash')
const QuickgRpc = require('quick-grpc')

let startPort = 9000

async function start () {
  let client = await new QuickgRpc({
    host: process.env.HOST || '0.0.0.0:9101',
    basePath: join(__dirname, '..')
  })
  let webcam = await client.webcam()
  webcam.info(undefined, function (err, { webcams }) {
    if (err || !webcams.length) throw err || (new Error('No webcams! Exiting'))
    let cam = webcams[0]
    let webcamId = cam.webcamId
      let StreamRequest = {
        webcamId,
        mode: _.reverse(cam.availableModes)[0],
        port: startPort
      }
      // start stream of first webcam found
      webcam.startStream(StreamRequest, function (err, { url }) {
        if (err) throw err
        console.log(`Webcam /dev/${webcamId}: ${url}`)
        // stop the stream after 10 seconds
        setTimeout(function () {
          webcam.stopStream(StreamRequest, function () {
            process.exit(0)
          })
        }, 10000)
      })
  })
}

start()