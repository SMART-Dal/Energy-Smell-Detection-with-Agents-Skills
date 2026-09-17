"""Cases for mutation_during_iteration."""


def drop_inactive(users):
    # Removing while iterating skips the element after each removal.
    for user in users:
        if not user.active:
            users.remove(user)
    return users


def expand_queue(queue):
    # Appending to the collection being walked can extend the loop unboundedly.
    for node in queue:
        queue.append(node.child)
    return queue


def prune_pending(self):
    # The collection is an attribute, which is where it usually lives.
    for job in self.pending:
        if job.done:
            self.pending.remove(job)


def drop_inactive_safely(users):
    # Iterating a snapshot: the repair, not the smell.
    for user in list(users):
        if not user.active:
            users.remove(user)
    return users


def move_between(source, target):
    # A different collection is mutated.
    for item in source:
        target.append(item)
    return target


def work_list(pending):
    # A `while` over a work list is meant to grow; `for` is what breaks.
    seen = []
    while pending:
        node = pending.pop()
        seen.append(node)
        pending.extend(node.children)
    return seen


def count_duplicates(values):
    # `.count()` reads the collection; it does not mutate it.
    return sum(1 for value in values if values.count(value) > 1)


def register_handlers(buttons, items):
    # The lambda runs on a click, not on this pass. Nothing is mutated while
    # the loop is walking.
    for item in items:
        buttons[item.id].on_delete(lambda: items.remove(item))


def drain_queue(queue):
    # `del` is an `ast.Delete`, not a method call, and reads exactly as badly.
    for _ in queue:
        del queue[0]


def shuffle_while_walking(elements):
    # Reordering skips and repeats elements as surely as removing one.
    for _ in elements:
        elements.reverse()


def insert_derived_key(counts):
    # A store under a key built from the loop variable adds an entry, and
    # CPython raises "dictionary changed size during iteration" on the next
    # pass. Neither a call nor a `del`, so a rule watching only those walked
    # past a shape that does not merely skip elements -- it crashes.
    for word in counts:
        counts[word + "_total"] = 0


def overwrite_existing_key(counts):
    # Quiet on purpose, and the reason is the whole distinction: storing under
    # the loop variable itself replaces a key that is already there, the dict
    # never changes size, and this is ordinary correct code.
    for word in counts:
        counts[word] = 0


def store_at_a_list_index(rows):
    # Also quiet. A list store never resizes the list, so the index has to be
    # derived from the loop variable before there is anything to report.
    for row in rows:
        rows[0] = row


def remove_then_stop(users, target):
    # Silent. The `break` means there is no next iteration to skip an element,
    # which is the ordinary way to remove one item by search.
    for user in users:
        if user is target:
            users.remove(user)
            break


def pop_while_enumerating(rows):
    # `enumerate(rows)` walks `rows` itself, so this mutates what it iterates
    # exactly as the bare form does. Requiring a Name or Attribute iterable
    # walked straight past the commonest way the shape is written.
    for index, row in enumerate(rows):
        rows.pop(index)
