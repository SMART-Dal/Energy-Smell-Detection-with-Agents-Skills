"""C9.S1 Fragmented I/O Operations -- one write per line against one buffered
write.

The same root cause with a filesystem rather than a database behind it, which
is the medium the card says makes the fixed cost a syscall and a flush of a
microsecond or two rather than a millisecond round trip. Comparing the two
readings is how the card can say how much the medium is worth.
"""

import os
import tempfile


def before(lines):
    handle, path = tempfile.mkstemp(suffix=".c9s1")
    os.close(handle)
    try:
        with open(path, "w", encoding="utf-8") as out:
            for line in lines:
                out.write(line)
                out.flush()                 # one syscall per line
        return os.path.getsize(path)
    finally:
        os.unlink(path)


def after(lines):
    handle, path = tempfile.mkstemp(suffix=".c9s1")
    os.close(handle)
    try:
        with open(path, "w", encoding="utf-8") as out:
            out.writelines(lines)
        return os.path.getsize(path)
    finally:
        os.unlink(path)


def cases():
    return [("many-lines", lambda: ([f"line {i}\n" for i in range(20_000)],)),
            ("few-lines",  lambda: ([f"line {i}\n" for i in range(20)],))]
