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
