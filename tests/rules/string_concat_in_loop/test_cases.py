"""Cases for string_concat_in_loop."""


class Report:
    def render(self, rows):
        # Card's own example: aliased through an attribute, so no in-place resize.
        self.buf = ""
        for row in rows:
            self.buf += render_row(row)
        return self.buf

    def rebuild(self, rows):
        # Same waste written as `s = s + x` rather than `s += x`.
        self.out = ""
        for row in rows:
            self.out = self.out + str(row)
        return self.out


def join_the_parts(rows):
    # The repair itself: nothing grows.
    parts = []
    for row in rows:
        parts.append(str(row))
    return "".join(parts)


def count_matches(rows, needle):
    # Numeric accumulator, not a string.
    found = 0
    for row in rows:
        if needle in row:
            found += 1
    return found


def grow_plain_local(chunks):
    # Unaliased local: CPython resizes in place, so this is already linear.
    out = ""
    for chunk in chunks:
        out += chunk
    return out


def grow_local_and_read_it(chunks, limit):
    # The read takes a second reference, so the in-place resize cannot fire.
    out = ""
    for chunk in chunks:
        out += chunk
        if len(out) > limit:
            flush(out)
    return out


def group_by_key(rows):
    # Subscript target: aliased through the container.
    grouped = {}
    for row in rows:
        grouped.setdefault(row.key, "")
        grouped[row.key] += row.text
    return grouped


def render_grid(table):
    # Nested loops: one statement, so it must be reported once and not twice.
    cells = Report()
    cells.buf = ""
    for line in table:
        for value in line:
            cells.buf += str(value)
    return cells.buf


def build_bytes(chunks):
    # Bytes are immutable too; the same copying applies through an attribute.
    holder = Report()
    holder.buf = b""
    for chunk in chunks:
        holder.buf += bytes(chunk)
    return holder.buf


def header_then_body(rows):
    # Concatenation outside any loop is one allocation.
    text = "HEAD" + "\n"
    for row in rows:
        emit(text, row)
    return text


def build_row(cells):
    # `res = res + "[" + c + "]"` is left-associative, so the accumulator sits
    # at the bottom of the left spine rather than at `value.left`. Comparing
    # only the immediate operand missed every concatenation of three or more
    # parts, which is how anyone actually builds a line.
    res = ""
    for c in cells:
        res = res + "[" + c + "]"
    return res


def grow_with_an_fstring(rows):
    # An f-string that interpolates its own target is the same quadratic growth
    # as `s = s + x` to a reader and a worse one to the interpreter: `+=` and
    # `+` reach `unicode_concatenate`, which resizes in place when the refcount
    # is 1, while an f-string compiles to BUILD_STRING and always allocates.
    # Measured 20k -> 40k: `out += p` 1.15 -> 2.10 ms, `out = f"{out}{p}"`
    # 41.16 -> 260.18 ms. So this fires even though the accumulator is a plain
    # local, which is exactly where the other two spellings are safe.
    out = ""
    for row in rows:
        out = f"{out}{row}"
    return out


def fstring_that_does_not_read_itself(rows):
    # Quiet: an f-string per iteration allocates, but it is not accumulation --
    # nothing grows, so there is no quadratic copy to report.
    out = ""
    for row in rows:
        out = f"[{row}]"
    return out


def tally(rows):
    # One key holds text, so `snapshot[...]` looks textual -- but `+= 1` is a
    # counter, and adding a number to text would raise.
    snapshot = {"message": ""}
    for row in rows:
        if row.bad:
            snapshot["message"] = "some rows were rejected"
            snapshot["invalid"] += 1
    return snapshot
