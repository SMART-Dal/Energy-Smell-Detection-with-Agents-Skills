"""Cases for filter_after_transform."""


def summarise_documents(paths):
    # Card's own repair example: every path is parsed, then most results dropped.
    parsed = [parse_document(p) for p in paths]
    return [d.title for d in parsed if d.path.suffix == ".md"]


def render_visible_cards(users):
    # Same shape through `map`: the transform is applied before the filter sees it.
    rendered = list(map(render_card, users))
    visible = [card for card in rendered if card.visible]
    visible.sort(key=lambda card: card.order)
    return visible


def weigh_records(records):
    # Laziness does not help: `normalise` still runs on every record pulled.
    converted = (normalise(r) for r in records)
    kept = [c for c in converted if c.weight > 0]
    return sum(c.weight for c in kept)


def positive_scores(rows):
    # The transform is recomputed in its own test, so it runs twice per survivor.
    return [score(row) for row in rows if score(row) > 0]


def format_present_values(data):
    # A comprehension's `if` runs before its element expression: already optimal.
    formatted = [format_data(x) for x in data if x is not None]
    return "\n".join(formatted)


def markdown_titles(paths):
    # Filter first, transform after -- this is what the repaired code looks like.
    wanted = [p for p in paths if p.suffix == ".md"]
    return [parse_document(p).title for p in wanted]


def report_parsed(paths):
    # The whole transformed list is needed as well, so the filter cannot move up.
    parsed = [parse_document(p) for p in paths]
    log_total(len(parsed))
    published = [d.title for d in parsed if d.published]
    return published


def collect_row_values(rows):
    # The element expression is an attribute read, not a call: nothing to save.
    values = [r.value for r in rows]
    present = [v for v in values if v is not None]
    return present


def bucket_open_orders(orders):
    # A plain filter over a parameter nothing transformed beforehand.
    selected = [o for o in orders if o.status == "open"]
    for order in selected:
        order.mark_seen()
    return selected


def normalise_then_index(records):
    # Transform then consume, but the consumer has no filter at all.
    converted = [normalise(r) for r in records]
    return {c.key: c for c in converted}


def closes(candles):
    # Tested and kept, but the test is a dict probe: nothing to compute once.
    return [item.get("close") for item in candles if item.get("close") is not None]
