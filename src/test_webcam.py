import server
import grpc
import pytest
import time

import webcam_pb2
import webcam_pb2_grpc

EMPTY = webcam_pb2.Empty()


@pytest.fixture(scope='session')
def stub():
    s = server.make_server('0.0.0.0:10000')
    s.start()
    channel = grpc.insecure_channel('localhost:10000')
    yield webcam_pb2_grpc.WebcamStub(channel)
    s.stop(0)


def test_info(stub):
    i = stub.Info(EMPTY)
    assert len(i.webcams)


def test_start_and_stop_stream(stub):
    info = stub.Info(EMPTY)
    for webcam in info.webcams:
        stub.StartStream(webcam_pb2.StreamRequest(
            webcam_id=webcam.webcam_id,
            mode=webcam.available_modes[-1],
            port='9999',
        ))
        time.sleep(5)

        stub.StopStream(webcam_pb2.StreamRequest(
            webcam_id=webcam.webcam_id,
        ))
