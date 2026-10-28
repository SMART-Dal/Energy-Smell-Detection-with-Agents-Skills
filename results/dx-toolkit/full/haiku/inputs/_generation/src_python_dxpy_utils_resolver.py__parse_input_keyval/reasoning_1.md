Let me think about the function. `parse_input_keyval(keyeqval)` takes a string like "name=value" and returns (name, value).

The functions get_first_pos_of_char and split_unescaped are O(n^2)-ish (slicing strings in a loop with rfind). Actually get_first_pos_of_char does `string[:pos].rfind(char)` repeatedly, which creates copies -> O(n^2). So a long string with many '=' characters or many backslashes will be slow.

We need 8 cases, realistic, taking ~1ms to 200ms.

Realistic inputs: command line -i flags like "name=value". Names like "reads=file.fastq", "value={\"key\": \"hello world\"}" etc. Values can be JSON, long.

Let's design:

1. Simple typical: "input1=somefile.txt"
2. Long value: "reads=" + large text (e.g. big JSON string) - many chars, one '='.
3. Many '=' in value: "name=a=b=c=d=..." 
4. Many escaped '=': "name=a\\=b\\=c..." escapes in the value.
5. Many backslashes before '=': "name=" + "\\" * n + "=value" 
6. Long name with '=' characters.
7. Long string with no '=' at all -> raises DXCLIError... but that's actually a case; can't be measured? It must run to completion on original. Raising is... "Every case must run to completion on the original function without raising." So cases must not raise. Checks can raise.

So all cases must contain at least one unescaped '='.

Let's think about complexity. get_first_pos_of_char: pos starts at len; loop: string[:pos].rfind(char). Each iteration reduces pos to the found position. So for a string with k occurrences of char, it loops k times, each doing an O(n) slice + rfind => O(k*n). If the string is length n with k '=' occurrences all over, and there are backslashes... Actually first_pos ends up as the first unescaped occurrence.

Wait, the loop continues even after finding first_pos? It sets first_pos = pos and continues searching in string[:pos], so it finds earlier occurrences. The loop ends when rfind returns -1. So it always scans all occurrences.

Then split_unescaped calls get_last_pos_of_char repeatedly on string[:lastpos] -> also O(k*n) probably.

So worst case string with many '=' => quadratic in n. E.g. n=100000 with 50000 '=' -> 50000 * ... too slow potentially. Let's keep n moderate.

Let's estimate: with n=20000 and k=10000 '=', get_first_pos: each rfind on slice of average length ~10000 costs ~10us? Actually rfind is fast C. Slicing costs O(n). 10000 iterations * 10000 chars = 1e8 char copies => maybe 50ms. That's fine. But the actual rfind checks... fine.

Actually get_last_pos_of_char - let's check its likely implementation. Not given but presumably similar. split_unescaped loops: pos = get_last_pos_of_char(char, string[:lastpos]), each call scans. So for k '=' chars it's also O(k*n).

Let's aim for cases with 10k-100k length strings, moderate number of '='.

Let's also consider backslash scanning: get_first_pos_of_char counts backslashes before each '=' via a while loop -> O(number of backslashes adjacent). A string of many backslashes then '=' could be slow: for the single '=', counting backslashes is O(n) once. Not too bad.

Better: many '=' each preceded by a long run of backslashes would be quadratic. E.g. "\\"*m + "=" repeated. Let's make one case: value with lots of escaped equals: "a\\=b" repeated.

Hmm, careful: escaped '=' means odd number of backslashes before. "\\=" in Python source is a backslash followed by '='. So string like "name=v\\=x" — first '=' at pos 4 unescaped. Fine.

To make it stress, many occurrences of '=' with escapes.

But requirement: must run without raising. parse_input_keyval only raises if no unescaped '=' found? Actually if first_eq_pos == -1 it raises bare `raise` inside try -> caught -> raises DXCLIError. So we need at least one unescaped '='.

Also note: split_unescaped result is a list; value = keyeqval[first_eq_pos+1:]. Returning tuple of two strings. Output under 100k values, fine.

Now, the important thing: the timing compares original vs modified. The modified version presumably optimizes. We want the workload to actually exercise the code. Since this is a tiny function, the workload must be big strings.

Let's design 8 cases:

