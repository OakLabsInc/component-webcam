FROM oaklabs/grpcio-tools:python3.7.0-1.15.0

COPY *.proto /protos/

RUN python -m grpc_tools.protoc --proto_path=/protos/ --python_out=/protos/ --grpc_python_out=/protos/ /protos/*.proto


FROM python:3.7.0-slim
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -qy --no-install-recommends \
    build-essential \
    imagemagick \
    libjpeg-dev \
    libv4l-dev \
    subversion \
    v4l2loopback-utils

COPY mjpgstreamer-input-lib-uvc.patch /tmp/

RUN cd /tmp && svn co https://svn.code.sf.net/p/mjpg-streamer/code mjpg-streamer \
    && cd /tmp/mjpg-streamer/mjpg-streamer \
    && patch -p0 < /tmp/mjpgstreamer-input-lib-uvc.patch \
    && make USE_LIBV4L2=true clean all \
    && make install

WORKDIR /src/

COPY src/requirements.txt ./

RUN pip install -r requirements.txt

COPY src ./

COPY --from=0 /protos/ /protos/

ENV LD_LIBRARY_PATH=/usr/local/lib/ \
    PYTHONUNBUFFERED=yes \
    PYTHONDONTWRITEBYTECODE=yes \
    PYTHONPATH=/protos/

CMD ["python", "server.py"]