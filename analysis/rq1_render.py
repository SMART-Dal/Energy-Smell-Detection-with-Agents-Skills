"""Writes the RQ1 text twice from one template: plain, and annotated with sources.

Reads temp_main_paper/results/rq1_template.tex, where
  - every number is a command such as \\rqOneSavingPct (values in generated/numbers.json,
    written by rq1_latex.py), and
  - \\src{...} marks the end of one or two sentences, with a note on how the
    numbers before it were computed.

Writes, next to the template:
  rq1.tex             the paper's text: numbers typed in, tables pasted in,
                      every \\src{...} removed
  rq1_annotated.tex   the same text, where each \\src{...} becomes a note in blue
                      parentheses. For every number since the previous marker,
                      the note gives the value, what it is, the file and line it
                      was read from, and the script that wrote that file; then the
                      text inside the braces. Needs \\usepackage{xcolor}.

rq1.tex is written by this script, so edit the template, not rq1.tex. To keep
hand edits from being lost, the script stops when rq1.tex differs from the copy
it wrote last time (generated/rq1_last_render.tex).

Run after rq1_latex.py:  python3 analysis/rq1_render.py
"""

import json
import re

from common import ROOT

RESULTS = ROOT / "temp_main_paper" / "results"
GENERATED = RESULTS / "generated"
TEMPLATE = RESULTS / "rq1_template.tex"
PLAIN = RESULTS / "rq1.tex"
ANNOTATED = RESULTS / "rq1_annotated.tex"
LAST = GENERATED / "rq1_last_render.tex"          # what this script wrote last time

COMMAND = re.compile(r"\\(rqOne[A-Za-z]+)(\{\})?")  # \rqOneName or \rqOneName{}
TABLE = re.compile(r"\\input\{results/generated/(table_\w+)\}")


def escaped(text):
    """Plain text made safe for LaTeX (for the notes, which name files and functions)."""
    special = {"\\": r"\textbackslash{}", "_": r"\_", "%": r"\%", "&": r"\&", "#": r"\#",
               "$": r"\$", "~": r"\textasciitilde{}", "{": r"\{", "}": r"\}"}
    result = ""
    for character in text:                              # one character at a time, so no
        result = result + special.get(character, character)   # replacement is replaced again
    return result


def split_on_markers(template):
    """The template as a list of ("text", ...) and ("src", note) pieces, in order.

    A marker is \\src{...}; the note may contain balanced braces.
    """
    pieces = []
    position = 0
    while True:
        start = template.find("\\src{", position)
        if start == -1:                                 # no more markers
            pieces.append(("text", template[position:]))
            return pieces
        pieces.append(("text", template[position:start]))
        depth = 0                                       # find the brace that closes this marker
        index = start + len("\\src")
        while True:
            if template[index] == "{":
                depth = depth + 1
            elif template[index] == "}":
                depth = depth - 1
                if depth == 0:
                    break
            index = index + 1
        pieces.append(("src", template[start + len("\\src{"):index]))
        position = index + 1


def with_numbers(text, numbers):
    """The text with every \\rqOne command replaced by its value."""
    def value_of(match):
        name = match.group(1)
        if name not in numbers:
            raise SystemExit(f"\\{name} is not in numbers.json (add it to rq1_latex.py)")
        return numbers[name]["value"]
    return COMMAND.sub(value_of, text)


def with_tables(text):
    """The text with each \\input of a generated table replaced by the table itself."""
    def table_of(match):
        return (GENERATED / (match.group(1) + ".tex")).read_text().strip()
    return TABLE.sub(table_of, text)


def note(names, numbers, free_text):
    """The annotation for one marker: the source of each number, then the free text."""
    parts = []
    for name in names:
        n = numbers[name]
        parts.append(f"{n['value']} = {n['meaning']}: {n['file']} {n['line']}, written by {n['made_by']}")
    if free_text.strip():
        parts.append(free_text.strip())
    return r" {\color{blue}\footnotesize (" + escaped("; ".join(parts)) + ")}"


def main():
    numbers = json.loads((GENERATED / "numbers.json").read_text())
    template = TEMPLATE.read_text()

    # Drop the template's own header (the comment lines at the very top)
    lines = template.splitlines(keepends=True)
    while lines and lines[0].startswith("%"):
        lines.pop(0)
    body = "".join(lines)

    plain = []                                          # pieces of rq1.tex
    annotated = []                                      # pieces of rq1_annotated.tex
    since_marker = []                                   # commands used since the last marker
    for kind, content in split_on_markers(body):
        if kind == "text":
            for match in COMMAND.finditer(content):     # remember the numbers in this text
                if match.group(1) not in since_marker:
                    since_marker.append(match.group(1))
            plain.append(with_numbers(content, numbers))
            annotated.append(with_numbers(content, numbers))
        else:
            annotated.append(note(since_marker, numbers, content))
            since_marker = []
    plain_text = with_tables("".join(plain))
    annotated_text = with_tables("".join(annotated))

    # In the plain text, a marker leaves a space before the next sentence or a
    # blank line; remove a space left at the end of a line, and double spaces.
    plain_text = re.sub(r" +\n", "\n", plain_text)
    plain_text = re.sub(r"(\S)  +(\S)", r"\1 \2", plain_text)

    header_plain = ("% Results, RQ1. Written by analysis/rq1_render.py from rq1_template.tex;\n"
                    "% edit the template and run it again. Every number's source is in\n"
                    "% generated/numbers.md, and rq1_annotated.tex shows it after each sentence.\n")
    header_annotated = ("% Results, RQ1, ANNOTATED: the text of rq1.tex with the source of every\n"
                        "% number in blue after each sentence or two. Written by analysis/rq1_render.py.\n"
                        "% Needs \\usepackage{xcolor}.\n")

    # Do not overwrite rq1.tex if someone edited it since the last render
    if PLAIN.exists() and LAST.exists() and PLAIN.read_text() != LAST.read_text():
        raise SystemExit(f"{PLAIN} was edited by hand since the last render. Move your edits "
                         f"into {TEMPLATE.name}, or delete {LAST} to overwrite.")

    PLAIN.write_text(header_plain + plain_text)
    ANNOTATED.write_text(header_annotated + annotated_text)
    LAST.write_text(header_plain + plain_text)
    print("wrote", PLAIN, "and", ANNOTATED)


if __name__ == "__main__":
    main()