1. "simple-short": "name=value"
2. "typical-file": "reads=/path/to/file.fastq.gz"
3. "long-value-json": "config=" + json.dumps(big dict)
4. "many-equals-value": "opts=a=b=c=..." (say 5000 pairs) length ~20000
5. "escaped-equals": value with many "\=" sequences
6. "many-backslashes": "name=" + "\\"*5000 + "=x" ... hmm escaped? first '=' is at pos 4. Fine.
7. "long-name", "long-value" symmetric? Let's make a long name with many '=' escaped, then final '=': e.g. ("a\\=" * 5000) + "=value".
8. no-escape large: "a=" + "=x"*... 

Let me just craft varied strings.

Let me think about sizes to hit ~1-200ms. Given quadratic behavior, let's test conservatively. n up to ~20000-50000 with many '=' chars.

Actually let's reconsider: the rfind approach. For a string of length n with k '=' occurrences, get_first_pos_of_char does k iterations, each slicing string[:pos] which is O(pos). Sum of positions ~ k*n/2 in worst case. With n=20000, k=10000, that's 1e8 char copy bytes — fast in C, maybe ~30-50 ms plus python loop overhead of 10000 iterations (negligible ~1ms). Hmm actually slicing 10000 times of average 10000 chars = 1e8 bytes = 100MB copying, ~50ms. OK.

split_unescaped similarly does k iterations calling get_last_pos_of_char each of which itself... get_last_pos_of_char maybe O(n) similarly. So combined maybe 2-3x.

Let's target n around 20000 with dense '='. That should be well within range.

Also: a case with no '=' would raise -> not allowed in cases. Checks can have that.

Checks (2-3 small edge inputs, may raise):
- empty string "" -> raises
- "=value" -> name empty, value "value"; returns ("", "value"). Actually get_first_pos_of_char returns 0, split_unescaped... words: with include_empty_strings=False, splitting "=value" -> hmm. Let's not worry; it runs.
- "novalue" (no '=') -> raises
- "name=" -> returns ("name", "")? first_eq_pos=4, split_unescaped('=', "name=") -> words=["name"]? Actually splits at pos 4, string[5:5] empty not included, then string[:4]="name" appended... lastpos=4 != 0 so append "name". words=["name"]. So [0]="name". value = keyeqval[5:] = "". return ("name","").

Check with odd type None? "An odd type" - passing None raises TypeError from get_first_pos_of_char (len(None)). That's a check maybe. But careful: it's caught by the except -> DXCLIError. Actually `get_first_pos_of_char('=', None)` -> len(None) raises TypeError, caught by except, raise DXCLIError. OK so it raises DXCLIError. Both original and modified presumably behave same. Hmm but if modified changes exception... risk. Keep it to string cases mostly; maybe include one None? The instruction says checks may raise. I'll include empty, no-equals, and one weird (just "="?). Let's do:
- "" (raises)
- "no-equals-here" (raises)
- "=" -> first_eq_pos=0, split_unescaped('=', "="): words: pos=1, lastpos=1; get_last_pos_of_char('=', "=") -> 0; pos=0 >=0; pos+1 == lastpos (1==1) and not include_empty -> skip; lastpos=0. loop: pos=0 >=0; get_last_pos_of_char('=', string[:0]="") -> -1. exit. lastpos==0 and not include_empty -> don't append. words=[] reversed=[]. So split_unescaped(...)[0] -> IndexError -> caught -> DXCLIError. So "=" raises. Good edge case.

Actually maybe better to have checks that include a name-empty valid case: "=value" returns ("", "value"). Let's verify: keyeqval="=value", first_eq_pos=0. split_unescaped('=',"=value"): lastpos=7, pos=7; get_last_pos_of_char('=',"=value") -> 0. pos=0>=0. pos+1=1 != lastpos=7 -> append string[1:7]="value". lastpos=0. loop pos=0>=0: get_last_pos_of_char('=', string[:0]="") -> -1. exit. lastpos==0 and not include_empty -> don't append. words=["value"] reversed -> ["value"]. [0]="value". value=keyeqval[1:]="value". return ("value","value"). Interesting.

OK.

