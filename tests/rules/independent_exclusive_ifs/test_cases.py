"""Cases for independent_exclusive_ifs."""


def route_event(kind, payload):
    # Three unchained tests on one subject; every pass evaluates all three.
    if kind == "created":
        index_document(payload)
    if kind == "updated":
        reindex_document(payload)
    if kind == "deleted":
        drop_document(payload)


class ReportStyle:
    def decorate(self, cell):
        # Same shape keyed on an attribute rather than a local.
        if self.mode == "plain":
            cell.style = None
        if self.mode == "zebra":
            cell.style = self.zebra_for(cell)
        if self.mode == "heatmap":
            cell.style = self.heat_for(cell)
        return cell


def apply_directives(token, node):
    # Two separate runs in one body, so two findings rather than one.
    if token.op == "bold":
        node.bold = True
    if token.op == "italic":
        node.italic = True
    node.dirty = True
    if token.scope == "line":
        node.wrap = False
    if token.scope == "block":
        node.wrap = True


def load_config(path):
    # A run inside an `except` body is a run like any other.
    try:
        return read_file(path)
    except OSError as exc:
        if exc.errno == 2:
            report_missing(path)
        if exc.errno == 13:
            report_denied(path)
    return DEFAULTS


def normalise_level(level):
    # Card counter-example: the first body rebinds the subject, so the second
    # test is asking about a different value and chaining drops behaviour.
    if level == "warn":
        level = "warning"
    if level == "warning":
        level = level.upper()
    return level


def classify_status(code):
    # Card counter-example: every arm returns, so control never reaches the
    # later tests after a match. `elif` here changes punctuation and nothing else.
    if code == 404:
        return "missing"
    if code == 410:
        return "gone"
    if code == 451:
        return "blocked"
    return "other"


def escalate(usage, alerts):
    # Range tests against constants overlap by construction: at 95 both fire,
    # and chaining them would silently drop the second notification.
    if usage > 90:
        alerts.page_oncall()
    if usage > 75:
        alerts.record_warning()


def audit_request(request, log):
    # Different subjects, and a statement between them: nothing to chain.
    if request.method == "POST":
        log.write(request.body)
    log.flush()
    if request.scheme == "http":
        log.warn("insecure")


def search_range(nums, target):
    # `not first_exist` is already settled by falling through the first test,
    # so the second condition does work whose answer is known. That is C4.S2,
    # which no signal points at: the redundancy is in what the values mean,
    # not in the shape. This rule reads `x == const` runs and must stay quiet.
    first_exist = bool(nums) and nums[0] == target
    last_exist = bool(nums) and nums[-1] == target
    if first_exist and last_exist:
        return -1
    if last_exist and not first_exist:
        return nums[0]
    return 0


def surcharge(age, size):
    # The conditions overlap: a row can be both stale and oversized, and an
    # `elif` chain would apply only the first.
    total = 0
    if age > 30:
        total += 5
    if size > 100:
        total += 7
    if size > 1_000:
        total += 11
    return total


def advance_pipeline(task):
    # The first arm rebinds what the second tests, through an attribute --
    # which `assigned_names` cannot see. Chained, `task.execute()` never runs.
    if task.state == "QUEUED":
        task.state = "RUNNING"
    if task.state == "RUNNING":
        task.execute()


def parse_flag(val):
    # `1 == True` in Python, so these are one test written two ways and the run
    # is not exclusive. Compared as source they looked distinct.
    if val == 1:
        handle_numeric_one()
    if val == True:
        handle_boolean_true()
