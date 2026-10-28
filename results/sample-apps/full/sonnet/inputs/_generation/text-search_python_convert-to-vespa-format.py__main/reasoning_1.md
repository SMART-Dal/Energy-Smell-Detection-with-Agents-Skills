Let me understand the module. The file `convert-to-vespa-format.py` at module level presumably defines `source_dir`, `dest_dir`, `fields`, `sample_offset_file`, `doc_type` from command line args or environment. We need to import it via importlib. But importing it executes module-level code which likely parses sys.argv. Let's think.

The function `main()` takes no arguments. It reads module globals: `docs_file`, `out_file`, `fields`, `doc_type`, `sample_offset_file` (used by load_document_offsets), and `source_dir`, `dest_dir`.

We need to set up these globals on the repository's own module (the imported module). We import with importlib.import_module('convert-to-vespa-format'). The module needs to be on sys.path — the file is at `text-search/python/convert-to-vespa-format.py`. We must add that directory to sys.path in module-level code (that's setup, not timed; and it's allowed since it's like a caller adding a path).

But importing the module executes its top-level code. Let's guess what that top-level code looks like. The snippet shows:

```
fields = fields.split(",")
docs_file = os.path.join(source_dir, "docs.tsv")
out_file = os.path.join(dest_dir, "documents.jsonl")
```

So earlier there must be definitions of `source_dir`, `dest_dir`, `fields`, `sample_offset_file`, `doc_type`. Likely parsed from sys.argv. Let me recall the sample-apps repo: text-search/python/convert-to-vespa-format.py.

Probably something like:

```python
import os
import io
import sys
import csv
import json

source_dir = sys.argv[1]
dest_dir = sys.argv[2]
fields = sys.argv[3]
sample_offset_file = sys.argv[4]
doc_type = sys.argv[5]
...
```

Hmm, we don't know exactly. The task says: "Import the repository's modules exactly as shown in the task. Use only the standard library, the repository itself and packages the repository already imports. Everything you can know about the repository is in the task."

But we don't see the argument parsing. Risky. However, importing requires the module to import successfully. If it reads sys.argv at import time and there's no argv, it will raise IndexError.

We could set sys.argv before importing. That's module-level setup. Let's try to guess the argument structure.

Actually let me think about the actual repo. The sample-apps repo by vespa-engine. There's a text-search sample app. The script convert-to-vespa-format.py. Let me try to recall... I think it's:

```python
import os
import io
import sys
import csv
import json

# ... 

def load_document_offsets():
    ...
```

Actually the top might be:

```python
source_dir = sys.argv[1]
dest_dir = sys.argv[2]
fields = sys.argv[3]
doc_type = sys.argv[4]
sample_offset_file = os.path.join(source_dir, "sample-offsets.tsv")  # ?
```

Hmm. The task gives us these globals used: `docs_file`, `out_file`, `fields`, `doc_type`, `sample_offset_file`, `source_dir`, `dest_dir`.

Since we can't know exactly, maybe the safest approach: we set the module attributes after import, so their values don't matter. But import-time parsing of sys.argv might still fail.

Alternative: import the module with sys.argv set to plausible values. We can set sys.argv = ['convert-to-vespa-format.py', 'sourcedir', 'destdir', 'field1,field2', 'doc', 'offsetfile'] — but if the order/meaning differs, values just end up wrong, which is fine because we override them afterwards.

But if it's not sys.argv-based... Maybe it uses argparse with required args, which would call sys.exit on failure. Setting sys.argv appropriately helps.

Hmm, but if argparse has a specific number of required arguments, we need the right count. Unknown.

Let me think harder about the actual code. Let me try to recall the Vespa sample-apps text-search script. I believe it's something like:

```python
import os
import io
import sys
import csv
import json

def main():
    ...

if __name__ == "__main__":
    main()
```

But where do globals come from? The snippet shows `fields = fields.split(",")` at module level — meaning `fields` is defined before as a string. So probably:

```python
source_dir = "data"  # or from argv
```

Hmm.

Maybe it's actually something like:

```python
source_dir = sys.argv[1]
dest_dir = sys.argv[2]
fields = sys.argv[3]
sample_offset_file = sys.argv[4]
doc_type = sys.argv[5]
```

Let me search memory: I think there's a version where they do:

```python
def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir")
    ...
```

I really don't know.

Given the constraints, maybe the best approach is to write robust code that tries to import and, if it fails, ... but we can't catch and fake. Actually we could catch exceptions from import? The instructions say the import should be as shown. Hmm, but if the module raises at import, we cannot proceed.

Alternative approach: set sys.argv generously with many arguments, so any positional indexing works. argparse would reject unknown extra args though (it would error). But argparse errors call parser.error → sys.exit(2). That would break import.

Hmm. Let's consider: maybe the module-level code is:

```python
if len(sys.argv) != 6:
    print("Usage: ...")
    sys.exit(1)
```

Then with 6 args it works.

Let me try to find the actual file content from memory more concretely. The sample-apps repo path: `text-search/python/convert-to-vespa-format.py`. I have some recollection of a blog post about Vespa text search sample app using MS MARCO dataset. The script converts a TSV to Vespa JSON format.

I believe the top of the file is:

```python
import os
import io
import sys
import csv
import json

source_dir = sys.argv[1]
dest_dir = sys.argv[2]
fields = sys.argv[3]
sample_offset_file = os.path.join(source_dir, sys.argv[4])
doc_type = sys.argv[5]
```

Hmm, honestly uncertain.

Wait — the task says "Import it as `main = importlib.import_module('convert-to-vespa-format').main`". This implies the import works in the grading harness environment. But the harness runs OUR code, which does the import. So the import must work given whatever sys.argv is at that time... Actually in the harness, sys.argv is whatever the test runner has. That would likely fail too. Unless the module doesn't parse argv at import.

Hmm, maybe the module reads from environment or has defaults. Let's reconsider: maybe the top-level is:

```python
source_dir = "msmarco"  
dest_dir = "vespa"
fields = "id,title,body"
```

No...

Actually, maybe the file uses `sys.argv` inside `if __name__ == "__main__"`? But the snippet shows `fields = fields.split(",")` and `docs_file = os.path.join(source_dir, ...)` at module level (no indentation shown). The task's "Definitions it uses from the same module" section lists these at top level presumably.

Hmm, but maybe those lines are actually inside main()? No — the given main() body doesn't include them, and they're listed separately as module definitions.

Let me reconsider. Perhaps the actual script structure is:

```python
import os
import io
import sys
import csv
import json

if len(sys.argv) < 6:
    print("Usage: python convert-to-vespa-format.py <source_dir> <dest_dir> <fields> <doc_type> <sample_offset_file>")
    sys.exit(1)

source_dir = sys.argv[1]
dest_dir = sys.argv[2]
fields = sys.argv[3]
doc_type = sys.argv[4]
sample_offset_file = sys.argv[5]

fields = fields.split(",")

docs_file = os.path.join(source_dir, "docs.tsv")
out_file = os.path.join(dest_dir, "documents.jsonl")

def load_document_offsets():
    ...
```

If it's a `len(sys.argv) < 6` check with sys.exit, then setting sys.argv with 6+ elements works.

I think I should set sys.argv before importing to a 6-element list, and also set defaults so that if it uses argparse... hmm.

Actually wait. There's a simpler consideration: maybe I should just try importing and if it fails, that's the harness's problem. But we want to write working code.

Let me try to actually recall the file. I'll think about the MS MARCO dataset: there's `collection.tsv` and `queries.tsv`, `qrels.dev.small.tsv`. But this script uses `docs.tsv` and offsets. Hmm, this looks like the "text search" sample with a different dataset — maybe it's the Vespa sample apps "text-search" which uses the "msmarco" or "cord19"? Actually I recall a script in sample-apps for converting to Vespa format that reads a TSV with offsets generated by a previous step.

Let me look at the naming: `load_document_offsets`, `sample_offset_file`, `docs_file`, `doc_type`. There's probably also a companion script that creates offsets.

I recall the sample-apps "text-search" tutorial uses the "MS MARCO" passage ranking... hmm.

Honestly, I'll take the pragmatic approach: set sys.argv to a list of 6 strings before importing, and also handle the possibility that the module reads specific arg names. Since we override module globals after import, wrong values don't matter.

But if the module uses argparse with named args, setting sys.argv positionally could fail. To hedge, we could try multiple import strategies... but instructions say "Import the repository's modules exactly as shown in the task." So `importlib.import_module('convert-to-vespa-format')`. We can still set sys.argv before.

Hmm, what if it's argparse with positional args and it errors out on wrong count? We can't know.

Let me try another angle: search my memory of the actual repository file content. The sample-apps repo... `text-search/python/convert-to-vespa-format.py`:

```python
import os
import io
import sys
import csv
import json


def main():
    document_offsets = load_document_offsets()
    ...
```

Hmm and maybe the globals are defined via `sys.argv` but guarded:

Actually, you know what, maybe the module has:

```python
if len(sys.argv) != 6:
    print("Usage: ...")
    sys.exit(1)

source_dir = sys.argv[1]
...
```

I'm fairly confident about the sys.argv pattern given the style (it uses `io.open`, `sys`). The presence of `sys` import strongly suggests sys.argv usage.

