# Webcams

Requirements for use:

* `PORT` env var set to port that gRPC server should listen on
* `/dev/video*` devicess mounted
* `/dev/oak/webcam/` bind-mounted
* This udev rule on the host:

```
SUBSYSTEM=="video4linux", SYMLINK+="oak/webcam/$env{ID_SERIAL}"
```

## Dev Notes

To run the unit tests, make sure at least one webcam is plugged in and
the above udev rule has fired. Then use this command:

```
docker-compose run server python -m pytest
```
