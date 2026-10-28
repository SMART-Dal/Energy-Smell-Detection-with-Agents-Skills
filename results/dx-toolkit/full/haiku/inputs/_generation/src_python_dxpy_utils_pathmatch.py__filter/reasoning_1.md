We need to write checks() and cases() for filter(names, pat). Need realistic workloads: folder listings and abs_path patterns. Need 8 measured inputs, each 1ms-200ms. Also note _cache global persists across calls; if we use same pattern repeatedly it's cached, fine. But function mutates _cache, not args. Names list not mutated. So can reuse.

Need to avoid patterns that cause translate cost dominating? Actually translate only if not cached. Since repeated many times, first call caches. But timing includes only call. If we use distinct patterns per thunk call? Each thunk returns same args, so same pattern each call; after first, cached. That's fine and realistic (the repo calls with same abs_path repeatedly? Actually path changes but okay). But we want substantial work in loop: many names, matching.

Need names realistic: folder listings like '/', '/A', '/B', '/A/B', etc. Pattern abs_path like '/A/*'? Note filter matches full name against pattern with \Z, so pattern must match entire path. In download.py, abs_path is a path glob? Let's think: pathmatch.filter(folder_listing, abs_path) where abs_path is something like '/project:/folder/*'? Actually _rel2abs returns abs_path, strip_prefix. The pattern is abs_path maybe with wildcard. matching_folders = pathmatch.filter(folder_listing, abs_path), then check '/' in matching_folders. So abs_path is a glob pattern for folder paths. Names are folder paths like '/', '/A', '/B'. We'll generate folder listings of various sizes and patterns.

Need 8 cases with different sizes, patterns, hit ratios. Ensure one call ~1ms-200ms. Python loop over names with regex match. For 200ms, maybe ~100k-500k names depending. Let's estimate: regex match simple pattern ~1-2 microsec per name. 100k -> 100-200ms. Keep under 100MB. Names as strings. 100k strings ~ few MB. Good.

Need output under 100k values. If many matches, result could be large. Keep result under 100k. So if names 100k and hit ratio high, result 100k, okay under 100k? "under about 100 000 values" keep <= 50k maybe. So use hit ratios moderate, and names maybe up to 80k with hit ratio 0.5 => 40k. Or 200k names with 0.1 hits => 20k. Work still large.

Also arguments rendered before/after each call; input data under 1,000,000 values. Names list of 200k strings okay.

Need checks: small edge inputs: empty names, single name, None pattern? Function expects str pat; None would raise at os.path.normcase(None)? Actually normcase expects path-like; None raises TypeError. checks may raise, allowed. But they compare behavior identical. Could include empty names with pattern, one element match/miss, pattern with special chars '[' unclosed, '!' etc. 2-3 checks.

Need import from dxpy.utils.pathmatch import filter. Also maybe import module to set _cache? We can import pathmatch module? The task says import exactly as shown: `from dxpy.utils.pathmatch import filter`. Could also import pathmatch? It says import the repository's modules exactly as shown in the task. We can use only that import. But we may need to reset _cache? Not necessary. However _cache persists across checks and cases; if we use same pattern, cached. But no issue. But if checks use weird pattern and then cases use same? Distinct labels. _cache max 100; our patterns maybe less than 100. We can clear _cache between? We can't access _cache without importing module. But not needed. However if we want each case to measure translate too? Not necessary; repeated calls mostly cached. The original and modified both share same cache behavior. Timing only call. If first call includes translate, but timing repeats many times; average dominated by loop. Fine.

Need generate realistic folder names. Let's design helper `_listing(n, seed, depth=3)`. Generate names like '/A/B/C' with random components. Also include root '/'. For patterns, use globs like '/A/*', '/A/*/B', '/*/foo*', '/*/*/bar?'. But note pattern matching uses [^\/]* for *, so * doesn't cross slash. So '/A/*' matches '/A/B' but not '/A/B/C'. Good.

Need cases that exercise different code paths in translate: '*', '?', character classes '[...]', '!', escaping, literal. The filter loop uses regex. Patterns with character classes cause more regex complexity. We can include patterns with classes.

Need ensure pattern matches enough names to produce output but not too many. For pattern like '/A/*' and random names, hit ratio depends. We can craft names to match. We can generate names from a set of top-level dirs, then pattern selects subset. For high hit ratio, use pattern with leading wildcard? e.g. '/*' matches only depth 1 names. If names mostly depth 3, few hits. We can design per case.