Let me just go with: `sys.argv = ['convert-to-vespa-format.py', src, dest, 'id,title,body', 'doc_type', offset_file]`? But we don't know order. Hmm, but it doesn't matter for values; what matters is the count. If it's `len(sys.argv) != 6` we need exactly 6.

But what if the check is `if len(sys.argv) < 6`? Then more is fine.

Risk: exact-count check with wrong count → exit. Let's pick 6 total (script + 5 args). Given 5 globals derived from args (source_dir, dest_dir, fields, doc_type, sample_offset_file), that's 5 args. So 6 total. Good guess.

Hmm, but maybe sample_offset_file is derived, not an arg. Then 4 args.

Alternatively, maybe the module uses environment variables... unlikely.

Another thought: maybe the harness for this task expects us to just write it and the import will happen with the harness's sys.argv which might already be set... no.

Let me think about whether there's a way to make this robust. We could do the import inside a try/except and, on failure, re-execute the module source with a patched sys.argv. But that's hacky and the instruction says no monkeypatching... Actually setting sys.argv is not monkeypatching the function. Re-executing the module manually with a different argv is questionable but arguably "preparing the way the repository's own callers do".

Hmm, but the import must be as shown. Let's do:

```python
import sys, os
sys.path.insert(0, str(WORKDIR / "repo"))  # hmm, we need the actual path
```

Wait, we need the path to the file: `text-search/python/convert-to-vespa-format.py`. The repository root is presumably the current working directory? The task says WORKDIR is provided and files we create go under WORKDIR. The repository itself — where is it? Probably the CWD is the repository root, or the repo is checked out somewhere.

Typical setup in these tasks: the repo is at some path, maybe cwd. The instruction "Prepare the way the repository's own callers do: if a caller runs some setup before calling the function (adds a path, loads a config), do the same in the thunk." So we should add `text-search/python` to sys.path.

We can use a relative path: `sys.path.insert(0, "text-search/python")` — but if cwd isn't repo root, fails. Could use `os.path.dirname(...)`? We don't know. Perhaps the repo is at cwd. Many of these tasks have the repo root as cwd.

Hmm, safer: search for the file. But that's complex. Let's just add a few candidate paths relative to cwd, and also try to locate via `__file__` of... we have no reference.

I think cwd = repo root is the standard assumption. Let's do:

```python
import sys, os
_repo_py = os.path.join(os.getcwd(), "text-search", "python")
if os.path.isdir(_repo_py):
    sys.path.insert(0, _repo_py)
else:
    sys.path.insert(0, "text-search/python")
```

Hmm. Alternatively maybe the repo is available as a package? No.

Actually, wait. Maybe these tasks place the repository at cwd. I'll assume cwd is repo root and the relative path `text-search/python` works.

Now the big question: module-level code execution. Let me just set sys.argv before import with 6 entries.

Actually — better idea: maybe the module's arg parsing is inside `if __name__ == "__main__":`? But then globals would be undefined at import... unless they're defined in the block before main is called. Since the snippet shows the `if __name__ == "__main__": main()` at line 68 and module-level definitions, the globals must be defined at module level (before main). So argv parsing at module level.

Let me write:

```python
import importlib, os, sys, io, json, csv, random

sys.path.insert(0, os.path.join(os.getcwd(), "text-search", "python"))
# also fallback
sys.argv = ["convert-to-vespa-format.py", "src", "dest", "id,title,body", "doc", "offsets.tsv"]
main_mod = importlib.import_module("convert-to-vespa-format")
main = main_mod.main
```

But careful: `importlib.import_module` with a hyphenated name works? Yes, it works — the name is just a key in sys.modules; import machinery finds the file via FileFinder. Actually, does it? `import_module("convert-to-vespa-format")` — the finder looks for `convert-to-vespa-format.py` in sys.path entries. Yes, FileFinder can find files with any name ending in .py. Actually the module name validity: importlib.import_module doesn't validate the name; it uses _bootstrap._find_and_load which uses the path finders. The finder's `find_spec` with name "convert-to-vespa-format" → it computes `tail_module = "convert-to-vespa-format"`, and checks for `convert-to-vespa-format.py`. Should work. Yes, this pattern is used in these tasks.

Now after import, override globals:

```python
main_mod.source_dir = str(SRC_DIR)
main_mod.dest_dir = str(DEST_DIR)
main_mod.fields = ["docid", "title", "body"]  # already split list
main_mod.docs_file = str(SRC_DIR / "docs.tsv")
main_mod.out_file = str(DEST_DIR / "documents.jsonl")
main_mod.sample_offset_file = str(SRC_DIR / "sample_offsets.tsv")
main_mod.doc_type = "doc"
```

Wait, `fields = fields.split(",")` at module level → `fields` is a list. So main_mod.fields must be a list of field names. And `doc_type` is a string.

`load_document_offsets` reads `sample_offset_file` (module global) with csv reader, delimiter tab, expects exactly 2 columns per row ([docid, offset]).

main() reads `docs_file` in text mode with utf-8, seeks to offsets, reads a line, strips, splits by tab. content[0] must equal docid. len(content) must equal len(fields). Then writes JSON.

Note: `open(out_file, "w")` — default encoding, but on Linux that's utf-8 typically. Fine.

Important: main() writes to out_file each call. Since we call many times, and the file is overwritten each time ("w"), it's fine — same work each call. But the instructions say "Anything the function writes must go under WORKDIR too." So out_file under WORKDIR. Good. Actually it says files the function reads go under WORKDIR too. So put source dir under WORKDIR.

But careful: the args rendered before/after each call — main takes no args, so nothing to compare. Outputs: main returns None. The comparison is on the output file? "The function's output is compared in full after every input" — main returns None, so output is None. Hmm, but the file is written. The harness might compare... Probably it compares the return value (None). Anyway, keep it deterministic.

Actually the comparison likely captures stdout and return value. main writes to a file. Since the file is overwritten identically each call, fine.

Now design the workload.

`docs.tsv`: tab-separated lines: docid \t field1 \t field2 ... The number of columns must equal len(fields).

`sample_offsets.tsv` (or whatever sample_offset_file is): lines `docid\toffset`, where offset is the byte offset of the docid line in docs.tsv.

Note: `f.seek(offset)` in text mode with utf-8 — offsets must be byte offsets. For ASCII content, byte offset == char offset. To be safe, use ASCII content. Actually with utf-8 and text mode, seek to arbitrary byte offset is allowed if offset is from tell() or 0. Hmm, actually TextIOWrapper.seek accepts any offset but decodes from there. It's fine for ASCII.

But wait — if content includes non-ASCII, seek byte offset works but the cookie thing... In Python 3, `f.seek(n)` on a text file is allowed with any n (it just seeks in the underlying binary buffer and resets the decoder). Actually TextIOWrapper.seek raises ValueError for non-zero positions not from tell() only in some cases? Let me recall: `TextIOWrapper.seek(cookie)` — for arbitrary offsets it's allowed; the restriction about cookies applies to `seek` with whence=1 or 2? Actually the docs say: "The offset must be either zero or the result of a previous call to tell(). Any other offset value will raise ValueError." Hmm, wait that's for... let me recall.

Actually yes! In Python 3, TextIOWrapper.seek: "Note that it's already possible to seek a text file to a byte offset obtained from tell()". Let me check: The documentation for io.TextIOBase.seek says nothing special. But TextIOWrapper.seek docs: "Change the stream position to the given byte offset... The offset must be a number returned by tell()... " Hmm.

Actually I recall ValueError "negative seek" and also that seeking to arbitrary positions in text mode is allowed but can produce incorrect decoding. Let me recall precisely: In CPython, `_io.TextIOWrapper.seek(pos, whence=0)` — for whence=0, it does `self.buffer.seek(pos, 0)`, then `self._reset_decoder()`... Actually no, it may raise "ValueError: Invalid argument" for negative.

Hmm, actually I'm fairly sure arbitrary byte offsets work in text mode with utf-8 for seeking to a line start. Let me think: the code in the repo does exactly this, so it must work in practice. The repo presumably runs it. So fine.

But there's a subtlety: for utf-8, seeking to a byte offset that's in the middle of a multibyte char causes issues. The repo uses ASCII-ish data probably. I'll use ASCII to be safe. Actually, I could include some non-ASCII to make it realistic... but risky. Use ASCII.

Hmm, but actually, let me reconsider: the docs say "offset must be either zero or the result of a previous call to tell()". If that were enforced, the repo code would fail. Since the repo works, either it's not enforced or the data is such that... Actually I now recall CPython's TextIOWrapper.seek does NOT enforce that; it just seeks the buffer and resets the decoder state. The restriction is that if you're in the middle of reading a multibyte sequence... Let me just test mentally: `open('f.txt').seek(5)` — works fine. Yes, I'm confident arbitrary seeks work.

OK. Now, realistic scale. MS MARCO-like: docids are integers as strings, fields maybe "id,title,body" or similar. Let's make docs with a few fields.

Design: fields = "docid,title,body" (3 fields). Each line: docid\ttitle\tbody. Content must have exactly 3 tab-separated parts.

Realistic: ~1000-5000 docs. Each line maybe 200-500 bytes. main() per call does: read offsets (parsing the offsets file with csv), then for each docid seek+readline+split+json.dump. So work is proportional to number of docs.

