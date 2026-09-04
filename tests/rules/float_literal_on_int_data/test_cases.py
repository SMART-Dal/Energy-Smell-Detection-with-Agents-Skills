"""Cases for float_literal_on_int_data."""


def multiply_elements(counts):
    # The card's own measured example: every product is boxed as a float.
    if not counts:
        return []
    return [n * 3.0 for n in counts]


def scale_row_widths(rows):
    # The same arithmetic in a statement loop rather than a comprehension.
    widths = []
    for row in rows:
        widths.append(row.cells * 2.0)
    return widths


def stack_bar_offsets(series):
    # Augmented assignment is the same add; the literal still forces a float.
    offsets = []
    offset = 0
    for value in series:
        offsets.append(offset)
        offset += 4.0
    return offsets


def countdown_ticks(remaining):
    # Subtraction in a `while` loop: same waste, no `for` in sight.
    ticks = []
    while remaining > 0:
        ticks.append(remaining)
        remaining = remaining - 1.0
    return ticks


def apply_discount(prices):
    # A fractional literal: the float is the point, not an accident.
    return [price * 0.85 for price in prices]


def sample_positions(track):
    # The bound is computed once, before the loop starts: one float multiply.
    picked = []
    for index in range(int(track.length * 2.0)):
        picked.append(track.at(index))
    return picked


def default_timeout(base):
    # One multiplication outside any loop is not worth a report.
    timeout = base * 2.0
    return min(timeout, 30)


def blend_alpha(layers):
    # `0.5` already forces the float, so the `1.0` beside it costs nothing extra.
    blended = []
    for layer in layers:
        blended.append(layer.alpha * 0.5 + 1.0)
    return blended


def above_threshold(readings):
    # A comparison against a float allocates no result object.
    hot = []
    for reading in readings:
        if reading.value > 5.0:
            hot.append(reading)
    return hot


def scale_durations(duration: float, out):
    # The author said this is a float. `duration * 2.0` forces nothing, and
    # assuming every untyped name is an integer is the whole finding.
    for _ in range(100):
        out.append(duration * 2.0)


def fractional_parts(measurements, out):
    # `m % 1.0` is how the fractional part of a float is written, and `% 1`
    # is not the same thing for an int.
    for m in measurements:
        out.append(m % 1.0)