Now, do I need to worry about the `raise` bare statement inside the try when first_eq_pos == -1? `raise` with no active exception raises RuntimeError; caught by except -> DXCLIError. Fine.

Now build cases. Let's make realistic-looking CLI inputs plus stress.

Let me write helper to build strings.

Cases:

1. ("simple", "reads=reads.fastq.gz")
2. ("json-value", "config=" + json.dumps(...)) with nested dict, maybe 5-20k chars.
3. ("many-equals", "opts=" + "k=v&"*... ) value containing many '='.
4. ("escaped-equals", "name=" + "a\\=b"*N) — many escaped '=' in value. But wait: escaped '=' are still found by rfind; get_first_pos_of_char will iterate over all of them and count backslashes. Good stress for the backslash loop.
5. ("leading-backslashes", "\\"*N + "=value")? Then first_eq_pos: the '=' preceded by N backslashes. If N even -> unescaped -> first_eq_pos = N. if N odd -> escaped -> keep searching earlier... there is no earlier '=' -> returns -1 -> raises. So use even N. But also this makes value = keyeqval[N+1:] = "value". Fine. Stress: get_first_pos_of_char iterating: it finds pos=N, counts backslashes O(N). Then searches string[:N] which has no '=' -> rfind -1 done. So O(N) once. Not super quadratic. 

Better: "a=" + "\\"*m + "=" + ... hmm.

Actually, the backslash counting loop: for each '=' occurrence, it counts preceding backslashes. If all '=' occurrences are preceded by many backslashes, cost = sum of backslash run lengths per '='. To make quadratic, pattern: each '=' preceded by a long run of backslashes that grows. E.g. "=" + "\\"*1 + "=" + "\\"*2 ... total O(n^2/...). Let's just do: value = ("=" + "\\"*20) * 5000. Then each '=' has 20 preceding backslashes (odd -> escaped). But then no unescaped '=' at all? The pattern "=\\\\...=" — each '=' is followed by backslashes then '='. The '=' at position 0 preceded by 0 backslashes -> unescaped! Good, that's first_eq_pos=0. But then name = split_unescaped[0]... wait split_unescaped splits at unescaped '='; the '=' at pos 0 is unescaped so split there. Hmm.

Actually careful: pattern "=\\=\\=" — '=' at 0 preceded by 0 backslashes (even) -> unescaped. So first_eq_pos = 0. Fine.

Let me instead use a leading name: "name" + "=\\="*... hmm.

Simpler: 
case "escaped-equals": keyeqval = "input=" + "\\="*3000 -> that's backslash-equals repeated. The first '=' is at pos 5 (unescaped). Then the rest are escaped (preceded by 1 backslash each). get_first_pos_of_char: pos=len; rfind finds last '=', count 1 backslash -> odd, not unescaped, continue. Iterates over 3000 '=', each O(1) backslash counting, each with a slice O(n). So O(k*n) = 3000 * 12000 = 3.6e7. Fine.

Then split_unescaped: also loops.

case "many-equals-value": "opts=" + "k=v;"*3000. Then '=' occurrences: one at pos 4, plus 3000 in value. get_first_pos_of_char iterates 3001 times. Similar cost. But note first_pos ends at 4 (the earliest unescaped). Fine.

Hmm, but wait: does get_first_pos_of_char stop early? No, it continues scanning to bottom. So all occurrences scanned.

case "long-value-no-eq": "name=" + "x"*100000 -> only one '='; rfind on full string once -> O(n). split_unescaped: get_last_pos_of_char on full string -> O(n), then on string[:pos] -> no '=' -> done. So O(n) total, fast. 100k chars ~ maybe 0.1ms. Actually that's cheap. Maybe not a good workload, but it's a realistic long value (a huge JSON). Combined with some '='? Let's include as diversity though it may be dropped.

Actually the runner keeps the 4 that do the most work. So we just need 8 diverse ones; 4 will be chosen. Fine.

Let's make sure each takes at least ~1ms ideally.

Let me estimate n and k for ~10-50ms.

Given the quadratic, k*n ~ 1e8 gives maybe 50-100ms.

