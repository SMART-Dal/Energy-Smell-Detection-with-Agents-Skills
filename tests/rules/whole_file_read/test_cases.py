"""Cases for whole_file_read."""

import hashlib
import io


def count_errors(path):
    # The whole file is loaded only to be walked line by line.
    with open(path) as handle:
        lines = handle.read().splitlines()
    return sum(1 for line in lines if "ERROR" in line)


def all_lines(path):
    # `readlines` is the same load with a different name.
    with open(path) as handle:
        return [line.rstrip() for line in handle.readlines()]


def response_body(response):
    # Any handle-like receiver counts, not only `open`.
    return response.read()


def checksum(path):
    # A hash needs every byte; the bounded form is the repair.
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while chunk := handle.read(65536):
            digest.update(chunk)
    return digest.hexdigest()


def parse_config(parser, path):
    # `configparser.read(path)` takes a filename and touches no handle.
    parser.read(path)
    return parser


def decode_payload(payload):
    # The bytes are already resident, so there is nothing left to stream.
    buffer = io.BytesIO(payload)
    return buffer.read()


def stream_lines(path):
    # Already streaming.
    with open(path) as handle:
        return sum(1 for line in handle if line.strip())
