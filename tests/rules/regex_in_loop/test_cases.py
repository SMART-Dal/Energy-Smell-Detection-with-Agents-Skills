"""Cases for regex_in_loop."""

import re
import re as regex
from re import search

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


def scan_with_direct_import(lines):
    # `from re import search` binds the function itself, so the call is a
    # bare name and the rule only ever looked at `re.<attr>`.
    for line in lines:
        search(r"\\d+", line)


def scan_with_keyword_args(lines):
    # The pattern is in a keyword, where `node.args[0]` finds nothing.
    for line in lines:
        re.search(pattern=r"\\d+", string=line)


def scan_with_finditer(lines):
    # `finditer` compiles exactly like `findall` and was simply not listed.
    for line in lines:
        list(re.finditer(r"\\d+", line))


def scan_with_renamed_module(lines):
    # `import re as regex` renames the module; the pattern still hoists.
    for line in lines:
        regex.search(r"\\d+", line)
