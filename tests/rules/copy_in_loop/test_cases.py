"""Cases for copy_in_loop."""

import copy


def refresh_scratch(rows, defaults):
    # Silent. `.copy()` says copy and means nothing else, but the copy is then
    # mutated and appended, so each row needs its own and there is nothing to
    # hoist. Identical to `merge_defaults` below but for the spelling.
    out = []
    for row in rows:
        current = defaults.copy()
        current.update(row)
        out.append(current)
    return out


def snapshot_each(rows, template):
    # `copy.deepcopy` inside a comprehension is the expensive spelling.
    return [copy.deepcopy(template) for _ in rows]


def slice_per_row(rows, header):
    # Silent, and for the same reason as `refresh_scratch`: a `[:]` slice is a
    # copy with different punctuation, but this one is appended to and kept.
    out = []
    for row in rows:
        line = header[:]
        line.append(row)
        out.append(line)
    return out


def copy_once(rows, defaults):
    # Copied above the loop: the repair.
    current = defaults.copy()
    for row in rows:
        current[row.key] = row.value
    return current


def merge_defaults(rows, defaults):
    # A constructor call, not a copy. Nothing in the syntax separates this from
    # `build_from_row` below, and a developer writing either one is not making a
    # mistake, so the rule reports neither.
    out = []
    for row in rows:
        current = dict(defaults)
        current.update(row)
        out.append(current)
    return out


def build_from_row(rows):
    # `dict(row)` converts the loop variable; there is nothing shared to copy.
    return [dict(row) for row in rows]


def slice_a_window(values, width):
    # A partial slice is a window, not a duplicate of the whole container.
    return [values[i:i + width] for i in range(len(values) - width)]


def copy_the_element(rows):
    # Every copy is an element of the result, not a duplicate of one shared
    # container, so there is nothing to hoist.
    return [row[:] for row in rows]


def ends_and_first(batches):
    # The copy is what preserves the caller ordering that the third line reads.
    total = 0
    for batch in batches:
        ordered = sorted(batch)
        total += ordered[0] + ordered[-1]
        total += batch[0]
    return total


def stage_configs(batches, manager, out):
    # `manager.default_config.copy()` is the same copy as `defaults.copy()`,
    # and a receiver test demanding a bare name missed every dotted one.
    for b in batches:
        out.append(manager.default_config.copy())


def find_subsets(nums, path, results):
    # `path` is mutated in place and never rebound, so it looked invariant.
    # The copy is a snapshot of a value that differs every pass; without it
    # `results` ends up a list of empty lists.
    for n in nums:
        path.append(n)
        results.append(path[:])
        find_subsets(nums, path, results)
        path.pop()