To get 1ms-200ms: 5000 docs * (json.dump of ~400 bytes) ≈ maybe 20-50ms. Let's aim for a few thousand docs.

Cases: 8 measured inputs. But main() takes no arguments — all the variation is in the files! Since the thunk must build the args... main takes no args, so thunk returns `()`. But the files must differ per case? That's tricky: files are shared module state. If we change files per case, the thunk can rewrite the files. But then all cases share the same module globals (docs_file etc.) unless we change them per thunk.

Hmm. The thunk can set module globals? The instruction says setup in the thunk or module-level. The thunk runs before timing. So a thunk could rewrite the files and set main_mod.docs_file etc. But "the call is repeated many times, and every call gets the arguments of its own thunk call" — the thunk runs once per call? Actually the harness calls the thunk before each timed call presumably. Hmm, "Thunks run before the timing starts; only the call of the function is timed." And "The call is repeated many times ... every call gets the arguments of its own thunk call". So the thunk is called each repetition. So the thunk must be cheap.

So for main(), the thunk returns `()`, and the files/globals are set at module level. To have 8 distinct cases, we'd need 8 distinct file sets... but each case's thunk must produce the same work each call. We can have multiple file sets and each thunk sets the globals to point to its own set. But thunks setting globals — is that allowed? Setting module attributes is data setup, allowed ("Setting data (a module's configuration, an object's fields) to build an input is fine"). But doing it in the thunk each time is fine too, as long as it's cheap.

Hmm, but careful: the harness might run all 8 cases, then keep the top 4 and re-run. Changing globals in the thunk is fine.

But actually there's a subtlety: is it OK for a thunk to have side effects on the module? The timing only measures main(). Setting globals is cheap. I think it's fine.

Alternatively, simpler: make each thunk rewrite the files. But rewriting a file with thousands of lines is expensive (~ms), and it's setup (not timed) — but it must happen each repetition, and it's fine as long as it's fast relative to... well, it's not timed, so no constraint except total runtime. Hmm, but total runtime: if each call takes 20ms and the thunk takes 10ms, and we run many repetitions... acceptable.

Better: pre-generate all data at module level, and thunks just point globals to pre-existing files. That's cheapest.

But wait — can we pre-create 8 different docs files? Yes, under WORKDIR.

Hmm, but actually simpler: since the function's behavior depends only on the files, and the "input" is the file state, different cases = different file sets. Let's create 8 (or fewer, say 4-8) dataset variants at module level, each with its own source dir, offsets file, docs file, and out file. Thunk sets main_mod globals and returns ().

Hmm, but out_file must be writable and distinct per case to avoid interference? Not necessary — but if two cases use the same out_file, it's fine since it's overwritten. Actually it doesn't matter.

Wait, but there's another consideration: the harness compares outputs. main returns None. The "output" might include the file content? Probably not; probably return value. Let's not worry.

Let me now think about what variation to create:

1. Typical: 2000 docs, 3 fields, medium length.
2. Large: 8000 docs.
3. Long fields: 1000 docs with very long body (e.g., 2000 chars).
4. Many fields: fields = docid,f1..f10, 2000 docs.
5. Sparse offsets: offsets file containing docids not in order / with duplicates? Actually load_document_offsets builds a dict keyed by docid; main iterates keys in insertion order. If the offsets file has duplicate docids, later overrides earlier but order is first occurrence. Hmm.
6. Missing fields / mismatched docid: docs where some lines have wrong content → `continue`. This exercises the skip paths. But note: the offsets must still point to lines. We can create a docs.tsv where some lines have fewer fields, so len(content) != len(fields) → skip. And some where content[0] != docid → skip.
7. Small: 200 docs.
8. Unicode? Skip.

Note the "work" measure: "We run them on the original function and keep the 4 that do the most work." So the harness picks top 4 by some measure (probably time/energy). So cases can vary in size.

But careful: if all cases are similar, fine.

Now: the checks() — 2-3 small edge inputs, never measured, may raise. E.g., empty offsets file → main writes just "\n" to out. Or offsets file with a docid whose offset is 0... Or empty docs file. Or offsets file missing (raises FileNotFoundError). Or a docid not found in docs (content[0] != docid → continue).

Since main takes no args, the "input" is the file state. checks() thunks set globals to edge-case files.

Let me now write the code.

Structure:

```python
import importlib
import io
import json
import os
import random
import sys

# Locate the repository's python dir
_REPO = os.getcwd()
_PYDIR = os.path.join(_REPO, "text-search", "python")
if not os.path.isdir(_PYDIR):
    # try a few alternatives
    for cand in ("text-search/python", "sample-apps/text-search/python"):
        if os.path.isdir(cand):
            _PYDIR = os.path.abspath(cand)
            break
sys.path.insert(0, _PYDIR)

# The module parses sys.argv at import time.
sys.argv = ["convert-to-vespa-format.py", str(WORKDIR / "src"), str(WORKDIR / "dest"),
            "docid,title,body", "doc", str(WORKDIR / "src" / "sample_offsets.tsv")]

_mod = importlib.import_module("convert-to-vespa-format")
main = _mod.main
```

Hmm wait — WORKDIR is provided. Is it available at module level? Yes, "WORKDIR (a provided pathlib.Path; do not define it)". It's a global provided to us.

Now, the concern: `_mod.main` — the function reads module globals of `_mod`. Good.

But the `__main__` guard: when imported as "convert-to-vespa-format", `__name__` is "convert-to-vespa-format", so main() is not called at import. Good.

Now, if the module-level code has an exact sys.argv length check, we need the right count. Let's think about the most likely. Given 5 globals: source_dir, dest_dir, fields, doc_type, sample_offset_file... but maybe sample_offset_file is `os.path.join(source_dir, sys.argv[4])`. Hmm.

I'll go with 5 args. Actually, to hedge against `len(sys.argv) != N`, what if we can't know? Hmm.

Alternative hedge: wrap the import in try/except and try different argv lengths? That's ugly but robust. Let's do:

```python
def _import_main():
    import importlib
    attempts = [...]
```

But instructions say import exactly as shown. I'll do the simple thing but with a fallback:

Actually, let's just do it directly with 5 args and hope. Hmm, risky.

Let me try to actually recall the file. Search memory: "convert-to-vespa-format.py" ... I have a vague memory of:

```python
import os
import io
import sys
import csv
import json

if len(sys.argv) < 6:
    print("Usage: python3 convert-to-vespa-format.py <source_dir> <dest_dir> <fields> <doc_type> <sample_offset_file>")
    sys.exit(1)

source_dir = sys.argv[1]
dest_dir = sys.argv[2]
fields = sys.argv[3]
doc_type = sys.argv[4]
sample_offset_file = sys.argv[5]
```

Hmm, that feels plausible but I'm not certain. Actually wait — the task description's "Definitions it uses from the same module" lists:

```python
fields = fields.split(",")
docs_file = os.path.join(source_dir, "docs.tsv")
out_file = os.path.join(dest_dir, "documents.jsonl")
```

It doesn't show where source_dir/dest_dir/fields/doc_type/sample_offset_file come from. The task omits them, which is odd — maybe because they're set by argv parsing that the task author considered irrelevant? Or maybe they're defined in the parts not shown.

Hmm, if they were simple literals, the task would show them. The omission suggests they come from argv (variable) and the author expects us to set sys.argv.

Actually, hold on. Maybe they come from environment variables! The task says "Module globals the function reads must be set on the repository's own module (import pricing; pricing.args = ...)". It gives that example, implying we may need to set globals ourselves. So maybe the author expects us to set main_mod.source_dir etc. after import, and the import works because... hmm, but if the module does `source_dir = sys.argv[1]` at import, import fails without argv.

Unless the module defines them with defaults, e.g.:

```python
source_dir = sys.argv[1] if len(sys.argv) > 1 else "."
```

Unlikely.

OK here's another thought: maybe the module-level argv parsing is guarded so it doesn't crash. Or maybe the module uses `os.environ`.

I'll go with setting sys.argv to 6 elements (script + 5) before import, which handles both `< 6` and `!= 6` checks with 5 args. If it's argparse with 5 positional args, also works. If 4 args needed, `!= 6` fails... 

Hmm. Let's think about what's most defensible. The script needs: source_dir, dest_dir, fields, doc_type, and the sample offsets file. That's 5 pieces of info → 5 args. I'll go with 5.

Hmm, but maybe sample_offset_file is derived as os.path.join(source_dir, "sample-offsets.tsv")? Then 4 args. 

Let me hedge with a try/except fallback:

```python
def _do_import():
    import importlib
    global main
    for args in (
        ["convert-to-vespa-format.py", src, dest, "docid,title,body", "doc", off],
        ["convert-to-vespa-format.py", src, dest, "docid,title,body", off, "doc"],
        ["convert-to-vespa-format.py", src, dest, "docid,title,body", "doc"],
        ["convert-to-vespa-format.py", src, dest, "docid,title,body"],
    ):
        sys.argv = args
        try:
            mod = importlib.import_module("convert-to-vespa-format")
            return mod
        except SystemExit:
            sys.modules.pop("convert-to-vespa-format", None)
            continue
    raise ...
```

