"""Writes each RQ text twice from its template: plain, and annotated with sources.

For RQ1 and RQ2, reads temp_main_paper/results/rq<N>_template.tex, where
  - every number is a command such as \\rqOneSavingPct or \\rqTwoInstances (values
    in generated/numbers.json and generated/rq2_numbers.json, written by
    rq1_latex.py and rq2_latex.py), and
  - \\src{...} marks the end of one or two sentences, with a note on how the
    numbers before it were computed.

Writes, next to each template:
  rq<N>.tex             the paper's text: numbers typed in, tables pasted in,
                        every \\src{...} removed
  rq<N>_annotated.tex   the same text, where each \\src{...} becomes a note in blue
                        parentheses. For every number since the previous marker,
                        the note gives the value, what it is, the file and line it
                        was read from, and the script that wrote that file; then the
                        text inside the braces. Needs \\usepackage{xcolor}.

rq<N>.tex is written by this script, so edit the template, not rq<N>.tex. To keep
hand edits from being lost, the script stops when rq<N>.tex differs from the copy
it wrote last time (generated/rq<N>_last_render.tex).

Run after rq1_latex.py and rq2_latex.py:  python3 analysis/render_text.py
"""

import json
import re

from common import ROOT

RESULTS = ROOT / "temp_main_paper" / "results"
GENERATED = RESULTS / "generated"
TEXTS = ["rq1", "rq2"]                                  # one template each: rq1_template.tex, ...
NUMBER_FILES = ["numbers.json", "rq2_numbers.json"]     # written by rq1_latex.py and rq2_latex.py

COMMAND = re.compile(r"\\(rq(?:One|Two)[A-Za-z]+)(\{\})?")   # \rqOneName, \rqTwoName{}, ...
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
    """The text with every number command replaced by its value."""
    def value_of(match):
        name = match.group(1)
        if name not in numbers:
            raise SystemExit(f"\\{name} is not in the numbers files (add it to rq1_latex.py or rq2_latex.py)")
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


def render(name, numbers):
    """Write rq<N>.tex and rq<N>_annotated.tex from rq<N>_template.tex."""
    template = (RESULTS / f"{name}_template.tex").read_text()
    plain_file = RESULTS / f"{name}.tex"
    annotated_file = RESULTS / f"{name}_annotated.tex"
    last_file = GENERATED / f"{name}_last_render.tex"   # what this script wrote last time

    # Drop the template's own header (the comment lines at the very top)
    lines = template.splitlines(keepends=True)
    while lines and lines[0].startswith("%"):
        lines.pop(0)
    body = "".join(lines)

    plain = []                                          # pieces of rq<N>.tex
    annotated = []                                      # pieces of rq<N>_annotated.tex
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

    number = name[2:]
    header_plain = (f"% Results, RQ{number}. Written by analysis/render_text.py from {name}_template.tex;\n"
                    "% edit the template and run it again. Every number's source is in the\n"
                    f"% generated/*numbers.md files, and {name}_annotated.tex shows it after each sentence.\n")
    header_annotated = (f"% Results, RQ{number}, ANNOTATED: the text of {name}.tex with the source of every\n"
                        "% number in blue after each sentence or two. Written by analysis/render_text.py.\n"
                        "% Needs \\usepackage{xcolor}.\n")

    # Do not overwrite rq<N>.tex if someone edited it since the last render
    if plain_file.exists() and last_file.exists() and plain_file.read_text() != last_file.read_text():
        raise SystemExit(f"{plain_file} was edited by hand since the last render. Move your edits "
                         f"into {name}_template.tex, or delete {last_file} to overwrite.")

    plain_file.write_text(header_plain + plain_text)
    annotated_file.write_text(header_annotated + annotated_text)
    last_file.write_text(header_plain + plain_text)
    print("wrote", plain_file, "and", annotated_file)


def main():
    numbers = {}
    for file_name in NUMBER_FILES:                      # the numbers of every RQ
        numbers.update(json.loads((GENERATED / file_name).read_text()))
    for name in TEXTS:
        render(name, numbers)


if __name__ == "__main__":
    main()