Let me pick:
- many-equals: "opts=" + "k=v;"*4000 -> n ≈ 5 + 4*4000=16005, k=4001. k*n ~ 6.4e7. Each iteration: slice of avg ~8000 chars = memcpy 8KB *4000 = 32MB -> ~10-20ms. Plus split_unescaped similar. Total maybe 30-50ms. Good.
- escaped-equals: "input=" + "\\="*8000 -> n≈5+16000=16005, k=8001. Similar.

- json-value: "config=" + json of nested structure ~ maybe 20KB, contains '='? unlikely many. One '=' at pos 6. Cheap. Maybe use a value with many '=' from a query string.

- something with backslashes runs: "path=" + "\\\\"*2000 + "=" ... hmm.

Let's craft a case: "expression=" + "a\\=b"*3000 where each '=' is preceded by 1 backslash (escaped). Same as escaped-equals basically.

Case with deep backslash runs: keyeqval = "name" + "".join("\\"*(2*i) + "=" for i in range(1, 300))? Each '=' preceded by even backslashes -> unescaped. Then get_first_pos_of_char will count backslashes for each '=': sum 2*i = O(m^2) where m~300 -> 90000 ops, plus slices O(m*n)... n ~ sum 2i ~ 90000. That's big. Hmm, 300 iterations with slices avg 45000 -> 1.35e7. Fine. But the backslash counting sum ~ 90000, trivial.

Let's not overcomplicate. Maybe a pattern that's genuinely quadratic in backslash counting: each '=' preceded by an increasing run from a common base... Actually the run before each '=' is independent.

Consider keyeqval = ("a" + "\\"*m + "=") * t. Each '=' preceded by m backslashes. Total n = t*(m+2). Cost of backslash counting = t*m. If we set t*m ~ 1e6 and n = t*(m+2). With m=100, t=10000 => n=1.02e6, backslash counting 1e6. Slices: t iterations * n/2 avg = 10000*510000 = 5.1e9 - too slow. So slices dominate.

OK so slices dominate always. So controlling k*n is key. Keep k*n under ~2e8 total for ~100ms. Let's keep around 5e7-1e8.

Let me define cases with explicit sizes and verify roughly.

Plan for 8 cases:

1. "typical-file" — short, ~20 chars. (may be dropped)
2. "json-config" — value is a JSON blob of moderate size (say 30KB) with one '='. Cheap-ish but realistic.
3. "dense-equals" — "opts=" + "k=v;"*5000, n~20005, k~5001 -> 1e8. ~maybe 50ms.
4. "escaped-equals" — "input=" + "\\="*10000, n~20005, k~10001 -> 2e8. Might be ~100ms. Let's use 6000.
5. "long-name-dense" — dense '=' in name portion after escaping? e.g. "a\\=b\\=c..." then final "=value". Actually name computed by split_unescaped[0]. Let's do: "n" + "\\="*5000 + "=value". first unescaped '=' is the final one. Similar cost.
6. "many-backslashes-value" — "name=" + "\\"*20000 + "x" (value with huge backslash run, no more '='). Cheap (one '='). But rfind scanning... only 1 '='. Cheap. Include for diversity.
7. "query-string" — "url=" + "a=1&b=2&..."*N with many '='.
8. "huge-single-value" — "name=" + random printable chars length ~50000 including some '='? random chars with a few '='.

Hmm. Let's simplify and make 8 concrete.

Actually since only 4 fastest... er, "keep the 4 that do the most work" — most work. So the heavy quadratic ones matter most. The others can be diverse but will be dropped. That's fine, requirement is exactly 8.

But each must run without raising and produce output. Fine.

Let me be careful about performance runaway for the dense ones: if original takes >1s it gets dropped... actually "Inputs where one call takes over 1 s are dropped." Dropped from the 4? It says dropped. Better to stay safely under 200ms.

Let me be conservative: target k*n ≈ 2e7-5e7.

dense-equals: "opts=" + "k=v;"*3000 => n = 5+12000 = 12005, k=3001 -> 3.6e7. Good, maybe 15-30ms.
escaped-equals: "input=" + "\\="*5000 => n=10005, k=5001 -> 5e7. ~30ms.

Wait, but in escaped-equals, is the '=' after backslash escaped? Yes, 1 backslash -> odd -> escaped, so first_pos remains the leading one at pos 5. But all 5001 occurrences scanned. Fine.

Let me also add a case where there's NO unescaped '=' except... no, must have.

