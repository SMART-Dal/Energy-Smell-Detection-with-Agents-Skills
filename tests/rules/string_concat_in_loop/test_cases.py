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
