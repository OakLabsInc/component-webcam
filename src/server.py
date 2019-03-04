import concurrent.futures
import grpc
import os
import signal
import subprocess
import time
import v4l2

import webcam_pb2
import webcam_pb2_grpc

PORT = os.getenv('PORT')
DEVICE_DIR = '/dev/'
STREAMS_BY_WEBCAM_ID = {}


def main():
    signal.signal(signal.SIGTERM, signal_handler)
    address = '0.0.0.0:%s' % PORT
    server = make_server(address)

    try:
        server.start()
        print('webcam component serving on %s' % address)
        while True:
            time.sleep(60 * 60 * 24)
    except KeyboardInterrupt:
        server.stop(5).wait()


class QuitException(BaseException):
    pass


def signal_handler(sig_num, frame):
    raise QuitException


def make_server(address):
    server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=10))
    webcam_pb2_grpc.add_WebcamServicer_to_server(WebcamServicer(), server)
    server.add_insecure_port(address)
    return server


class WebcamServicer(webcam_pb2_grpc.WebcamServicer):

    def Info(self, request, context):
        webcam_ids = filter(lambda name: name.startswith('video'), safe_list_dir(DEVICE_DIR))
        webcams = []
        for webcam_id in webcam_ids:
            info = v4l2.webcam_info(os.path.join(DEVICE_DIR, webcam_id))
            if 'Motion-JPEG' in info:
                webcams.append({
                    'webcam_id': webcam_id,
                    'available_modes': info['Motion-JPEG']['modes'],
                })
        return webcam_pb2.WebcamInformation(webcams=webcams)

    def StartStream(self, request, context):
        webcam_id = request.webcam_id
        if webcam_id in STREAMS_BY_WEBCAM_ID:
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            context.set_details('Webcam is already streaming')
            return webcam_pb2.Empty()

        full_path = os.path.join(DEVICE_DIR, webcam_id)
        dev_path = os.path.join(full_path, os.path.realpath(full_path))
        port, mode = request.port, request.mode
        if not v4l2.supports_mode(full_path, 'Motion-JPEG', mode):
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details('Webcam does not support mode')
            return webcam_pb2.Empty()
        if not port.isdigit() and 9000 <= int(port) <= 9999:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details('port must be numeric between 9000 and 9999')
            return webcam_pb2.Empty()
        r, f = parse_video_mode(mode)
        process = subprocess.Popen(
            args=[
                'mjpg_streamer',
                '-i', 'input_uvc.so -d %s -r %s -f %s' % (dev_path, r, f),
                '-o', 'output_http.so -p %s' % port,
            ],
            # Despite these lines, there will still be some output in the logs.
            # I can't explain why, but I suspect it's the gRPC library's fault.
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        STREAMS_BY_WEBCAM_ID[webcam_id] = {
            'process': process,
            'mode': mode,
            'port': port,
        }
        url = 'http://localhost:%s/?action=stream_0' % port
        return webcam_pb2.JpgStream(url=url)

    def StopStream(self, request, context):
        stream = STREAMS_BY_WEBCAM_ID.pop(request.webcam_id, None)
        if stream is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Webcam is not streaming")
            return webcam_pb2.Empty()
        process = stream['process']
        process.send_signal(signal.SIGTERM)
        process.wait()  # this is necessary to prevent zombie processes
        return webcam_pb2.Empty()

def safe_list_dir(path):
    return os.listdir(path) if os.path.isdir(path) else []


def parse_video_mode(mode):
    resolution, framerate = mode.split('@', 1)
    return resolution, framerate


if __name__ == '__main__':
    main()