This is reasonable setup code, not monkeypatching. But it's a bit gross. Hmm. But it increases robustness a lot. However, if the module prints usage and exits, SystemExit is raised — catchable. If IndexError, catchable too.

But careful: if import partially succeeds (module executed, added to sys.modules, then raised), we must remove from sys.modules before retrying. Actually `import_module` on failure removes the module from sys.modules itself? In Python 3, if the module body raises, `_bootstrap._load` removes it from sys.modules. Yes. So no need.

I think a fallback loop is pragmatic and safe. But is it "cheating"? No, it's just setting sys.argv. Fine.

But hold on — the check might be `if len(sys.argv) != 6: sys.exit(1)` with a specific order. With 5 args in the wrong order, the import succeeds but with swapped values (e.g., doc_type="offsets.tsv"). Then we override all globals afterwards, so values don't matter! Only the count matters. 

So the loop tries counts 5, 5(swapped), 4, 4... but really we need to try different counts. Let me simplify: try argv lists of length 6 (5 args) and length 5 (4 args) and length 4 (3 args).

Actually, we should also consider the possibility of `if len(sys.argv) < 6` which accepts more. So trying the largest first is good.

Let me write:

```python
_ARGV_CANDIDATES = [
    ["x", SRC, DEST, "docid,title,body", "doc", OFF],
    ["x", SRC, DEST, "docid,title,body", "doc"],
    ["x", SRC, DEST, "docid,title,body"],
    ["x", SRC, DEST],
    ["x", SRC],
]
```

Try each, catching SystemExit/IndexError/ValueError.

Hmm, but there's a risk: if the module uses argparse with positional args and errors, it calls sys.exit(2) → SystemExit. Caught.

OK. But also, importing multiple times executes module code repeatedly — fine.

Wait, one more risk: what if the module-level code actually opens/reads files at import? Unlikely given the function structure.

Now, after import, we set globals on `_mod`:

```python
_mod.source_dir = ...
_mod.dest_dir = ...
_mod.docs_file = ...
_mod.out_file = ...
_mod.fields = [...]
_mod.doc_type = ...
_mod.sample_offset_file = ...
```

Note: if the module computed `docs_file = os.path.join(source_dir, "docs.tsv")` at import, we just override docs_file directly. Good.

But careful: `load_document_offsets` uses `sample_offset_file` global — we override it. Good.

Now: what if the module doesn't define `doc_type` at module level but main uses it — then AttributeError. We set it, so fine.

Now the data generation.

Let me define a helper to build a dataset:

```python
def _make_dataset(name, docids, fields, rng, title_len, body_len, skip_ratio=0.0):
    src = WORKDIR / name
    src.mkdir(parents=True, exist_ok=True)
    docs_path = src / "docs.tsv"
    off_path = src / "sample_offsets.tsv"
    offsets = {}
    with open(docs_path, "wb") as f:
        for i, docid in enumerate(docids):
            pos = f.tell()
            ...
```

We need byte offsets. Write bytes. Content: docid + "\t" + title + "\t" + body + "\n".

For skip cases: some lines have fewer fields (so len(content) != len(fields)), or a wrong first column. But the offset must still point to that line.

Important: `f.seek(offset)` then `readline()`. So offset must be the byte start of the line.

Let's write offsets file as `docid\toffset\n` lines. But careful: if the offsets file contains a docid twice, dict keeps first position. Let's not do duplicates in most cases.

Also, `load_document_offsets` reads with csv.reader delimiter="\t", and unpacks `[docid, offset]` — so exactly 2 columns. If a row has 3 columns, ValueError. Keep 2.

Now, does the offset file order determine iteration order? Yes, dict preserves insertion order = file order. main iterates in that order. Doesn't matter much.

Now let's design the 8 cases:

Case A "typical": 3000 docs, fields=docid,title,body; title ~40 chars, body ~300 chars.
Case B "large": 10000 docs, same fields, moderate sizes. Might be ~100ms+. Let's estimate: json.dump per doc ~ maybe 5µs, plus seek/read/split ~10µs → 15µs * 10000 = 150ms. Plus offsets load. OK, under 200ms probably. Let's use 8000.
Case C "long-body": 1500 docs, body ~2000 chars → json.dump of 2KB → ~30µs each → 45ms.
Case D "many-fields": fields with 10 fields, 3000 docs.
Case E "skips": 3000 docs but half have wrong field count or wrong docid → exercises `continue`.
Case F "small": 500 docs.
Case G "unicode"? risky with byte offsets. Let's use "long docids / long titles".
Case H "single-field": fields=docid only? Then content has 1 column; len(content)==1==len(fields). doc["fields"]["docid"] = content[0]. Works. 5000 docs, tiny lines → fast. Hmm.

Actually, maybe better to make the 8 cases diverse in field count and size.

Let me also consider: is the "work" measured per call including reading the offsets file (which has N lines)? Yes, load_document_offsets is called inside main each time. So offsets file size also matters.

Let's think about the check for "dataset has some wrong lookup values": content[0] != docid → continue. We can craft that: put an offset that points to a different line.

Careful with the skip case: if content[0] != docid we continue; but if the line is shorter (fewer fields), len(content) != len(fields) → continue. Both fine.

Now, an important subtlety: for the "wrong docid" case, we need offsets pointing at lines whose first column differs. E.g., docid "1000" but the line at that offset starts with "9999". But then that line's own docid may also be in the offsets... doesn't matter, main just processes each offset entry.

Let's build it more simply: generate lines, record offsets keyed by the *line's actual first column*, but write the offsets file with a possibly-different key. Hmm, that complicates.

Simpler approach for skip case: generate docs lines; for a subset, write the line with the correct docid but drop a field (so len mismatch), and for another subset, write a line starting with a wrong docid.

Let me write a generic builder:

```python
def _build(name, specs, fields):
    """specs: list of (docid, offset_key, values) where values is the list of columns to write."""
```

Hmm, let's make it concrete.

Plan: a function `_write_dataset(dirname, n_docs, n_fields, rng, body_len, title_len, skip_field_every=0, wrong_docid_every=0, offset_order=None)`.

Let me write:

```python
def _dataset(name, n, fields, rng, title_len, body_len, bad_fields=0, bad_docid=0):
    d = WORKDIR / name
    d.mkdir(parents=True, exist_ok=True)
    docs_path = d / "docs.tsv"
    off_path = d / "sample_offsets.tsv"
    offsets = []  # (key, offset)
    with open(docs_path, "wb") as f:
        for i in range(n):
            docid = str(100000 + i)
            cols = [docid]
            for fi in range(1, len(fields)):
                if fi == 1:
                    cols.append(_rand_text(rng, title_len))
                else:
                    cols.append(_rand_text(rng, body_len))
            pos = f.tell()
            line = "\t".join(cols)
            if bad_fields and i % bad_fields == 0:
                # drop the last column
                line = "\t".join(cols[:-1])
            if bad_docid and i % bad_docid == 0:
                # first column becomes something else
                line = "X" + line
            f.write((line + "\n").encode("utf-8"))
            offsets.append((docid, pos))
    with open(off_path, "w", encoding="utf-8") as f:
        for k, p in offsets:
            f.write(f"{k}\t{p}\n")
    return d, docs_path, off_path
```

Wait: for bad_docid, the line's first column becomes "X100000" while the offset key is "100000" → content[0] != docid → continue. Good.

For bad_fields, dropping a column → len(content) = len(fields)-1 → continue. Good.

But careful: with bad_docid, the line starts with "X"+docid, so content[0] = "X100000" ≠ "100000". Good.

Now, the last line: main writes "\n" at the end after the loop. Fine.

Note: main writes "\n" between docs (`if docs > 0: out.write("\n")`). So output is newline-separated JSON objects plus trailing newline. Fine.

Now, one more consideration: `open(out_file, "w")` — each call truncates and rewrites. Deterministic.

Now let's handle the number of fields: fields list includes "docid" as first field name. main does `doc["fields"][field] = content[i]` for i, field in enumerate(fields). So content[i] corresponds to field name fields[i]. Fine.

Now the thunk: for each case, thunk sets globals and returns ().

```python
def _case(src_dir, out_dir, fields, doc_type):
    def thunk():
        _mod.source_dir = str(src_dir)
        _mod.dest_dir = str(out_dir)
        _mod.docs_file = str(src_dir / "docs.tsv")
        _mod.out_file = str(out_dir / "documents.jsonl")
        _mod.sample_offset_file = str(src_dir / "sample_offsets.tsv")
        _mod.fields = list(fields)
        _mod.doc_type = doc_type
        return ()
    return thunk
```

But wait — the thunk returns args for main. main() takes no args, so `()` is correct.

Hmm, but there's a subtle issue: `_mod.out_file` directory must exist. Create out dirs at module level.

Another subtlety: main opens out_file with `open(out_file, "w")` — no encoding specified; writes JSON with default ensure_ascii=True, so ASCII output. Fine.

Now, "every thunk call gets the arguments of its own thunk call" — main has no args, so the state is the globals+files. Since the files aren't modified by main (except out_file which is rewritten), every call does the same work. Good.

But hold on: does the harness call the thunk once and then call main many times, or call the thunk before each call? Either way, setting globals is idempotent.

