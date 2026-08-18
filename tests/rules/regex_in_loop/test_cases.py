"""Cases for regex_in_loop."""

import re

_ID = re.compile(r"id=(\d+)")


def extract_ids(lines):
    # A module-level cache lookup and a match per line.
    found = []
    for line in lines:
        match = re.search(r"id=(\d+)", line)
        if match:
            found.append(match.group(1))
    return found


def strip_tags(lines):
    # `re.sub` costs the same lookup as `re.search`.
    return [re.sub(r"<[^>]+>", "", line) for line in lines]


def compile_each_time(lines, pattern):
    # `re.compile` on a fixed pattern inside the loop is the plainest form.
    out = []
    for line in lines:
        matcher = re.compile(pattern)
        out.append(matcher.findall(line))
    return out


def compile_per_pattern(patterns, text):
    # The pattern *is* the loop variable, so there is nothing to hoist.
    return [re.compile(p).findall(text) for p in patterns]


def use_precompiled(lines):
    # Already hoisted to module scope.
    return [_ID.search(line) for line in lines]


def compile_then_loop(lines, pattern):
    # Compiled once above the loop.
    matcher = re.compile(pattern)
    found = []
    for line in lines:
        found.append(matcher.search(line))
    return found


def split_once(text):
    # Outside any loop.
    return re.split(r"\s+", text)
