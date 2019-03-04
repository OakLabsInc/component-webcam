import re
import subprocess

from natsort import natsorted


def v4l2_ctl(*args):
    return subprocess.run(
        args=['v4l2-ctl'] + list(args),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)


def webcam_info(device_path):
    output = v4l2_ctl(
        '-d', device_path, '--list-formats-ext').stdout.decode("utf-8")
    lines = iter(output.splitlines())
    next(lines)  # skip line "ioctl: VIDIOC_ENUM_FMT"
    formats = []
    current_index = None
    current_res = None
    for line in lines:
        m = re.match(r'\tIndex       : (\d+)', line)
        if m:
            current_index = {
                'modes': [],
            }
            formats.append(current_index)
            continue
        m = re.match(r'\t([\w ]+?)\s*: (.+)$', line)
        if m:
            k, v = m.group(1), m.group(2)
            if k == 'Name':
                current_index['name'] = v
            continue
        m = re.match(r'\t\tSize: Discrete (\w+)', line)
        if m:
            current_res = m.group(1)
            continue
        m = re.match(
            r'\t\t\tInterval: Discrete [0-9.]+s \(([0-9.]+) fps\)', line)
        if m:
            mode = '%s@%s' % (current_res, m.group(1))
            current_index['modes'].append(mode)
            continue

    for f in formats:
        f['modes'] = natsorted(f['modes'])

    # for now, we're only supporting MJPEG
    formats_by_name = {f.pop('name'): f for f in formats}

    # On OakOS it's "Motion-JPEG" but on other systems it's 'MJPEG'
    # It's not clear what causes the difference, probably some version
    # mismatch, but for now this hack covers it up.
    if 'MJPEG' in formats_by_name:
        formats_by_name['Motion-JPEG'] = formats_by_name.pop('MJPEG')

    return formats_by_name


def supports_mode(device_path, pixel_type, mode):
    info = webcam_info(device_path)
    supported = info.get(pixel_type, {}).get('modes', [])
    return mode in supported
