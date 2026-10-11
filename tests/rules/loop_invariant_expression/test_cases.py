"""Cases for loop_invariant_expression."""

from typing import Dict, List

WEIGHTS = {"default": 1.0, "boosted": 2.5}


def filter_rows(rows, config):
    # One invariant nested inside another: the subscript is part of the call,
    # so the pair must be reported once and not twice.
    kept = []
    for row in rows:
        if row.score > max(config["thresholds"]):
            kept.append(row)
    return kept


def take_while_small(values, limit):
    # A `while` test *is* re-evaluated every pass, unlike a `for` iterable.
    index = 0
    while index < limit and values[index] < max(values) / 2:
        emit(values[index])
        index += 1


def cross_check(orders, customers, region):
    # Invariant in a nest: one finding, attributed to the innermost loop.
    for order in orders:
        for customer in customers:
            if customer.region == region.strip().lower():
                link(order, customer)


def score_all(records):
    # A module-level dict indexed by a constant key: nothing here can change.
    total = 0
    for record in records:
        total += record.weight * WEIGHTS["default"]
    return total


def index_walk(values):
    # `len(values)` sits in the iterable clause, which runs once before the loop.
    for i in range(len(values)):
        process(values[i], i)


def walk_tree(queue):
    # The length must be recomputed: `extend` grows the very list it measures.
    position = 0
    while position < len(queue):
        queue.extend(children_of(queue[position]))
        position += 1
    return queue


def compact(values):
    # `del` shortens the list, so hoisting the bound would read past the end.
    i = 0
    while i < len(values):
        if values[i] is None:
            del values[i]
        else:
            i += 1
    return values


def bucket_lengths(rows):
    # Looks repetitive, reads the loop variable: a different value every pass.
    sizes = []
    for row in rows:
        sizes.append(len(row.items))
    return sizes


def take_until_full(rows, ceiling):
    # `ceiling - len(out)` reads the container the loop is filling, so it is
    # invariant in text only.
    out = []
    for row in rows:
        capacity = ceiling - len(out)
        if capacity > 0:
            out.append(row)
    return out


def best_per_group(groups):
    # `x` is the lambda's own parameter, rebound on every call.
    picked = {}
    for key, rows in groups.items():
        picked[key] = max(rows, key=lambda x: x[1])
    return picked


def report_failures(futures):
    # `e` is rebound by every iteration that raises, so `str(e)` is not
    # invariant -- and `except ... as e` carries its name as a bare string,
    # which no walk over Name nodes can see.
    for future in futures:
        label = futures[future]
        try:
            future.result(timeout=60)
        except Exception as e:
            print(f"failed {label}: {str(e)}")


def normalise(values):
    # The total is recomputed once per element: quadratic on a long list, and
    # a comprehension hides it exactly as a `for` statement would.
    return [v / sum(values) for v in values]


def row_products(a, b):
    # `a[i]` does not depend on `j`, so the inner comprehension re-reads it
    # once per column -- the lookup `C3S4_genuinely_quadratic` hoisted, at
    # +16-19%. `range(len(b))` is invariant too, but it is a lazy range: one
    # call saved per row, not a finding.
    return [[a[i] * b[j] for j in range(len(b))] for i in range(len(a))]


def strip_prefix(keys):
    # `len("private_word:")` is one builtin call on a constant.
    out = []
    for key in keys:
        if key.startswith("private_word:"):
            out.append(key[len("private_word:"):])
    return out


def mark_missing(rows, markers, arm):
    # `markers[arm]` is a lookup by a key that never changes: reported.
    # `float("nan")` is one builtin call on a constant: not.
    out = []
    for row in rows:
        out.append((row, markers[arm], float("nan")))
    return out


def variants(kwargs, keys):
    # `dict(kwargs)` reads nothing the loop changes, but each pass edits its own
    # copy: hoisting it would hand every pass the same dict.
    out = []
    for key in keys:
        changed = dict(kwargs)
        changed[key] = None
        out.append(changed)
    return out


def keep_odd(xs, k):
    # The same set built on every pass and only ever read.
    out = []
    for x in xs:
        allowed = {i for i in range(1, k, 2)}
        if x in allowed:
            out.append(x)
    return out


def sorted_once(rows):
    # A comprehension's first iterable runs once, before iteration starts.
    return [row.id for row in sorted(rows)]


class Order:
    pass


def collect_batches(groups):
    # `List[Order]` is a subscript that does not vary, and it is not work:
    # a function-local annotation is never evaluated, whatever its target.
    # The `[]` beside it is still a fresh list per pass, which is somebody
    # else's rule.
    out = []
    for group in groups:
        batch: List[Order] = []
        seen: Dict[str, List[Order]] = {}
        batch.append(group)
        seen[str(group)] = batch
        out.append(seen)
    return out


def score_batches(batches, static_weights):
    # A generator is a single-use iterator. Hoisting `gen = (w * 2 for w in
    # static_weights)` above the loop leaves it exhausted after the first
    # pass, so this "invariant" must not be reported -- unlike the list
    # comprehension beside it, which rebuilds nothing and hoists cleanly.
    for batch in batches:
        gen = (w * 2 for w in static_weights)
        consume(batch, gen)


def score_batches_inline(batches, static_weights):
    # The same generator passed straight to a call, with no name to hoist to.
    for batch in batches:
        consume(batch, (w * 2 for w in static_weights))


class Service:
    def dispatch(self, rows):
        # `self.log.debug(...)` mutates `self.log` and nothing else, so
        # `max(self.limits)` is still invariant and still reportable. Tracking
        # the mutation by its root name instead marked the whole of `self` as
        # changed, and one logging call inside a loop was enough to hide every
        # other `self.*` invariant in it -- which, in method-heavy code, is most
        # loops the rule ever sees.
        for row in rows:
            self.log.debug(row)
            if row.size > max(self.limits):
                skip(row)

    def touches_what_it_reads(self, rows):
        # Quiet: the read reaches inside the thing that changed.
        for row in rows:
            self.log.debug(row)
            if row.size > max(self.log.limits):
                skip(row)

    def rebuilds_itself(self, rows):
        # Quiet: a method on `self` can touch anything under it, so the bare
        # receiver still suppresses its whole subtree.
        for row in rows:
            self.reset()
            if row.size > max(self.limits):
                skip(row)


def parse_judge(raw):
    # The slice is in a `return`, which ends the loop: it runs once, not per pass.
    for attempt in range(3):
        if attempt_parse(raw, attempt):
            continue
        return {"score": -1, "reason": raw[:200]}
    return None


def refresh_all(module, tracked, samples):
    # A defensive copy handed straight to a call that may keep or change it.
    out = []
    for live in samples:
        out.append(module.update_stats(dict(tracked), live))
    return out


def tally_by_arm(rows, arms):
    # Each arm gets its own counter dict, changed below: hoisting the inner
    # comprehension would hand every arm the same one.
    counts = {arm: {s: 0 for s in (0, 1, 2, 3)} for arm in arms}
    for row in rows:
        counts[row.arm][row.score] += 1
    return counts


def records(results, targets):
    # The list is part of each record that is kept.
    out = []
    for result in results:
        out.append({"result": result, "targets": [(t[0], t[1]) for t in targets]})
    return out


def apply_patches(rows, patch):
    # `patch.items()` builds a view per row: a call, not a finding.
    for row in rows:
        for key, value in patch.items():
            row[key] = value


def present(keys, mapping):
    # Membership through a view is the C4.S8 shape: still reported here.
    return [k for k in keys if k in mapping.keys()]
