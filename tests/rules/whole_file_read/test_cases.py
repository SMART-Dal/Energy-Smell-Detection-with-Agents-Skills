"""Cases for whole_file_read."""

import hashlib
import io
import json


def count_errors(path):
    # Loaded whole, then walked a line at a time: `.splitlines()` is the tell.
    with open(path) as handle:
        lines = handle.read().splitlines()
    return sum(1 for line in lines if "ERROR" in line)


def all_lines(path):
    # `readlines` consumed by a comprehension is the same load and the same walk.
    with open(path) as handle:
        return [line.rstrip() for line in handle.readlines()]


def each_record(path):
    # A statement loop over `readlines` counts too.
    total = 0
    with open(path) as handle:
        for line in handle.readlines():
            total += len(line)
    return total


def split_on_newline(path):
    # `.split("\n")` is `.splitlines()` with different punctuation.
    with open(path) as handle:
        return handle.read().split("\n")


def response_body(response):
    # The whole body *is* the return value. There is no streaming form of this.
    return response.read()


def config_document(path):
    # A document has to be parsed whole; nothing consumes it a line at a time.
    with open(path) as handle:
        return json.loads(handle.read())


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
    # The bytes are already resident, so there is nothing left to stream --
    # even though the walk that would otherwise qualify is right here.
    buffer = io.StringIO(payload)
    return [line for line in buffer.read().splitlines()]


def fields_not_lines(path):
    # `.split(",")` breaks the content into fields. Iterating the handle would
    # not produce them, so there is no streaming form to recommend.
    with open(path) as handle:
        return handle.read().split(",")


def stream_lines(path):
    # Already streaming.
    with open(path) as handle:
        return sum(1 for line in handle if line.strip())


def parse_paragraphs(doc_handle):
    # `split("\n\n")` cuts paragraphs, not lines. Iterating the handle yields
    # single lines, so the repair would change what this produces -- and a
    # substring test for "\n" said it was a line walk.
    return doc_handle.read().split("\n\n")


def dispatch_all(handle):
    # The same pattern one name apart. Keying producer to consumer on `id()`
    # alone could never join an `ast.Call` to the `ast.Name` that reads it.
    lines = handle.readlines()
    for line in lines:
        dispatch(line)
