# Inputs for test/test.py::parse_page, generated outside the session: the 4 most
# expensive of 8 candidates that ran and repeated on the original.

import random

# ---------------------------------------------------------------- data pools

_CMDS = [
    "vespa config set target local",
    "docker run --detach --name vespa --hostname vespa-container --publish 8080:8080 --publish 19071:19071 vespaengine/vespa",
    "vespa status deploy --wait 300",
    "vespa deploy --wait 300 ./app",
    "vespa clone album-recommendation myapp",
    "echo hello world",
    "sleep 2",
    "cat app/services.xml",
    "vespa document put id:music:music::1",
    "vespa query yql select from music where true",
    "ls -la /tmp",
    "pwd",
    "python3 -m json.tool data.json",
    "vespa visit --cluster music",
    "vespa destroy",
]


def _rand_lines(rng, n):
    out = []
    for _ in range(n):
        r = rng.random()
        if r < 0.08:
            out.append(_CMDS[rng.randrange(len(_CMDS))] + " \\")
        elif r < 0.12:
            out.append("")
        else:
            out.append(_CMDS[rng.randrange(len(_CMDS))])
    return out


def _pre_block(rng, kind, nlines, extra=""):
    body = "\n".join(_rand_lines(rng, nlines))
    return '<pre data-test="%s"%s>\n%s\n</pre>\n' % (kind, extra, body)


def _file_block(path, body):
    return '<div data-test="file" data-path="%s">\n%s\n</div>\n' % (path, body)


# ---------------------------------------------------------------- case bodies

def _build_all():
    data = {}

    # 1) one very large exec block
    rng = random.Random(101)
    data["big-exec"] = (
        '<html><body>\n<pre data-test="exec">\n'
        + "\n".join(_rand_lines(rng, 4000))
        + "\n</pre>\n</body></html>\n"
    )

    # 2) many small exec blocks (lots of tags to scan and parse)
    rng = random.Random(102)
    parts = ["<html><body>\n"]
    for _ in range(500):
        parts.append(_pre_block(rng, "exec", 8))
    parts.append("</body></html>\n")
    data["many-exec"] = "".join(parts)

    # 3) before + after sections only
    rng = random.Random(103)
    parts = ["<html><body>\n"]
    for _ in range(3):
        parts.append(_pre_block(rng, "before", 500))
        parts.append(_pre_block(rng, "after", 500))
    parts.append("</body></html>\n")
    data["before-after"] = "".join(parts)

    # 4) file elements, plain text and nested markup
    rng = random.Random(104)
    parts = ["<html><body>\n"]
    for i in range(300):
        body = "\n".join(_rand_lines(rng, 6))
        parts.append(_file_block("app/config/file_%d.xml" % i, body))
    for i in range(50):
        parts.append(
            '<div data-test="file" data-path="app/services/service_%d.xml">\n'
            '<services><content id="c%d">hello world</content></services>\n'
            "</div>\n" % (i, i)
        )
    parts.append("</body></html>\n")
    data["files"] = "".join(parts)

    # 5) run-macro elements (both spaced and unspaced spellings)
    parts = ["<html><body>\n"]
    for i in range(300):
        parts.append(
            '<pre data-test="run-macro init-deploy app%d">\n$ vespa deploy\n</pre>\n'
            % (i % 13)
        )
    for i in range(100):
        parts.append('<pre data-test="run-macroinit-deploy up%d">\n</pre>\n' % i)
    parts.append("</body></html>\n")
    data["run-macro"] = "".join(parts)

    # 6) realistic mixed page
    rng = random.Random(106)
    parts = ["<html><body>\n"]
    parts.append(_pre_block(rng, "before", 300))
    for _ in range(200):
        parts.append(_pre_block(rng, "exec", 5, ' data-assert="true"'))
    parts.append('<pre data-test="run-macro init-deploy myapp">\n</pre>\n')
    for i in range(100):
        parts.append(_file_block("app/data/f%d.json" % i, "{}"))
    parts.append(_pre_block(rng, "after", 300))
    parts.append("</body></html>\n")
    data["mixed"] = "".join(parts)

    # 7) heavy line-continuation workload
    rng = random.Random(107)
    lines = []
    for i in range(2000):
        if i % 3 == 0:
            lines.append(_CMDS[rng.randrange(len(_CMDS))] + " \\")
        else:
            lines.append(_CMDS[rng.randrange(len(_CMDS))])
    data["continuations"] = (
        '<html><body>\n<pre data-test="exec">\n'
        + "\n".join(lines)
        + "\n</pre>\n</body></html>\n"
    )

    # 8) large document, very few matching elements
    rng = random.Random(108)
    tag_names = ["div", "p", "span", "a", "li", "section"]
    parts = ["<html><body>\n"]
    for i in range(6000):
        t = tag_names[rng.randrange(len(tag_names))]
        parts.append('<%s class="c%d">item %d</%s>\n' % (t, i % 7, i, t))
    for i in range(50):
        parts.append(
            '<div data-test="exec">\n%s\n</div>\n' % _CMDS[i % len(_CMDS)]
        )
    parts.append("</body></html>\n")
    data["large-few-match"] = "".join(parts)

    return data


_DATA = _build_all()


# ---------------------------------------------------------------- tests

def checks():
    return [
        ("empty", lambda: ("",)),
        ("no-match", lambda: ("<html><body><p>hello</p><div>world</div></body></html>",)),
        ("file-no-path", lambda: ('<div data-test="file">content</div>',)),
    ]


def cases():
    d = _DATA
    return [
        ("big-exec", lambda: (d["big-exec"],)),
        ("many-exec", lambda: (d["many-exec"],)),
        ("before-after", lambda: (d["before-after"],)),
        ("files", lambda: (d["files"],)),
        ("run-macro", lambda: (d["run-macro"],)),
        ("mixed", lambda: (d["mixed"],)),
        ("continuations", lambda: (d["continuations"],)),
        ("large-few-match", lambda: (d["large-few-match"],)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['large-few-match', 'many-exec', 'files', 'run-macro']
_KEEP_CHECKS = ['empty', 'no-match', 'file-no-path']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
