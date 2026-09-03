"""Cases for global_lookup_in_loop."""

import itertools
import math

MAX_RETRIES = 5
FEATURE_FLAGS = {}
FIELD_LABELS = {}
KIND_TABLE = {}
WEIGHTS = {}


def count_exhausted(attempts):
    # A module constant probed four times per attempt: one dict probe each.
    total = 0
    for attempt in attempts:
        if attempt.tries >= MAX_RETRIES:
            total += 1
        elif attempt.tries == MAX_RETRIES - 1:
            log_warning(attempt, MAX_RETRIES, MAX_RETRIES)
    return total


def render_rows(rows):
    # The card's own repair example: a builtin resolved three times per row.
    out = []
    for row in rows:
        out.append(str(row.key) + "=" + str(row.value) + "/" + str(row.unit)
                   + ":" + str(row.scale))
    return out


def score_matrix(grid):
    # Nested loops, one name: one hoist to suggest, not one report per loop level.
    total = 0
    for row in grid:
        for cell in row:
            if cell in WEIGHTS:
                total += WEIGHTS[cell] * WEIGHTS.get(cell, 1) + WEIGHTS["base"]
    return total


def summarise_batch(records):
    # Two names past the threshold, and the cap allows two per loop.
    lines = []
    for record in records:
        label = FIELD_LABELS.get(record.field, FIELD_LABELS["default"])
        width = FIELD_LABELS.get(record.field + "_width", FIELD_LABELS["pad"])
        lines.append(format_cell(label, width) + format_cell(record.value, width)
                     + format_cell(record.unit, width) + format_cell(width, width))
    return lines


def classify_tokens(tokens):
    # Three names past the threshold; only the worst two are reported per loop.
    tagged = []
    for token in tokens:
        kind = (KIND_TABLE.get(token.text) or KIND_TABLE.get(token.lower())
                or KIND_TABLE.get(token.stem) or KIND_TABLE.get(token.root)
                or KIND_TABLE["?"])
        weight = WEIGHTS[kind] + WEIGHTS.get(token.text, 0) + WEIGHTS["base"] + WEIGHTS["pad"]
        tagged.append(normalise(kind, normalise(weight, normalise(token, 0))))
    return tagged


def tally_flags(events):
    # Three reads per iteration is one under the threshold: not worth a local.
    enabled = 0
    for event in events:
        if event.flag in FEATURE_FLAGS:
            enabled += FEATURE_FLAGS[event.flag]
    return enabled


def replay_events(primary, backup):
    # All three reads sit in the iterable, which is evaluated once before the loop.
    total = 0
    for event in itertools.chain(itertools.islice(primary, 100), itertools.cycle(backup)):
        total += event.weight
    return total


def accumulate_totals(rows, factor):
    # `scale` is assigned in this unit, so every read is already a frame slot.
    scale = factor * 2
    total = 0
    for row in rows:
        total += row.a * scale + row.b * scale + row.c * scale
    return total


def scale_readings(readings):
    # A comprehension pays the same lookup per element as the loop it replaces.
    return [math.sqrt(math.fabs(math.floor(math.trunc(r)))) for r in readings]


def total_readings(readings):
    # Same four lookups, in a generator expression.
    return sum(math.sqrt(math.fabs(math.floor(math.trunc(r)))) for r in readings)


class Throttle:
    def apply_limits(self, requests):
        # An attribute chain, not a scope lookup: `self` is a parameter.
        allowed = []
        for request in requests:
            if request.size <= self.limits.max_size and request.rate <= self.limits.max_rate:
                allowed.append(request)
            elif request.size <= self.limits.hard_cap:
                allowed.append(request.truncate())
        return allowed


def above_threshold(values):
    # `recalibrate` rebinds THRESHOLD, so a local bound above the loop freezes
    # a number the loop is deliberately watching move.
    above = 0
    for index, value in enumerate(values):
        if index and index % 1_000 == 0:
            recalibrate(value)
        if value > THRESHOLD:
            above += 1
    return above


def scale_all(readings):
    # Three reads: right at the old threshold and deliberately below the new
    # one. A module a loop reaches for three times is ordinary code, and the
    # hoist trades a dict lookup for a name the next reader has to follow.
    out = []
    for reading in readings:
        out.append(math.floor(reading) + math.ceil(reading) + math.trunc(reading))
    return out

