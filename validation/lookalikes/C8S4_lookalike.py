"""C8.S4 Redundant Data Fetching -- LOOKS THE SAME, IS NOT: the source changes during
the call.

"Loading a configuration file from disk on every incoming request when it only
changes on application restart" is the description, and `C8S4_same_file_reread`
measures hoisting the read at +99.7%. The load-bearing clause is the last one.

The file here is a job queue that another process appends to, which is why it is
being re-read: each pass is meant to see whatever has arrived. Reading it once
before the loop turns a poll into a single snapshot, and the rows written after
the call started are never seen. The function returns quickly and reports less
work than there was.

Caching an external read is a claim about the source's update frequency
relative to the call. State the claim in the finding -- "the file is written
only at deploy time", "the row is immutable once created" -- so that a reviewer
can disagree with it. Where the answer is "it changes while we run", the repeated
fetch is the feature.
"""

import os
import tempfile

_HANDLE, _PATH = tempfile.mkstemp(suffix=".c8s4-counter")
with os.fdopen(_HANDLE, "w", encoding="utf-8") as _out:
    for _i in range(400):
        _out.write(f"job {_i}\n")


def _read_jobs():
    with open(_PATH, encoding="utf-8") as handle:
        return handle.read().count("\n")


def _append_job(text):
    with open(_PATH, "a", encoding="utf-8") as handle:
        handle.write(text)


def _reset():
    """Back to 400 rows, so repeated calls measure the same work.

    Without this the file grows for the life of the process and every
    repetition of the measured window reads a longer file than the last."""
    with open(_PATH, "w", encoding="utf-8") as handle:
        for i in range(400):
            handle.write(f"job {i}\n")


def before(rounds):
    _reset()
    seen = 0
    for index in range(rounds):
        seen += _read_jobs()               # re-read: sees what has arrived
        if index % 8 == 0:
            _append_job(f"job extra {index}\n")
    return seen


def after(rounds):
    _reset()
    jobs = _read_jobs()                    # hoisted: one snapshot
    seen = 0
    for index in range(rounds):
        seen += jobs
        if index % 8 == 0:
            _append_job(f"job extra {index}\n")
    return seen


def cases():
    return [("many-rounds", lambda: (400,)),
            ("one-round",   lambda: (1,)),
            ("edge",        lambda: (0,))]
