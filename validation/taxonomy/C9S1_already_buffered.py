"""C9.S1 Fragmented I/O Calls -- the file object was already
batching.

`C9S1_writelines` measures one write per line against one buffered write at
+95.8%, and `C9S1_fragmented_io` at +97%. Both of those call `flush()` in the
loop, which is what makes each line a syscall.

Without the flush there is no fragmentation to remove. A Python file object
buffers 8 KB by default, so a loop of `write()` calls already issues one syscall
per 8 KB; joining the lines first adds a full copy of the payload into a new
string and then hands the same bytes to the same buffer. The I/O is identical
and the repair is a memory allocation the size of the output.

Look for what actually crosses the boundary before batching: an unflushed file
object, a buffered socket, an ORM that defers until commit, and a client library
with its own queue are all already doing this, and the repair only moves the
copying.
"""

import os
import tempfile

_DIR = tempfile.mkdtemp(prefix="c9s1-counter-")


def before(lines):
    path = os.path.join(_DIR, "a.txt")
    with open(path, "w", encoding="utf-8") as out:
        for line in lines:
            out.write(line)                  # buffered; no flush
    return os.path.getsize(path)


def after(lines):
    path = os.path.join(_DIR, "b.txt")
    with open(path, "w", encoding="utf-8") as out:
        out.write("".join(lines))            # one string, then the same buffer
    return os.path.getsize(path)


def cases():
    return [("many-lines", lambda: ([f"line {i}\n" for i in range(200_000)],)),
            ("long-lines", lambda: ([f"line {i} " + "pad " * 200 + "\n"
                                     for i in range(20_000)],)),
            ("edge",       lambda: ([],))]