One risk: if the harness runs all cases and then re-runs the top 4 in a different order or interleaved, the globals are set per thunk call, so fine.

Now, checks(): 2-3 edge inputs, never measured, may raise.

1. Empty offsets file → main writes just "\n". (load_document_offsets returns {}, loop doesn't execute, out.write("\n")).
2. Offset pointing to a line with wrong docid → continue, only "\n" written.
3. A missing docs file → FileNotFoundError (raises). Hmm, "may raise" is allowed. But is it a good edge case? The check compares behaviour — both original and modified should raise identically. Probably fine, but maybe safer to keep non-raising edge cases. Let's do:
   - empty dataset (offsets file empty, docs file empty)
   - one doc with a single field (fields=["docid"]) — content has 1 column.
   - offsets file with an offset of 0 pointing to an empty first line? Hmm, if docs.tsv's first line is empty, content = [""], len 1 != 3 → continue.

Let's do 3 checks:
- "empty": empty docs.tsv and empty offsets file.
- "one-doc": one doc, 3 fields.
- "bad-offset": offsets file with a docid whose offset points beyond... Actually seek beyond EOF then readline returns "" → content=[""] → len 1 != 3 → continue. Fine, no raise.

Hmm, seek beyond EOF is allowed.

Let me include a "missing-docs-file" check that raises? The instruction says checks "may raise". But identical behaviour must hold. A FileNotFoundError message includes the path — same path in both runs → identical. OK. But I'd rather avoid.

I'll do 3 checks: empty, one-doc, offset-beyond-eof.

Actually let's make one of them a genuinely odd one: offsets file with a docid but the docs file has a line with fewer fields.

Fine.

Now, let's think about performance and total runtime. The harness runs each case "many times". Total must be reasonable. Each case ~10-150ms. Fine.

Now let's write the text generator. Use random.Random(seed) for reproducibility.

```python
_WORDS = [...]  # small vocabulary
def _text(rng, n):
    return " ".join(rng.choice(_WORDS) for _ in range(n))
```

But generating 8000 docs * 50 words = 400k words — fine, but building all inputs under 10s. Let's be efficient: build a list of words and join.

Actually, simpler and faster: `"".join(rng.choice(_ALPHA) for _ in range(n))` is slow-ish for large n. Let's use random.choices.

```python
_ALPHA = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,-"
def _text(rng, n):
    return "".join(rng.choices(_ALPHA, k=n))
```

random.choices with k=n is fast. Good. But it may produce tabs? No, no tabs in alphabet. Good — important since content is split by tab.

Careful: avoid "\t" and "\n" in generated text. Yes.

Also avoid the JSON output being huge: each doc's JSON is roughly the content size. For 8000 docs * 400 bytes = 3.2MB output. Under 100k values? The output is a file; "keep what it returns (and anything it writes) under about 100 000 values". Hmm — 8000 docs with 3 fields = 24000 values. OK. But if I write to a file, the "values" count... The instruction says outputs compared in full. Since main returns None, comparison is probably on None. But to be safe, keep outputs modest: total docs across a case under ~20k.

Let me set sizes:
- typical: 3000 docs, 3 fields, title 30, body 200.
- large: 8000 docs, 3 fields, title 40, body 250. Output values: 8000*3=24000. OK.
- long-body: 1200 docs, body 1500.
- many-fields: 2500 docs, 8 fields, each ~60 chars.
- skips: 3000 docs, with 1/3 bad fields and 1/3 bad docid.
- tiny-lines: 12000 docs, fields=docid,title with tiny text (10 chars). Output values 24000.
- medium-long-titles: 4000 docs, title 400.
- single-field: 15000 docs, fields=docid only, content = just docid. Then len(content)==1==len(fields). Output 15000 values. Fast per doc but 15000 iterations.

Hmm, I want each case to do "substantial and different work". Let's finalize 8.

Actually, also need to consider that the harness keeps the 4 with most work — so it's fine if some are small.

Let me now also double check: main's `f.seek(document_offsets[docid])` — the offsets must be byte offsets into the *binary* file. Since we write with `f.tell()` on a binary file, correct.

But main opens docs_file with `io.open(docs_file, "r", encoding="utf-8")` — text mode. seek() with a byte offset: For TextIOWrapper, `seek(offset)` with whence=0 seeks the underlying buffer to that byte offset and discards the decoder state. I'm now fairly confident this works (it's the documented behavior for offsets from tell(), but arbitrary offsets also work as long as they're at a character boundary). Since our data is ASCII (alphabet is ASCII), all byte offsets are char boundaries. 

Hmm wait, is `_ALPHA` ASCII? "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,-" — yes ASCII. And docids are digits. Good. Everything ASCII → byte offset == char offset.

Now the offsets file: written with `encoding="utf-8"`, ASCII content. Fine.

Now, the module import: `importlib.import_module("convert-to-vespa-format")`. The file's module-level code runs. If it requires argv, we set it.

Let me now write the final code carefully.

One more consideration: WORKDIR might not be defined at the time... it's provided. OK.

Also: the harness imports our module — so module-level code runs. We create files there. Good.

Potential issue: `sys.path.insert(0, _PYDIR)` — where is the repo? I'll try several candidates:

```python
_CANDIDATES = [
    os.path.join(os.getcwd(), "text-search", "python"),
    os.path.join(os.getcwd(), "sample-apps", "text-search", "python"),
    "text-search/python",
]
```

And pick the first with the file.

Actually more robust: walk up from cwd looking for "text-search/python/convert-to-vespa-format.py". Let's do a simple search:

```python
def _find_pydir():
    base = os.getcwd()
    cand = os.path.join(base, "text-search", "python")
    if os.path.isfile(os.path.join(cand, "convert-to-vespa-format.py")):
        return cand
    # search upward and downward a bit
    for root, dirs, files in os.walk(base):
        # limit depth
        if "convert-to-vespa-format.py" in files:
            return root
    ...
```

os.walk over the whole repo could be slow but OK (repo is small). But could be huge... sample-apps repo is small-ish. Let's limit: walk with a depth check. Eh, let's just do the direct check plus a bounded walk.

Actually simpler: use `pathlib.Path.cwd().rglob("convert-to-vespa-format.py")`. Could be slow if repo huge. sample-apps is maybe a few thousand files. Acceptable.

Hmm, but the harness might run with cwd = repo root. Let's do:

```python
_pyfile = None
for p in Path.cwd().rglob("convert-to-vespa-format.py"):
    _pyfile = p
    break
```

Wait, but is `pathlib` imported? We can import it. WORKDIR is a pathlib.Path.

Hmm, rglob could be slow (seconds). Risky for the 10s budget but probably fine. Let's first try the direct path, then fall back to rglob.

Actually, since we can't be sure, and rglob on a large repo... sample-apps: I think it's a moderately sized repo with many sample app directories. rglob might take a couple seconds. Acceptable.

Let me combine: try direct candidate; if not found, rglob.

Now write it.

```python
import importlib
import os
import random
import sys
from pathlib import Path


def _find_module_dir():
    direct = Path.cwd() / "text-search" / "python"
    if (direct / "convert-to-vespa-format.py").is_file():
        return direct
    for p in Path.cwd().rglob("convert-to-vespa-format.py"):
        return p.parent
    raise RuntimeError("convert-to-vespa-format.py not found")
```

Then:

```python
_MOD_DIR = _find_module_dir()
if str(_MOD_DIR) not in sys.path:
    sys.path.insert(0, str(_MOD_DIR))
```

Then import with argv fallback.

```python
def _import_module():
    src = str(WORKDIR / "argv-src")
    dst = str(WORKDIR / "argv-dst")
    off = str(WORKDIR / "argv-src" / "sample_offsets.tsv")
    cands = [
        ["convert-to-vespa-format.py", src, dst, "docid,title,body", "doc", off],
        ["convert-to-vespa-format.py", src, dst, "docid,title,body", "doc"],
        ["convert-to-vespa-format.py", src, dst, "docid,title,body"],
        ["convert-to-vespa-format.py", src, dst],
    ]
    last = None
    for argv in cands:
        sys.argv = argv
        try:
            return importlib.import_module("convert-to-vespa-format")
        except (SystemExit, IndexError, ValueError, TypeError) as e:
            last = e
            continue
    raise RuntimeError(f"could not import: {last}")


_mod = _import_module()
main = _mod.main
```

Hmm, careful: catching broad exceptions might mask real errors. But fine.

Wait, one issue: if the first candidate succeeds, great. If it fails with SystemExit (usage), we retry. But the module might partially create files? No.

Another issue: if the module's usage check is `if len(sys.argv) != 6`, then candidate 1 (6 elements) works. If it's `!= 5`, candidate 2 works. Etc.

But what if the module uses `sys.argv[1..5]` without a length check and there are only 4 args in candidate 4 → IndexError → caught. Good.

Alright.

Now, after import, we should override globals. But if the module defined `source_dir` etc. — we override anyway.

Also `fields` — note that the module did `fields = fields.split(",")`. If we set `_mod.fields = ["docid","title","body"]`, good.

Now, an important check: does `main` reference `doc_type`? Yes. Set it.

Let me now write the data builders.

```python
_ALPHA = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,-"

def _text(rng, n):
    if n <= 0:
        return ""
    return "".join(rng.choices(_ALPHA, k=n))
```

Now the dataset builder. I want flexibility. Let me write:

```python
def _build_dataset(name, docids, field_names, rng, sizes, bad_fields_every=0, bad_docid_every=0, skip_last_every=0):
    ...
```

Hmm, let me simplify with a spec list per doc: each entry is (offset_key, columns).

Actually let's write a lower-level function:

```python
def _write_files(name, lines, offsets):
    """lines: list of str (without newline); offsets: list of (key, index_into_lines)"""
    d = WORKDIR / name
    d.mkdir(parents=True, exist_ok=True)
    docs_path = d / "docs.tsv"
    off_path = d / "sample_offsets.tsv"
    pos_list = []
    with open(docs_path, "wb") as f:
        for ln in lines:
            pos_list.append(f.tell())
            f.write((ln + "\n").encode("utf-8"))
    with open(off_path, "w", encoding="utf-8") as f:
        for key, idx in offsets:
            f.write(f"{key}\t{pos_list[idx]}\n")
    return d
```

And out dir: `WORKDIR / (name + "_out")`, created.

Then a generic generator:

```python
def _gen_case(name, n_docs, field_names, rng, title_len, body_len, bad_fields_every=0, bad_docid_every=0):
    lines = []
    offsets = []
    for i in range(n_docs):
        docid = str(100000 + i)
        cols = [docid]
        for fi in range(1, len(field_names)):
            if fi == 1:
                cols.append(_text(rng, title_len))
            else:
                cols.append(_text(rng, body_len))
        line = "\t".join(cols)
        if bad_fields_every and i % bad_fields_every == 0:
            line = "\t".join(cols[:-1])
        if bad_docid_every and i % bad_docid_every == 0:
            line = "X" + line
        offsets.append((docid, len(lines)))
        lines.append(line)
    return _write_files(name, lines, offsets)
```

Wait, if `bad_fields_every` drops the last column, but the last column is the "body" — for field_names of length 3, cols has 3 entries, drop last → 2 → len mismatch. Good.

But careful: for the case where we drop columns, we still record the offset. Good.

Now docids: `str(100000 + i)`.

Now out dirs: create at module level.

Let me define cases:

```python
def cases():
    out = []
    specs = [
        ("typical", 3000, ["docid", "title", "body"], 0, 40, 250, 0, 0),
        ...
    ]
```

Hmm, but each case needs its own rng seed and its own generated files. Let me build them at module level so thunks are cheap, or build inside thunk (setup not timed but runs each repetition). Building 8000 docs each repetition would be slow (total runtime). Better build at module level.

But `cases()` returns thunks; the thunks reference pre-built dirs. So build at module level.

Let me structure:

```python
_CASES = []

def _make_case(label, n_docs, field_names, seed, title_len, body_len, bad_fields_every=0, bad_docid_every=0):
    rng = random.Random(seed)
    d = _gen_case("case_" + label, n_docs, field_names, rng, title_len, body_len, bad_fields_every, bad_docid_every)
    outdir = WORKDIR / ("out_" + label)
    outdir.mkdir(parents=True, exist_ok=True)
    _CASES.append((label, d, outdir, list(field_names)))
```

Then:

```python
def cases():
    return [(_label, _thunk_for(d, outdir, fields)) for ...]
```

with

```python
def _make_thunk(src, outdir, fields):
    def thunk():
        _mod.source_dir = str(src)
        _mod.dest_dir = str(outdir)
        _mod.docs_file = str(src / "docs.tsv")
        _mod.out_file = str(outdir / "documents.jsonl")
        _mod.sample_offset_file = str(src / "sample_offsets.tsv")
        _mod.fields = list(fields)
        _mod.doc_type = "doc"
        return ()
    return thunk
```

Hmm wait — WORKDIR might not exist as a directory? It's provided, presumably exists. `(WORKDIR / "case_x").mkdir(parents=True, exist_ok=True)` works.

Now the label uniqueness: yes.

Let me define the 8 cases concretely:

1. ("typical", 3000, ["docid","title","body"], seed 0, title 40, body 250)
2. ("large", 9000, ["docid","title","body"], seed 1, title 50, body 300)  — output values 27000
3. ("long-body", 1200, ["docid","title","body"], seed 2, title 30, body 1500)
4. ("many-fields", 2500, ["docid"] + [f"f{i}" for i in range(1,9)], seed 3, title 40, body 40) — 9 fields total. Wait, my generator uses field_names length; for fi==1 title_len, else body_len. With 9 fields, 8 body-ish fields of 40 chars. Total line ~ 320 chars.
5. ("skips", 4000, ["docid","title","body"], seed 4, title 40, body 200, bad_fields_every=3, bad_docid_every=5)
6. ("tiny", 15000, ["docid","title"], seed 5, title 8, body 0) — 2 fields.
7. ("long-titles", 3500, ["docid","title","body"], seed 6, title 500, body 100)
8. ("single-field", 20000, ["docid"], seed 7, ...) — fields=docid only. Lines are just "100000". len(content)=1. Output 20000 values. Hmm, that's fast per doc. Maybe use 20000.

Hmm, case 8 with 20000 docs: each iteration does seek, readline, strip, split, dict creation, json.dump. Maybe 20000 * 8µs = 160ms. OK.

Actually, let me reconsider case 6 "tiny" with 15000 docs of 2 fields — output values 30000. Fine.

Total output size per case: keep under 100k values. OK.

Memory: lines stored as Python strings; 20000 lines * ~20 chars = small. Case 2: 9000 lines * 350 chars = 3MB. Fine.

Build time: generating random text with rng.choices for ~9000*300 = 2.7M chars — fast (~0.1s). Total across cases maybe 1s. Fine.

Now, one issue: `_write_files` returns `d` (Path). But `WORKDIR / name` — name includes "case_". Fine.

Now checks():

```python
def checks():
    # empty dataset
    d0 = WORKDIR / "chk_empty"
    d0.mkdir(parents=True, exist_ok=True)
    (d0 / "docs.tsv").write_bytes(b"")
    (d0 / "sample_offsets.tsv").write_bytes(b"")
    out0 = WORKDIR / "chk_empty_out"
    out0.mkdir(parents=True, exist_ok=True)

    # one doc
    d1 = WORKDIR / "chk_one"
    d1.mkdir(parents=True, exist_ok=True)
    line = "100000\thello\tworld"
    (d1 / "docs.tsv").write_bytes((line + "\n").encode())
    (d1 / "sample_offsets.tsv").write_bytes(b"100000\t0\n")
    out1 = ...

    # offset beyond EOF
    d2 = ...
    (d2/"docs.tsv").write_bytes(b"100000\thello\tworld\n")
    (d2/"sample_offsets.tsv").write_bytes(b"999999\t100000\n")  # seek past end
    ...
    return [
        ("empty", _make_thunk(d0, out0, ["docid","title","body"])),
        ("one-doc", _make_thunk(d1, out1, ["docid","title","body"])),
        ("offset-past-eof", _make_thunk(d2, out2, ["docid","title","body"])),
    ]
```

Hmm, for "offset-past-eof", seek to 100000 on a 20-byte file then readline → "" → strip → "" → split("\t") → [""] → content[0]="" != "999999" → continue. Writes "\n". No raise. Good.

Actually wait — is seeking past EOF allowed in text mode? Yes, seek to any non-negative offset is allowed. Reading returns "". Good.

Let's also consider adding a check that raises — not needed.

Now, module-level construction of the case files. But careful: WORKDIR usage at module level. And `_mod` import.

Order: define helper functions, find module dir, import module, build datasets, define checks/cases.

Potential problem: if the harness imports our module in a fresh process each time... fine.

Another potential problem: `_import_module` may print usage text to stdout for failed attempts. That could pollute stdout comparison? The harness probably captures stdout around the function call only. But to be safe, redirect stdout/stderr during import attempts. Let's use contextlib.redirect_stdout(io.StringIO()) — hmm, that requires importing io and contextlib. Actually simpler: `sys.stdout = ...`? That's mutating global state. Use contextlib.redirect_stdout with a StringIO for the import phase only, then restore.

Actually, does the module print? If it has `print("Usage: ...")` then yes. Let's suppress with contextlib.

```python
import contextlib, io
with contextlib.redirect_stdout(io.StringIO()):
    ...
```

But redirect_stdout doesn't capture C-level writes; print goes through sys.stdout so it's fine.

Hmm, but careful: redirect_stdout sets sys.stdout globally during import; since it's module-level setup, fine.

Let's just do it for the import loop.

Now, what if all import candidates fail? Then we raise at import time, and the harness fails. Can't do much.

Let me reconsider the argv values: they should be plausible. `src` and `dst` paths. Since we override globals, values don't matter, only count. But if the module does something at import like opening files... it doesn't (per the code shown).

Alright. Also: what if the module's arg parsing happens inside a function called at module level? Same thing.

Now — another important thought: what if the module does NOT use sys.argv at all, and source_dir/dest_dir/fields/etc. are hardcoded literals in the module? Then import works regardless, and we override. Fine.

What if the module reads from `os.environ`? Then import works (defaults) and we override. Fine.

OK, the fallback loop handles the argv case.

One more: what if the module name with hyphens fails to import via importlib? Let me double check. `importlib.import_module("convert-to-vespa-format")` → `_bootstrap._gcd_import` → `_find_and_load` → `_find_and_load_unlocked` → checks sys.modules, then `_bootstrap._find_spec(name, path)` → iterates sys.meta_path finders. The PathFinder finds in sys.path: for each entry, FileFinder. FileFinder._fill_cache / _find_spec: `tail_module = name.rpartition('.')[2]` = "convert-to-vespa-format"; then checks `tail_module + '.py'` in the cache → "convert-to-vespa-format.py". Yes, it works.

Also, sys.modules key is "convert-to-vespa-format". Fine.

Now let's also handle the possibility that the harness's sys.argv is needed... no.

Let me write the final code.

Also note: the module under test uses `open(out_file, "w")` without encoding — writes ASCII JSON. Good.

Wait, one more: `json.dump(doc, out)` writes with ensure_ascii=True by default, so non-ASCII would be escaped. Our data is ASCII anyway.

Let me also double check the "fields" length vs content length for the many-fields case: field_names = ["docid", "f1", ..., "f8"] → 9 names. cols = [docid] + 8 generated strings → 9. len matches. Good.

For "tiny": field_names = ["docid","title"] → cols = [docid, text(title_len=8)] → 2 columns. Good.

For "single-field": field_names = ["docid"] → the for loop `range(1,1)` is empty → cols = [docid] → 1 column. len(content)=1=len(fields). Good. But wait, if docid contains no tab, split("\t") gives [docid]. Good.

Hmm, but with 20000 docs and single field, the JSON output is `{"put": "id:doc:doc::100000", "fields": {"docid": "100000"}}` ~ 60 bytes each → 1.2MB. Fine.

Now, is 20000 docs too many for the harness's "keep the data in memory under about 100 MB"? docs.tsv ~ 20000*7 = 140KB. Fine.

Let me reconsider case sizes to make each call 1ms-200ms. The dominant cost per doc is probably the seek+readline (Python-level) ~2-5µs and json.dump ~3-10µs. So 20000 docs → ~100-200ms. OK, borderline. Let's use 15000 for single-field.

Let me set:
1. typical: 3000 docs, 3 fields
2. large: 9000 docs, 3 fields
3. long-body: 1500 docs, body 1500
4. many-fields: 3000 docs, 9 fields
5. skips: 5000 docs, mixed
6. tiny: 12000 docs, 2 fields
7. long-titles: 4000 docs, title 500
8. single-field: 15000 docs, 1 field

Fine.

Now write `_gen_case` to also handle title/body lengths per field index. For many-fields, I want each of the 8 fields to be ~40 chars. My generator: fi==1 → title_len; else body_len. So set title_len=40, body_len=40 for many-fields. Good.

For long-titles: title_len=500, body_len=100.

OK.

Let me write everything now.

```python
import contextlib
import importlib
import io
import os
import random
import sys
from pathlib import Path

_ALPHA = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,-"


def _find_module_dir():
    direct = Path.cwd() / "text-search" / "python"
    if (direct / "convert-to-vespa-format.py").is_file():
        return direct
    for p in Path.cwd().rglob("convert-to-vespa-format.py"):
        return p.parent
    raise RuntimeError("convert-to-vespa-format.py not found")


_MOD_DIR = _find_module_dir()
if str(_MOD_DIR) not in sys.path:
    sys.path.insert(0, str(_MOD_DIR))


def _import_under_test():
    src = str(WORKDIR / "_argv_src")
    dst = str(WORKDIR / "_argv_dst")
    off = str(WORKDIR / "_argv_src" / "sample_offsets.tsv")
    candidates = [
        ["convert-to-vespa-format.py", src, dst, "docid,title,body", "doc", off],
        ["convert-to-vespa-format.py", src, dst, "docid,title,body", "doc"],
        ["convert-to-vespa-format.py", src, dst, "docid,title,body"],
        ["convert-to-vespa-format.py", src, dst],
    ]
    last_err = None
    for argv in candidates:
        sys.argv = argv
        try:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                return importlib.import_module("convert-to-vespa-format")
        except (SystemExit, IndexError, ValueError, TypeError) as exc:
            last_err = exc
            continue
    raise RuntimeError("failed to import convert-to-vespa-format: %r" % (last_err,))


_mod = _import_under_test()
main = _mod.main
```

Hmm, `importlib.import_module` inside redirect — fine.

But careful: if the module imports fine but its body raises SystemExit deliberately... same handling.

Now the builders.

```python
def _text(rng, n):
    if n <= 0:
        return ""
    return "".join(rng.choices(_ALPHA, k=n))


def _write_dataset(name, lines, offsets):
    d = WORKDIR / name
    d.mkdir(parents=True, exist_ok=True)
    docs_path = d / "docs.tsv"
    off_path = d / "sample_offsets.tsv"
    positions = []
    with open(docs_path, "wb") as f:
        for ln in lines:
            positions.append(f.tell())
            f.write((ln + "\n").encode("utf-8"))
    with open(off_path, "w", encoding="utf-8") as f:
        for key, idx in offsets:
            f.write("%s\t%d\n" % (key, positions[idx]))
    return d


def _build_case(name, n_docs, field_names, seed, title_len, body_len,
                bad_fields_every=0, bad_docid_every=0):
    rng = random.Random(seed)
    lines = []
    offsets = []
    for i in range(n_docs):
        docid = str(100000 + i)
        cols = [docid]
        for fi in range(1, len(field_names)):
            cols.append(_text(rng, title_len if fi == 1 else body_len))
        line = "\t".join(cols)
        if bad_fields_every and i % bad_fields_every == 0:
            line = "\t".join(cols[:-1])
        if bad_docid_every and i % bad_docid_every == 0:
            line = "X" + line
        offsets.append((docid, len(lines)))
        lines.append(line)
    src = _write_dataset("case_" + name, lines, offsets)
    outdir = WORKDIR / ("out_" + name)
    outdir.mkdir(parents=True, exist_ok=True)
    return src, outdir, list(field_names)
```

Wait — if bad_fields_every drops the last col AND bad_docid_every prefixes, the line may still have len != fields. Fine.

Hmm, but a subtle bug: when bad_fields_every applies, we write a line with fewer columns; the offset for that docid points to it; content[0] == docid (good) but len mismatch → continue. Good.

When bad_docid_every applies, content[0] = "X1000xx" != docid → continue. Good.

Now the thunk maker:

```python
def _thunk(src, outdir, fields):
    def run():
        _mod.source_dir = str(src)
        _mod.dest_dir = str(outdir)
        _mod.docs_file = str(src / "docs.tsv")
        _mod.out_file = str(outdir / "documents.jsonl")
        _mod.sample_offset_file = str(src / "sample_offsets.tsv")
        _mod.fields = list(fields)
        _mod.doc_type = "doc"
        return ()
    return run
```

Hmm, `fields` is a closure variable; `list(fields)` makes a copy each call — cheap.

Now build all cases at module level:

```python
_CASE_DEFS = [
    ("typical", 3000, ["docid", "title", "body"], 0, 40, 250, 0, 0),
    ("large", 9000, ["docid", "title", "body"], 1, 50, 300, 0, 0),
    ("long-body", 1500, ["docid", "title", "body"], 2, 30, 1500, 0, 0),
    ("many-fields", 3000, ["docid"] + ["f%d" % i for i in range(1, 9)], 3, 40, 40, 0, 0),
    ("with-skips", 5000, ["docid", "title", "body"], 4, 40, 200, 3, 5),
    ("tiny-lines", 12000, ["docid", "title"], 5, 8, 0, 0, 0),
    ("long-titles", 4000, ["docid", "title", "body"], 6, 500, 100, 0, 0),
    ("single-field", 15000, ["docid"], 7, 0, 0, 0, 0),
]

_BUILT = [(name, _thunk(*(_build_case(name, *rest)))) for name, *rest in _CASE_DEFS]
```

Hmm, `_build_case(name, n_docs, field_names, seed, title_len, body_len, bad_fields_every, bad_docid_every)` returns (src, outdir, fields). Then `_thunk(src, outdir, fields)`. So `_thunk(*_build_case(...))`. And `_CASE_DEFS` entries are (name, n, fields, seed, tl, bl, bf, bd). So `rest` = [n, fields, seed, tl, bl, bf, bd]. Good.

Then:

```python
def cases():
    return [(name, thunk) for name, thunk in _BUILT]
```

But wait: should cases() return fresh thunks each call? Doesn't matter.

Hmm, but building at module level means the files are created at import. Good.

Now checks:

```python
def _edge(name, docs_bytes, offsets_bytes, fields):
    src = WORKDIR / ("chk_" + name)
    src.mkdir(parents=True, exist_ok=True)
    (src / "docs.tsv").write_bytes(docs_bytes)
    (src / "sample_offsets.tsv").write_bytes(offsets_bytes)
    outdir = WORKDIR / ("chk_out_" + name)
    outdir.mkdir(parents=True, exist_ok=True)
    return _thunk(src, outdir, fields)


def checks():
    return [
        ("empty", _edge("empty", b"", b"", ["docid", "title", "body"])),
        ("one-doc", _edge("one", b"100000\thello\tworld\n", b"100000\t0\n", ["docid", "title", "body"])),
        ("offset-past-eof", _edge("past", b"100000\thello\tworld\n", b"999999\t100000\n", ["docid", "title", "body"])),
    ]
```

Wait, `_edge` needs to be defined after `_thunk`. Fine.

Hmm, `_edge` writes files at module level? No — it's called inside checks(), which the harness calls. That's setup, not timed (the returned thunks are what's measured; but `_edge` runs inside checks() itself). The instructions say setup goes in the thunk or module-level code. checks() body running file writes — is that OK? checks() is called to get the list; the file writes happen there. It's not timed (only the function call under test is timed). I think it's fine. But to be safer, put the file writes in the thunk.

Let me restructure `_edge` to return a thunk that writes the files:

Actually simpler: make `_edge` return a thunk that (a) writes the files and (b) sets globals. That's fully compliant.

```python
def _edge(name, docs_bytes, offsets_bytes, fields):
    src = WORKDIR / ("chk_" + name)
    src.mkdir(parents=True, exist_ok=True)
    outdir = WORKDIR / ("chk_out_" + name)
    outdir.mkdir(parents=True, exist_ok=True)

    def run():
        (src / "docs.tsv").write_bytes(docs_bytes)
        (src / "sample_offsets.tsv").write_bytes(offsets_bytes)
        _mod.source_dir = str(src)
        _mod.dest_dir = str(outdir)
        _mod.docs_file = str(src / "docs.tsv")
        _mod.out_file = str(outdir / "documents.jsonl")
        _mod.sample_offset_file = str(src / "sample_offsets.tsv")
        _mod.fields = list(fields)
        _mod.doc_type = "doc"
        return ()
    return run
```

Good. The dir creation is at checks() call time (module-level-ish), file writes in thunk.

Now, let me double-check `main` doesn't use `source_dir`/`dest_dir` directly (it uses docs_file/out_file). We set them anyway.

One more consideration: `main` is called with no args, and the harness "renders arguments before and after each call to see whether it changed them" — no args, fine.

Now let's think again about whether main might fail on our data. `content = line.split("\t")`. For lines with tabs — our text has no tabs. Good.

`found_docid = content[0]` — fine.

`len(content) != len(fields)` — for typical, 3 == 3. Good.

`doc = {...}`; `json.dump(doc, out)` — fine.

So all cases run to completion.

Potential issue: docid str "100000" — the offset key must match content[0] exactly. We write the same docid in both. Good.

Now, one thing: the offsets file keys — csv.reader with delimiter "\t" yields [docid, offset]. Our file writes "%s\t%d\n". Good.

Edge: empty offsets file → csv.reader yields nothing → {} → fine.

Now let me reconsider the `_find_module_dir` rglob — if the file isn't found, RuntimeError at import → harness fails. Acceptable risk.

Actually, maybe I should also add `str(WORKDIR)`-relative? No.

Hmm, what if the repo is not under cwd but under WORKDIR? Unlikely. Let me also check `Path.cwd()` and its parents for a "text-search/python" dir. Let me write a more thorough search:

```python
def _find_module_dir():
    cands = []
    cwd = Path.cwd()
    for base in [cwd] + list(cwd.parents):
        cands.append(base / "text-search" / "python")
        cands.append(base / "sample-apps" / "text-search" / "python")
    for c in cands:
        if (c / "convert-to-vespa-format.py").is_file():
            return c
    for p in cwd.rglob("convert-to-vespa-format.py"):
        return p.parent
    raise RuntimeError(...)
```

Good.

Now, let me also double check: after import, `_mod` is the module. But `main = _mod.main` — if the module's `main` references globals via the module dict, calling `main()` works.

Wait, careful: `main` is defined as a function in the module; calling `_mod.main()` uses `_mod.__dict__` for globals. Yes.

Now let me reconsider: is there a risk that the module-level code in convert-to-vespa-format.py *reads* files (e.g., checks existence)? The shown code doesn't.

Let's finalize.

One more thought on total output size for the "single-field" case: 15000 docs → the out file is ~1MB. The harness compares outputs "in full" — for main, output is None (return). But it might also compare file writes? Unlikely. Anyway, 15000 values is under 100k.

Actually hmm — "keep what it returns (and anything it writes) under about 100 000 values". Our biggest write is 9000 docs * (1 put + 3 fields) = 36000 values. Under 100k. Good.

Let me reconsider case "large" with 9000 docs and see the time. Each iteration: seek + readline + strip + split + dict + json.dump. Probably ~15-25µs. 9000 * 20µs = 180ms. Plus offsets load (9000 csv rows) ~ 20ms. Total ~200ms. Borderline but under 1s. OK. Maybe reduce to 7000 to be safe. Let's use 8000.

Actually the limit is "over 1 s are dropped" and target 1ms-200ms. 200ms is the upper target. Let's keep sizes moderate:

1. typical: 3000
2. large: 7000
3. long-body: 1500
4. many-fields: 3000
5. with-skips: 5000
6. tiny-lines: 12000
7. long-titles: 4000
8. single-field: 15000

Fine.

Now writing the final code. Also need `import io` for StringIO — yes.

Let me make sure not to shadow `io` module name in a way that breaks... we import io at top and use io.StringIO. The module under test also imports io but that's separate.

Wait, careful: our module-level `import io` and the repo module's `import io` are the same module object. Fine.

Let me write it out.

```python
import contextlib
import importlib
import io
import random
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Locate and import the repository module under test
# ---------------------------------------------------------------------------

def _find_module_dir():
    cwd = Path.cwd()
    cands = []
    for base in [cwd] + list(cwd.parents):
        cands.append(base / "text-search" / "python")
        cands.append(base / "sample-apps" / "text-search" / "python")
    for c in cands:
        if (c / "convert-to-vespa-format.py").is_file():
            return c
    for p in cwd.rglob("convert-to-vespa-format.py"):
        return p.parent
    raise RuntimeError("could not locate convert-to-vespa-format.py")


_MOD_DIR = _find_module_dir()
if str(_MOD_DIR) not in sys.path:
    sys.path.insert(0, str(_MOD_DIR))


def _import_under_test():
    src = str(WORKDIR / "_argv_src")
    dst = str(WORKDIR / "_argv_dst")
    off = str(WORKDIR / "_argv_src" / "sample_offsets.tsv")
    candidates = [
        ["convert-to-vespa-format.py", src, dst, "docid,title,body", "doc", off],
        ["convert-to-vespa-format.py", src, dst, "docid,title,body", "doc"],
        ["convert-to-vespa-format.py", src, dst, "docid,title,body"],
        ["convert-to-vespa-format.py", src, dst],
    ]
    last_err = None
    for argv in candidates:
        sys.argv = argv
        try:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                return importlib.import_module("convert-to-vespa-format")
        except (SystemExit, IndexError, ValueError, TypeError) as exc:
            last_err = exc
    raise RuntimeError("failed to import convert-to-vespa-format: %r" % (last_err,))


_mod = _import_under_test()
main = _mod.main
```

Then helpers, data build, checks, cases.

I realize there may be an issue with redirect_stdout during import: if the import succeeds, we return inside the with block — fine.

Let me finalize the rest.

Also: should I worry that `sys.argv` mutation affects the harness? It's module-level setup; probably fine. To be tidy, could restore the original argv after import. Let's save and restore.

```python
_orig_argv = list(sys.argv)
...
sys.argv = _orig_argv
```

Hmm, but if the harness relies on sys.argv... unlikely. Let's restore.

Let me write final code.

Also for `_build_case`, note `bad_fields_every` uses `i % every == 0`, so index 0 also gets bad — that's fine (first doc skipped).

Wait, for the "with-skips" case with bad_fields_every=3 and bad_docid_every=5: at i=0, both apply → line = "X100000\ttitle" (dropped last col and prefixed). Fine.

Let's double check `line = "\t".join(cols[:-1])` when cols has 3 → 2 cols. Then `"X" + line`. OK.

Now writing.

One more: the `fields` we pass to `_mod.fields` must be a list of the field names in order matching columns. Yes.

Final answer below.

Let me also double check: `_thunk` returns `()` — main() called with no args. Good.

Potential gotcha: the harness may call `main(*args)` where args=() → `main()`. Good.

I think we're done. Let me write the complete source.

Actually, one concern: `WORKDIR` used inside `_import_under_test` at module level — WORKDIR is provided before our module runs? Presumably yes, it's a global injected. OK.

Also note `Path.cwd().rglob(...)` might be slow if the repo is huge; but it's a fallback.

Let me write it.

Final check on the "long-body" case: 1500 docs each with 1500-char body → each json ~1600 bytes → 2.4MB output. Values: 1500*3=4500. Fine.

And generation time for long-body: 1500*1500 = 2.25M chars via rng.choices — fast.

Total generation across all cases: roughly (3000*290 + 7000*350 + 1500*1530 + 3000*320 + 5000*240 + 12000*8 + 4000*600 + 15000*7) ≈ 0.87M + 2.45M + 2.3M + 0.96M + 1.2M + 0.1M + 2.4M + 0.1M ≈ 10.4M chars. rng.choices at ~10M chars/s... maybe 1-2s. Under 10s. OK.

Writing the answer now.