Let's create a base pool of folder names: generate random paths with components from a vocabulary. For each case, we can generate names tailored to pattern to get desired hit ratio. Simpler: generate names and then choose pattern that matches a fraction. But need diversity.

Maybe build names as list of strings. For each case, generate a list of names with a certain structure and pattern. Use random seed.

Need 8 cases:
1. typical: 20k names, pattern '/project-*/data/*' maybe. But we need names matching. Let's make names like '/project-0/data/sub0', etc. Pattern '/project-*/data/*' matches depth 3 exactly. Hit ratio maybe 1/3 if all names depth 3 and first component project-*. Actually if all names start with '/project-', then pattern matches all. To get moderate hits, mix names.

Let's think of realistic folder listing from dxpy.list_subfolders(project, parent_folder, recurse=False). It returns immediate subfolders of a parent. So names are sibling paths, not deep? Actually it lists subfolders of parent_folder, so names are like '/A', '/B' if parent is '/'. But in download.py, folder_listing from parent_folder = os.path.dirname(abs_path). If abs_path is '/A/*', parent_folder is '/A', listing gives '/A/B', '/A/C'. Then pattern '/A/*' matches all. So typical: names are immediate children of a parent, pattern is parent + '/*'. Thus hit ratio often high. But could have other entries? list_subfolders returns only subfolders of that parent, so all names share parent and pattern matches all. So filter often returns all. But we need diverse hit ratios. Could simulate patterns with '?' or character classes selecting subset. Or pattern with specific name.

Realistic calls: filter(folder_listing, abs_path) where abs_path may contain wildcards from user path. So names are children of dirname(abs_path), and pattern is abs_path. If pattern has wildcard in last component, it filters among siblings. So names share parent, pattern like '/parent/foo*' selects some. That's realistic.

So generate names as siblings under a parent, e.g. '/data/proj-0000', '/data/proj-0001', ... up to n. Pattern '/data/proj-1*' selects those starting with 1. Hit ratio ~10%. For high hit ratio, pattern '/data/*' selects all. For low, pattern '/data/proj-999*' selects few. Need substantial work: loop over all names regardless of hits. So n can be large.

We can make cases:
- many siblings, pattern matches all (n=50k, result 50k)
- many siblings, pattern matches 10% (n=100k, result 10k)
- many siblings, pattern with '?' (n=80k, result ~?).
- pattern with character class '[0-9]' etc.
- deep paths? But list_subfolders recurse=False gives immediate children only, so depth maybe parent depth + 1. But parent could be deep. Names can be deep paths. So we can have long path strings to increase regex work.
- names with special chars? Paths may have spaces, unicode? Could include.
- pattern with unclosed bracket triggers translate fallback, but only once. Not much loop difference.
- pattern with multiple wildcards.
- pattern with '!' class.
- pattern with no wildcards exact match (literal) - regex match still.

Need ensure output under 100k. For n=100k and hit ratio 0.5, result 50k. Good.

Need measure time. We can't run here, but choose sizes likely 1-200ms. Python loop with regex match over 100k names ~ maybe 50-100ms. Good. 200k names ~ 200ms maybe too high. Use up to 150k. Building all inputs under 10s: generating 8 lists of ~100k strings each ~800k strings, okay maybe 2-3s. Memory ~ maybe 50MB. Good.

Need avoid uniformity that simple trick could exploit? The original function uses regex, modified likely same. We want realistic. Random generation with seed.

Let's write helper `_names(n, parent, prefix, width, seed, extra_suffixes)`? Simpler: generate names as f"{parent}/{prefix}{i:0{width}d}{suffix}" for i in range(n). But that's uniform pattern; could be exploited? The function uses regex, no trick. But instruction says avoid uniformity unless repo really passes. Folder listings are naturally sequential? Could be. But to be safe, randomize order and include random components. Use random.Random(seed) to shuffle and vary.

We can generate names by sampling random integers, but need unique? Not necessary, duplicates possible. Duplicates are realistic? Folder names unique within parent. Use set to unique. For n up to 150k, generating unique random ints fine.

Let's create a helper that builds a list of sibling names under a parent with random suffixes:
```
def _siblings(n, parent, seed, prefix="", suffix_pool=None, width=6):
    rng = random.Random(seed)
    names = set()
    while len(names) < n:
        i = rng.randrange(10**width)
        s = f"{parent}/{prefix}{i:0{width}d}"
        if suffix_pool:
            s += rng.choice(suffix_pool)
        names.add(s)
    names = list(names)
    rng.shuffle(names)
    return names
```
But if n close to 10**width, loop slow. Use n <= 100k, width=6 gives 1M space, fine. For n=150k, 1M space, okay. Or use sequential with random shuffle.

But pattern must match subset. If names are random 6-digit numbers, pattern '/parent/1*' matches those starting with 1 (10%). Pattern '/parent/[0-4]*' matches 50%. Pattern '/parent/???0' matches numbers ending with 0? Actually '?' matches one non-slash char, so '/parent/??????' matches any 6-char. For specific digits, use pattern '/parent/1?????' matches first digit 1. Good.

We can also include parent with wildcards? Pattern must match full name. So pattern includes parent literal.

Let's define cases:

Case 1: "many-all": n=60_000, parent="/data/project", prefix="run-", width=6, pattern="/data/project/run-*" -> matches all. Result 60k. Work ~60k matches. Time maybe 30-60ms.

Case 2: "many-low-hit": n=120_000, parent="/data/project", prefix="run-", width=6, pattern="/data/project/run-9*" -> ~10% hits = 12k. Work 120k loops. Time ~60-120ms.

Case 3: "question-mark": n=80_000, parent="/data/project", prefix="run-", width=6, pattern="/data/project/run-??????" -> matches all? Actually run- then 6 chars. All names have run- + 6 digits, so all match. Need '?' to do work. Pattern with '?' matches all but regex more complex. Result 80k. Time maybe.

Case 4: "char-class": n=100_000, parent="/data/project", prefix="run-", width=6, pattern="/data/project/run-[0-4]?????" -> 50% hits = 50k. Work 100k.

Case 5: "negated-class": n=100_000, parent="/data/project", prefix="run-", width=6, pattern="/data/project/run-[!0-4]?????" -> 50% hits. Note translate handles '!' by replacing with '^'. Good.

Case 6: "deep-paths": n=80_000, parent="/data/project/subfolder/deeper", prefix="file-", width=6, pattern="/data/project/subfolder/deeper/file-*" -> all match. Longer strings, more work per name. Time maybe 80k * longer.

Case 7: "mixed-suffixes": n=100_000, parent="/data/project", prefix="", width=6, suffix_pool=["", ".txt", "_backup", "-old", ".tar.gz"]? But folder names can have dots. Pattern "/data/project/*.txt" matches only suffix .txt. But * doesn't cross slash, so matches any name ending .txt. Hit ratio ~20%. Work 100k. Need generate names with suffix. Use helper with suffix_pool. Pattern "/data/project/*.txt". Note * matches any chars except slash, so matches "123456.txt". Good. Result ~20k.

Case 8: "exact-literal": n=150_000, parent="/data/project", prefix="run-", width=6, pattern="/data/project/run-123456" -> 1 hit (maybe none if not generated). Work 150k loops, result 0 or 1. This tests literal match with no wildcards. Time ~150k regex matches. Good.

Need ensure patterns are strings. For exact literal, if name not present, result empty, still work. But we want realistic. We can ensure one name matches by including it. But if random set doesn't include 123456, result empty. That's okay, but maybe output empty. Still work. Could choose pattern that matches one known name by generating names and then setting pattern to first name. But thunk returns args; we can compute pattern from generated list. In module-level, build names and pattern. For case 8, we can set pattern = names[0] (exact). Then matches 1. But if names[0] has special regex chars? Our names are alphanumeric, hyphen, slash, dot. Dot in suffix? For case 8 no suffix. Safe. But pattern is exact literal; translate escapes. Good.

Need checks:
- empty names: `([], "/data/*")` returns [].
- single match: `(["/data/project/run-000001"], "/data/project/run-*")` returns list.
- single miss or special pattern: `(["/data/project/run-000001"], "/data/project/run-9*")` returns [].
- unclosed bracket: `(["/data/project/run-000001"], "/data/project/run-[abc")` maybe translate treats as literal '[', so no match. This exercises edge. But checks only 2-3. We can do 3: empty, single match, unclosed bracket. Or None pattern? That would raise. Allowed. But maybe better to include pattern None to check error behavior? The function would call os.path.normcase(None) -> TypeError. Original and modified both raise? If modified same, okay. But checks may raise, allowed. But if modified handles differently, it would be a difference. The task says checks may raise. But to be safe, use inputs that run? It says checks may raise. But if original raises and modified raises same, fine. However if modified doesn't raise, difference. We don't know. Better use valid inputs for checks to avoid false difference? The checks are for identical behaviour, including exceptions. If we include None, it tests edge. But the function signature expects names, pat. None pat is odd type. Could be useful. But risk: modified might have different error message? They compare outputs? "checked only for identical behaviour" likely includes exception type. If both raise TypeError, okay. But if modified added handling, maybe not. The task says checks may raise, implying we can include raising inputs. I'll include one with None pattern? Hmm.

Let's read: "checks(): 2 or 3 small edge inputs (empty, one element, None, an odd type) checked only for identical behaviour, never measured. These may raise." So they encourage None/odd type. We can include:
- ("empty-names", lambda: ([], "/data/*"))
- ("single-match", lambda: (["/data/project/run-000001"], "/data/project/run-*"))
- ("none-pattern", lambda: (["/data/project/run-000001"], None))
But None pattern will raise TypeError at os.path.normcase(None). On posix, normcase does `os.fspath(s)`? Actually posixpath.normcase(s) returns os.fspath(s) maybe. In Python 3, posixpath.normcase = lambda s: os.fspath(s). So None raises TypeError. Both original and modified likely same. Good.

But note _cache: if None pattern, `pat = os.path.normcase(pat)` raises before cache. Fine.

Need module-level generation. We must import from dxpy.utils.pathmatch import filter. The module may not be importable? Repository dx-toolkit, src/python/dxpy/utils/pathmatch.py. The import path `from dxpy.utils.pathmatch import filter` assumes src/python on sys.path. The task says import exactly as shown. So we just use that.

Need ensure no network etc.

Let's write code.

Helper:
```
import random

def _siblings(n, parent, seed, prefix="", width=6, suffix_pool=None, shuffle=True):
    rng = random.Random(seed)
    names = set()
    # use sequential to guarantee n unique if n <= 10**width
    base = rng.randrange(10**width - n) if 10**width > n else 0
    for i in range(n):
        num = base + i
        s = f"{parent}/{prefix}{num:0{width}d}"
        if suffix_pool:
            s += rng.choice(suffix_pool)
        names.add(s)
    names = list(names)
    if shuffle:
        rng.shuffle(names)
    return names
```
But if suffix_pool, multiple numbers may get same suffix but still unique due to number. Good. If n > 10**width? We use width=6, n<=150k < 1M. Good. Base random offset could cause num exceed width? base max 10**width - n, so base+n-1 <= 10**width-1. Fine.

But for case with suffix_pool, pattern "/data/project/*.txt" matches names ending .txt. Our names are f"{num:06d}" + suffix. So e.g. "123456.txt". Pattern "*" matches "123456" then ".txt" literal. Good. Hit ratio = fraction with .txt. If suffix_pool has 5 items, ~20%. Good.

For case 7, we need suffix_pool include ".txt" and others. Use `["", ".txt", "_backup", "-old", ".tar.gz"]`. Note pattern "/data/project/*.txt" will also match names ending ".txt" only. Good.

For case 8 exact literal: use names from case 1? We can build a separate list. We can set pattern to a known name. But if we use helper, names[0] is random. We can do:
```
_names8 = _siblings(150_000, "/data/project", 8, prefix="run-", width=6)
_pat8 = _names8[0]
```
Then thunk returns (_names8, _pat8). But note _names8[0] might contain regex special chars? It's "/data/project/run-123456" no special. Good.

But we must be careful: module-level code runs before thunks. Building 8 lists of up to 150k, total ~790k strings. Each string ~50 bytes, list overhead ~8 bytes per pointer, total maybe 50MB. Within 100MB. Time to build maybe 1-2s. Good.

Need ensure each case's thunk returns a tuple of args. For filter, args are (names, pat). So `lambda: (_names1, _pat1)`. The function doesn't modify names, so reuse safe. If it did, we'd copy. It doesn't.

But _cache global: if we use same pattern across cases? They are distinct. _cache max 100, our patterns 8, fine. But checks run before cases? The harness likely calls checks and cases. _cache may contain check patterns. If check pattern equals a case pattern? We use distinct. But even if, cached. No issue.

Potential issue: `_cache` is module global and persists across original and modified? They run original and modified separately? Probably separate processes or same? Not our concern. But if they run original and modified in same process, _cache may be shared? The module is same? Actually modified version is a different function, but likely they replace? The task says "We run the original function and a modified version of it on your inputs". They probably have separate modules or monkeypatch? Not our concern. But if they use same module and swap function, _cache could carry. But both use same _cache. Our inputs don't rely on cache state.

Need ensure pattern strings are not mutated. filter does `pat = os.path.normcase(pat)`, returns new string or same. No mutation.

Let's write cases list with labels.

Case 1: "all-match-60k"
```
_names1 = _siblings(60_000, "/data/project", 1, prefix="run-", width=6)
_pat1 = "/data/project/run-*"
```
Case 2: "low-hit-120k"
```
_names2 = _siblings(120_000, "/data/project", 2, prefix="run-", width=6)
_pat2 = "/data/project/run-9*"
```
Case 3: "question-mark-80k"
```
_names3 = _siblings(80_000, "/data/project", 3, prefix="run-", width=6)
_pat3 = "/data/project/run-??????"
```
Case 4: "char-class-100k"
```
_names4 = _siblings(100_000, "/data/project", 4, prefix="run-", width=6)
_pat4 = "/data/project/run-[0-4]?????"
```
Case 5: "negated-class-100k"
```
_names5 = _siblings(100_000, "/data/project", 5, prefix="run-", width=6)
_pat5 = "/data/project/run-[!0-4]?????"
```
Case 6: "deep-paths-80k"
```
_names6 = _siblings(80_000, "/data/project/subfolder/deeper", 6, prefix="file-", width=6)
_pat6 = "/data/project/subfolder/deeper/file-*"
```
Case 7: "suffix-mix-100k"
```
_names7 = _siblings(100_000, "/data/project", 7, prefix="", width=6, suffix_pool=["", ".txt", "_backup", "-old", ".tar.gz"])
_pat7 = "/data/project/*.txt"
```
Case 8: "exact-literal-150k"
```
_names8 = _siblings(150_000, "/data/project", 8, prefix="run-", width=6)
_pat8 = _names8[0]
```
Wait for case 7, prefix="" and width=6, names like "/data/project/123456.txt". Pattern "/data/project/*.txt" matches. Good.

Need check hit ratios: Case 4 pattern "[0-4]?????" - first digit 0-4, then 5 '?' characters. Our names have 6 digits after run-. So pattern matches 6 chars: first digit 0-4, then any 5. That's 50% of names. Good. Case 5 negated: first digit not 0-4, i.e., 5-9, 50%. Good.

Case 3 pattern "??????" matches any 6 chars, all names. So all match. That's high hit, result 80k. Work includes '?' translation to '[^\/].' which is more complex. Good.

Case 2 pattern "run-9*" matches names starting with 9 after run-. Since numbers are random sequential with base offset, not exactly 10%? Our names are base+i sequential, so first digit distribution: if base random, roughly 10% start with 9. Good.

Case 1 all match.

Case 6 deep paths all match.

Case 8 exact literal: 150k loops, one match.

Need ensure no case takes >200ms. 150k regex matches on literal pattern might be ~50-100ms. 120k with wildcard ~100ms. Good. If too slow, but we can't test. We can reduce sizes if worried. The instruction says one call roughly 1ms to 200ms. 150k might be ~150ms. Fine. If >200ms, dropped? They keep 4 that do most work, but inputs over 1s dropped. 200ms target. 150k likely under 200ms. Python regex match on simple pattern ~0.5 microsec? Actually re.match on short string ~1-2 microsec. 150k * 1.5us = 225ms. Might be slightly over. To be safe, reduce max to 100k. But we want substantial work. Let's estimate: Python loop with regex match, 100k ~ 50-100ms. 150k ~ 75-150ms. Probably okay. But to be safe, use 120k max. Let's adjust:

- Case 1: 50k
- Case 2: 100k
- Case 3: 80k
- Case 4: 100k
- Case 5: 100k
- Case 6: 80k
- Case 7: 100k
- Case 8: 120k

Total names ~730k. Good.

But need "4 that do most work" - they will pick 4. Our cases vary. Fine.

Let's write final code.

Need import random only. Use module-level variables. The thunks return tuples.

Check the function signature: `filter(names, pat)`. So thunk returns `(names, pat)`. Good.

Let's produce code block.

One more thing: The task says "For keyword arguments the thunk returns call(...)". Here no kwargs. So simple tuples.

Also, "A method is called as a plain function: the thunk builds the instance and passes it as the first argument". Not applicable.

Write checks:
```
def checks():
    return [
        ("empty-names", lambda: ([], "/data/project/*")),
        ("single-match", lambda: (["/data/project/run-000001"], "/data/project/run-*")),
        ("none-pattern", lambda: (["/data/project/run-000001"], None)),
    ]
```
But note `filter` on empty names with pattern "/data/project/*" will compile pattern and cache. Then single-match uses different pattern. None raises. Fine.

Could include unclosed bracket instead of None? The instruction mentions None/odd type. I'll keep None.

Need ensure `_cache` not polluted with None? It raises before cache. Good.

Now final.