Case "trailing-escaped": "name=value" + "\\="*2000 -> '=' at pos 4 unescaped. rest escaped.

Hmm these are similar. Let's diversify:

Let's designate:
A. simple: "reads=reads.fastq.gz"
B. long-value-json: "config=" + json.dumps(nested)
C. dense-equals: value with many '=' separators: "opts=" + "key=val;"*3000
D. escaped-equals: "input=" + "\\="*5000
E. leading-escapes: "path=" + "\\"*4000 + "\\=x"  wait need unescaped '=' earlier. "path=..." the first '=' at pos 4 is unescaped. Then value has backslashes and an escaped '='. Hmm, get_first_pos_of_char: finds last '=' (escaped, preceded by 1 backslash? "\\\\=x" in python source is "\\=x"? Let's just construct with string concat.)

Let me use explicit: value = "\\" * 4000 + "=" + "x" -> that's 4000 backslashes then '=' then x. That trailing '=' is preceded by 4000 (even) backslashes -> unescaped! So first_pos would be that one, not pos 4. Because the loop finds LATER occurrences first and keeps updating first_pos to earlier ones. Wait the loop scans from the end backwards; first_pos gets set to each unescaped occurrence found, ending at the earliest. So first_pos = 4 eventually. But the scanning still processes the later one.

Keyeqval = "path=" + "\\"*4000 + "=x": n=6+4000+2=4008. '=' at pos 4 and at pos 4005. get_first_pos: pos=4008, rfind -> 4005, count 4000 backslashes (even) -> first_pos=4005. loop: string[:4005].rfind('=') -> 4, count 0 -> first_pos=4. loop: string[:4]="path".rfind -> -1. done. cost: 4000 backslash chars scanning + slices. Trivial, ~microseconds.

Better to make it heavier: repeat the pattern: "path=" + ("\\"*20 + "=")*3000 + "x". Each '=' preceded by 20 backslashes (even -> unescaped). n = 6 + 21*3000+1 ≈ 63007, k=3001. Slices costly: 3001 * 31500 = 9.4e7. Good ~40ms. Plus backslash counting 3001*20=60000 trivial.

F. name-heavy: "a\\=b"*? Let's do keyeqval = ("n\\=x"*3000) + "=value". Wait '=' escaped in name part, final '=' unescaped. first unescaped is the final one near end. n ≈ 4*3000+6=12006, k=3001. Similar cost. The name is split_unescaped[0] which is long.

G. url query: "url=" + "&".join("k%d=v%d"%(i,i) for i in range(4000)) -> n ~ many, k=4000. cost ~ 4000*~40000/2=8e7? n ≈ 5 + sum(len("k%d=v%d"&) ) ≈ 4000*(3+1+4+1)~... let's compute: "k1234=v1234&" ~ 11 chars, so n≈44000. k*n/2 = 4000*22000=8.8e7. ~40ms.

H. no-equals-long: "name=" + "x"*200000 -> n=200005, k=1. get_first_pos: rfind once O(n) then done -> 1 slice of 200k. split_unescaped: get_last_pos_of_char on 200k... then on string[:4]. O(n) total. ~sub-ms. Cheap but diverse. Might be dropped. Maybe instead make it value with a few '=' far apart. Eh, include.

Actually, let's also consider that get_last_pos_of_char implementation unknown; likely similar. Fine.

Let me cap sizes so total memory fine (all strings tiny relative to 100MB).

Let me now write code.

```python
import json
import random

from dxpy.utils.resolver import parse_input_keyval


def _json_config(n_items, seed):
    rng = random.Random(seed)
    obj = {
        "name": "workflow-input",
        "items": [
            {"id": "item%d" % i,
             "value": rng.choice(["alpha", "beta", "gamma"]) + "-" * rng.randint(1, 5) + str(rng.randint(0, 10**6)),
             "count": rng.randint(0, 10**6),
             "nested": {"a": rng.random(), "b": [rng.randint(0, 9) for _ in range(rng.randint(0, 4))]}}
            for i in range(n_items)
        ],
    }
    return json.dumps(obj)


_SIMPLE = "reads=reads.fastq.gz"
_JSON = "config=" + _json_config(150, 0)
_DENSE = "opts=" + "key=val;" * 3000
_ESCAPED = "input=" + "\\=" * 5000
_BACKSLASH_RUNS = "path=" + ("\\" * 20 + "=") * 3000 + "x"
_NAME_ESCAPED = ("n\\=x" * 3000) + "=value"
_QUERY = "url=" + "&".join("k%d=v%d" % (i, i) for i in range(4000))
_LONG = "name=" + "x" * 200000


def checks():
    return [
        ("empty", lambda: ("",)),
        ("no-equals", lambda: ("plainvalue",)),
        ("equals-only", lambda: ("=",)),
    ]


def cases():
    return [
        ("simple", lambda: (_SIMPLE,)),
        ("json-config", lambda: (_JSON,)),
        ("dense-equals", lambda: (_DENSE,)),
        ("escaped-equals", lambda: (_ESCAPED,)),
        ("backslash-runs", lambda: (_BACKSLASH_RUNS,)),
        ("name-escaped", lambda: (_NAME_ESCAPED,)),
        ("query-string", lambda: (_QUERY,)),
        ("long-value", lambda: (_LONG,)),
    ]
```

Wait: _JSON value contains characters like '"' and ':' etc. Does it contain '='? json.dumps won't produce '='. first '=' at pos 6. fine.

Check _BACKSLASH_RUNS: "path=" then ("\\"*20 + "=") repeated. In Python source "\\"*20 is 20 backslashes. Then '='. So string is path=<20 backslashes>=<20 backslashes>=... The '=' at pos 4 unescaped, then subsequent '=' each preceded by 20 backslashes (even) -> unescaped. Good, weighted. Ends with "x". first_eq_pos=4.

Check _NAME_ESCAPED: "n\\=x" in source is n backslash = x. So "n\=x" repeated: '=' preceded by 1 backslash -> escaped. Then final "=value". get_first_pos: scans from end: final '=' at position len-6? preceded by 'x' -> 0 backslashes -> unescaped, first_pos set. continue searching earlier: each escaped '=' -> not unescaped. eventually -1. So first_pos = index of final '='. Then name = split_unescaped('=', keyeqval)[0]. split_unescaped will split at final '=', words: [everything before final '='] since the escaped ones not split. include_empty false: string[pos+1:lastpos] = "value". lastpos=pos. Then continue; string[:lastpos] contains only escaped '=' -> no split -> append whole prefix. words reversed -> [prefix, "value"]. [0]=prefix = the name. Good, returns (long_name, "value"). Output: one long string ~12000 chars. Under 100k values fine.

Hmm but is that "realistic"? Names with escaped equals... eh, it's a stress. Fine.

Check _ESCAPED: "input=" + "\\="*5000. '=' at pos 5 unescaped (preceded by 't'). Then 5000 escaped '='. first_pos=5. split_unescaped: splits at pos 5. value = keyeqval[6:] = the escaped equals string. name = "input". Fine.

Check _DENSE: "opts=" + "key=val;"*3000. '=' at 4 unescaped, then 3000 '=' each preceded by 'y' -> unescaped. first_pos=4. name: split_unescaped splits at all '=' -> many words; [0] would be "opts". Good. value = keyeqval[5:]. Good.

Check _QUERY: "url=" + "k0=v0&k1=v1&...". '=' at 3. then many. name: first word "url". Fine.

_LONG: "name=" + "x"*200000. value huge string 200k chars. Output tuple ("name", 200k string). One output value ~200k chars, under 100k values? "keep what it returns ... under about 100 000 values" — values here means elements; a string of 200k chars is one value. Should be fine; though rendering arguments compares... arguments rendered before/after: keyeqval is 200005 chars rendered as a string — that's fine.

Hmm, actually the instruction says keep each input's data under 1,000,000 values. A string of 200k chars is one value. OK.

Now the total memory is trivial.

Let me double check checks: "=value"? no I used "=". Fine.

cheks: ("empty", lambda: ("",)) -> raises DXCLIError. ("no-equals", ("plainvalue",)) -> raises. ("equals-only", ("=",)) -> raises per analysis. Hmm, three raising cases. Maybe include one that doesn't raise for variety? Not needed—checks just compare behavior; raising is allowed and both should raise identically. But if modified version fixes the empty-split bug (maybe the optimization changes exception type)... risk. Let's include a non-raising edge too: ("equals-only-value", lambda: ("=value",)) returns ("value","value"). Actually that's weird but valid. Let me swap "equals-only" for "key-empty-value-empty": ("=") hmm.

I'll do 3 checks:
- empty string -> raises
- no-equals -> raises
- "name=" -> returns ("name", "")  (non-raising)

Both consistent likely.

Hmm, but "empty" raising: original raises DXCLIError. Modified presumably same. OK.

Actually let me reconsider using "=": the modified implementation might handle empty name differently. Safer to use edge cases where behavior is well-defined: empty string (raises), no equals (raises), "name=" (returns). Let's use those 3. Maybe add "a=b=c" but that's a normal case already covered.

Let me finalize with 3 checks.

One more consideration: the thunk returns a tuple of positional args: `lambda: ("",)`. Good.

Now sizes: let me re-estimate work more carefully to ensure at least some cases are ~10-100ms but none >1s.

Cost per iteration of get_first_pos_of_char's loop: `string[:pos].rfind(char)`. Slicing creates a copy of pos bytes; rfind scans. Python overhead small. For pos ~ n.

_DENSE: n=12004, k=3001. Sum over found positions: rfind finds positions from the end down. Actually rfind searches string[:pos] and finds the LAST occurrence before pos. So positions decrease: first pos=12004 -> finds last '=' near end, then string[:that] etc. So positions roughly n, n-4, n-8, ... decreasing by 4 each. Sum ≈ k*n - 4*k^2/2 ≈ 3001*12004 - 2*9e6 = 3.6e7 - 1.8e7 = 1.8e7 bytes copied. That's ~20MB. Fast (<10ms). Plus backslash counting trivial. Then split_unescaped: get_last_pos_of_char repeated similarly — maybe another 20MB. Total maybe 20-40ms. Good.

_ESCAPED: n=10005, k=5001, step 2. Sum ≈ 5001*10005 - 2*(5001^2)/2 = 5e7 - 2.5e7 = 2.5e7. fine.

_NAME_ESCAPED: n=12006, k=3001 but most escaped; step 2 for the escaped ones. Similar 2.5e7. Plus the final unescaped split_unescaped processes entire string too. Fine.

_QUERY: n~? "k{i}=v{i}&" for i in 0..3999. lengths 2-4 digits. ~ 4000*8? Let's say avg "k123=v123&" = 10 chars -> n≈40005, k=4000, step ~10. Sum ≈ 4000*40005 - 10*(4000^2)/2 = 1.6e8 - 8e7 = 8e7. ~80MB copies + rfind scans. Could be ~100-200ms. Hmm, rfind itself scans too (over the slice) so 2x. Might approach 200ms. Let's reduce to 2500 -> n~25000, k=2500, sum ≈ 6.25e7 - 3.1e7=3e7. Safe. Use 2500.

Actually let me reduce all a bit to be safe. The point is they should be in 1-200ms; being slightly fast is okay because 4 will be picked.

Let me set:
- dense: "key=val;"*2500 -> n=10004, k=2501, sum≈2.5e7-6e6=1.9e7... eh ~few ms. Hmm maybe too fast. Let's keep 3000.

Honestly, hard to predict; let's aim moderate. Use 3000-4000.

I'll go with the numbers above, reduce query to 3000.

Also consider split_unescaped's inner get_last_pos_of_char — unknown implementation but presumably also O(n) per call, so total doubles.

Let's finalize.

Actually also: get_first_pos_of_char counts backslashes per found '=' via while loop; for _BACKSLASH_RUNS each '=' has 20 backslashes -> 3001*20=60000 iterations, trivial.

Let me reduce _BACKSLASH_RUNS backslash run to 20 but count 3000 -> fine.

Final code. Also need WORKDIR? Not needed, no files.

Import: `from dxpy.utils.resolver import parse_input_keyval`. But importing dxpy.utils.resolver triggers imports of dxpy, .describe, ..cli, ..exceptions — should be available since it's the repo. Possibly dxpy imports heavy stuff but that's setup, not timed. Assume it works.

Should I worry that importing resolver needs DXPY config? The task says the repo is available. Runtime setup before timing. Fine.

Write it.