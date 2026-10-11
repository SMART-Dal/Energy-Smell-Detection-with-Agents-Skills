"""Cases for expensive_operand_first."""

import math


def visible_rows(rows, viewer):
    # Card's own example: the permission call runs for every row, even the
    # unpublished ones the attribute read would have rejected for free.
    return [r for r in rows if permitted(viewer, r) and r.published]


def should_retry(response, attempt, policy) -> bool:
    # The expensive operand is a whole sub-expression, not a bare call:
    # `retryable_statuses` builds a set the attempt count often makes pointless.
    return (
        response.status in policy.retryable_statuses(response.host)
        and attempt < policy.max_attempts
    )


def needs_rebuild(config, manifest) -> bool:
    # `or` short-circuits on the first true operand, so the cheap flag belongs first.
    return checksum_changed(manifest) or config.force


class SessionCache:
    def should_evict(self, entry, now) -> bool:
        # Fires: `touch_stats` may be a side effect that
        # has to happen on every call, which only reading it can settle.
        return self.touch_stats(entry) and entry.expires_at < now


def write_if_open(handle, payload):
    # The call is second because it has to be -- `is_open()` raises on None.
    if handle is not None and handle.is_open():
        handle.write(payload)


def resolve_default(cache, key):
    # Both operands call something, so there is no cheap test to promote.
    if cache.get(key) is not None or expensive_default(key):
        return cache[key]
    return None


def fits_on_line(node, width):
    # `isinstance` is a recognisably cheap builtin, not work worth reordering.
    return isinstance(node, Leaf) and node.width <= width


def first_active(rows):
    # The walrus binds the name the second operand reads, so the operands
    # cannot be swapped at all: `row` does not exist until the call has run.
    for candidate in rows:
        if (row := load_row(candidate)) and row.active:
            return row
    return None


def with_tier(rows, wanted):
    # The first operand is the guard that makes the second safe to evaluate;
    # reordering raises on every row whose profile is None.
    return [r for r in rows if r["profile"] is not None
            and tier_rank(r["profile"]) == wanted]


def get_author(post_id, fallback_user):
    # A default passed in rather than written as a literal. Reordering gives
    # `fallback_user or fetch_username(post_id)`, which never queries at all
    # when the fallback is truthy.
    return fetch_username(post_id) or fallback_user


def worth_processing(data):
    # `len` is in CHEAP_CALLS, and banning every call in the second position
    # hid exactly the guards this rule exists to promote.
    if query_external_service(data) and len(data) > 0:
        return True
    return False


def extract_role(messages):
    # An `or` whose value is kept: the call's result with a fallback. Swapping
    # the operands returns the fallback whenever it is truthy.
    role = None
    for msg in messages:
        role = msg.get("role") or role
    return role


def fenced_blocks(lines):
    # `"```" in t` is a substring search over the whole line, and `startswith`
    # checks three characters: the "cheaper" test is the dearer one.
    return [t for t in lines if t.startswith("```") and "```" in t]


def positive_number(number):
    # `math.isfinite` and `str.endswith` cost what the comparison beside them costs.
    if math.isfinite(number) and number > 0:
        return number
    return None


def zip_target(fname, chat_id):
    if fname.endswith(".zip") and chat_id:
        return chat_id
    return None


def known_method(request):
    # A membership test against a literal written out here is short, so it is
    # still the cheap test to put first.
    if verify_signature(request) and request.method in ("GET", "HEAD"):
        return True
    return False


def local_timezone():
    # A fallback to a module constant: `UTC or now()...` would always be UTC.
    return datetime.now().astimezone().tzinfo or UTC
