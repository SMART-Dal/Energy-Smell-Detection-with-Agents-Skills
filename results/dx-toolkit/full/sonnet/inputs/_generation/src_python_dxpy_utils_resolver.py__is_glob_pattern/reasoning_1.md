We need write cases for is_glob_pattern. Function simple: checks for unescaped * or ?. Workload: strings of realistic DNAnexus entity names, potentially long with backslashes. Need 8 measured inputs making substantial work. Function is O(n) mostly via get_last_pos_of_char which loops scanning from end, rfind each time. Worst case: many escaped '*' or '?' characters causing repeated rfind loops, i.e., string with many backslash-escaped stars. This makes O(k*n) potentially. Need inputs 1ms-200ms.

Let's construct strings. Realistic: paths/entity names. But to stress, long strings with many escaped '*' and '?'. get_last_pos_of_char: pos=len, loop: rfind char in string[:pos]; if found, count preceding backslashes; if even return; else continue with pos at that index, searching earlier. So escaped stars cause repeated searches. If string has many escaped stars (odd backslashes), each iteration scans prefix, causing O(n*k) where k number escaped occurrences. For 1ms-200ms, need maybe ~5000-50000 chars. Python slicing string[:pos] copies, so each iteration O(pos). If many escaped stars, total O(n^2) ~ 1e8 char copies maybe 50ms. Let's estimate: 20,000 chars with 10,000 escaped stars -> sum ~ 100M operations of slicing (C memcpy) maybe ~50ms. Good.

But also function calls get_last_pos_of_char twice: first '*' then '?'. If '*' found unescaped early at end, returns fast, not stress. To make both scan whole string, we need no unescaped '*' and no unescaped '?'; all escaped. So string with many "\*" and "\?" escaped. But careful: backslashes before star. For each star preceded by odd number of backslashes it's escaped. Pattern "\\*" in Python literal means backslash + star. If we have "\\*" repeated, each star preceded by one backslash, so escaped. But consecutive: "\*\\*" etc. Need ensure backslash counts. Simpler: build segments like "\\*" (backslash star) and "\\?" (backslash question). Between them maybe letters. Each star preceded by exactly one backslash (unless previous char is backslash, but segment ends with star, next segment starts with letter or backslash; if next starts with backslash, then star is followed by backslash not preceding). Fine.

But note: when searching for '*', rfind finds stars. For '?' search, it ignores stars. So both scan many occurrences. If string has k escaped stars and k escaped questions, each scan does k iterations of decreasing prefix. Total ~2*sum lengths ~ n^2. Good.

However function returns False for all escaped. Need also cases with unescaped at various positions, hits. Cases: long strings with no wildcards (full scan? get_last_pos_of_char rfind returns -1 quickly, O(n) C scan, fast). Long strings with one unescaped '*' at beginning: rfind scans whole string once O(n), then returns pos. Fast. To stress need many escaped then no unescaped. Also many escaped followed by unescaped near beginning: first rfind finds unescaped at beginning after scanning? Actually rfind searches from end, finds last '*' which if unescaped near beginning, then returns pos quickly after one scan, but scanning prefix length n. Fast O(n). The repeated loop only when many escaped stars after the unescaped? Wait loop starts at end, finds last star. If last star is unescaped returns immediately. If last star escaped, continue searching earlier, finds previous star, if escaped continue... So to force many iterations, all stars from end backward must be escaped until maybe an unescaped one. If unescaped at very beginning, still k escaped iterations. So yes.

We need 8 cases with different sizes and distributions. Need each call 1-200ms original. We can generate strings.

Also checks: 2-3 small edge inputs: empty string, single char, maybe None? Function expects string; None would raise TypeError in len. Checks may raise. Could include None. But "checked only for identical behaviour, never measured. These may raise." So okay. But is it safe? They call original and modified; if both raise same, fine. Include empty, "*", "\\*", None maybe. Need 2-3.

Cases exactly 8. Need realistic scale. Entity names in dx toolkit maybe paths like "/folder/name". But can be long? We can make strings of entity names with escaped wildcards. Realistic enough: names could contain backslashes? Not sure. But stress.

Let's design generator:

def _make(n_pairs, seed, extra=...):
    rng = random.Random(seed)
    parts = []
    for i in range(n_pairs):
        # random letters
        parts.append("".join(rng.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(rng.randint(0,5))))
        parts.append(rng.choice(["\\*", "\\?"]))
    # maybe trailing
    return "".join(parts)

This gives length ~ n_pairs*(avg 2.5 + 2) = ~4.5*n_pairs. For n_pairs=5000 -> 22,500 chars, 10,000 escaped wildcards. Each scan for '*' has 5000 stars -> sum lengths ~ 5000*~11000 = 55M; for '?' similar. Slicing copies maybe ~100M chars, ~20-50ms. Good.

Need 8 cases with varying n_pairs: maybe 1000, 2000, 4000, 6000, 8000, 10000, 12000, 15000. But max call <200ms. Let's be careful. 15000 pairs -> length ~67500, 15000 stars -> sum ~ 15000*33750=506M per char, two chars ~1B char copies. That might be >200ms, maybe ~1s. Need test mentally. Python string slicing of ~30k average * 15k = 450M bytes copied per get_last_pos, 900M total. memcpy ~10GB/s => 0.09s plus Python loop overhead 30k iterations negligible. So ~100ms. Could be okay. But also rfind scans prefix O(pos) in C, similar. Maybe 200ms. Let's cap at 10000 pairs. Need 8 distinct. Use sizes: 500, 1000, 2000, 3000, 4000, 5000, 7000, 9000. Also vary distribution: some all stars, some all questions, some mixed, some with long random letters, some with unescaped at very end/beginning? But need substantial work. Cases that don't stress might be fast (<1ms) and dropped; but requirement each should make function do substantial and different work. We can include cases with unescaped wildcard at beginning after many escaped, causing many iterations then return. Also cases with no wildcards but very long (fast, maybe <1ms) not good. We need 8 measured inputs; we want the 4 most work kept. But all 8 should be reasonable. Could include some with unescaped near end (fast) but then maybe dropped. Better all stress.

We can make cases:
1. many escaped stars only, size 3000 pairs
2. many escaped questions only, size 3000
3. mixed escaped stars/questions, size 5000
4. mixed with long random letters, size 4000
5. escaped then unescaped '*' at beginning, size 6000
6. escaped then unescaped '?' at beginning, size 6000
7. alternating escaped and unescaped? If unescaped near end, fast. Instead many escaped with occasional unescaped deep? To force loop until near beginning, place unescaped at index 0 after many escaped. That still does all iterations.
8. very large mixed 9000.

But note if unescaped '*' at beginning, get_last_pos_of_char('*') will iterate through all escaped stars then find unescaped at pos maybe 0 and return 0. Then is_glob_pattern returns True without calling '?' check. That halves work. Still substantial. For '?' unescaped at beginning but no '*' unescaped: first call scans all escaped stars (if any) returns -1, second scans all escaped questions then finds unescaped at 0 returns 0 -> True. Good.

Need avoid building all inputs >10s. Generating 8 strings with total maybe 50k-100k chars trivial.

Need ensure strings don't contain unescaped stars accidentally. Our generator uses "\\*" and "\\?" segments. But if a segment ends with backslash? No. If random letters include backslash? No. Good.

But careful: consecutive segments "\\*" + "\\?" gives "\\*\\?" -> characters: backslash, star, backslash, question. Star preceded by one backslash -> escaped. Question preceded by one backslash -> escaped. Good.

If we append unescaped at beginning: "*" + generated. Then first char star unescaped, but rfind finds last star (escaped) first, loops through all escaped, then finds star at 0, backslashes before 0 = 0 even, returns 0. Good. But wait the generated string has many escaped stars; the last star is escaped, so loop continues. Eventually reaches star at 0. Good.

Also need maybe strings with even number of backslashes before star (unescaped). Could create "\\\\*" (two backslashes then star) which is unescaped. But not necessary.

Realistic data: entity names might be like "file.txt" no wildcards. But stress is fine.

Need define module-level _make functions and precompute all strings. Thunks return (string,). Since function doesn't mutate, can return same string.

Need import from dxpy.utils.resolver import is_glob_pattern. But importing resolver may import dxpy which may require network? The task says import it as shown. But resolver imports dxpy, cli etc. Could importing fail due to missing dependencies? We must assume repository available. But potential issue: dxpy import may need config? Usually import okay. We don't call other functions. We'll import.

But note module has `from ..cli import try_call, INTERACTIVE_CLI`; cli may import things. Should be fine.

We need write code only. Use random.Random(0) fixed seed. Build all cases at module level.

Let's design a helper:

def _escaped_string(n_pairs, seed, chars="*?"):
    rng = random.Random(seed)
    parts = []
    for _ in range(n_pairs):
        # random alphanumeric prefix length 0-6
        L = rng.randint(0, 6)
        if L:
            parts.append("".join(rng.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(L)))
        c = rng.choice(chars)
        parts.append("\\" + c)
    return "".join(parts)

For stars only, chars="*". For questions only, chars="?".

For mixed with long letters, use L up to 10.

For unescaped at beginning: "*" + _escaped_string(...). But if generated has escaped stars, fine. For question: "?" + _escaped_string(..., chars="?").

But for case 5, if we prepend "*", then get_last_pos_of_char('*') returns 0 after loops. Good. For case 6 prepend "?" with only escaped questions, first '*' search returns -1 (no stars), then '?' search loops and returns 0. Good.

Need ensure no accidental unescaped '?' or '*' elsewhere. We only use escaped segments.

Potential issue: In Python string literals, "\\*" is backslash + star. Good.

Let's create cases:
- ("escaped-stars-2000", lambda: (_S1,))
- ("escaped-questions-2000", lambda: (_S2,))
- ("mixed-4000", lambda: (_S3,))
- ("mixed-long-5000", lambda: (_S4,))
- ("star-unescaped-start-6000", lambda: (_S5,))
- ("question-unescaped-start-6000", lambda: (_S6,))
- ("dense-mixed-8000", lambda: (_S7,))
- ("very-dense-mixed-10000", lambda: (_S8,))

Need ensure each call time not >1s. Let's estimate worst S8: n_pairs=10000, avg letters 3, length ~ 10000*(3+2)=50000 chars. Number of stars ~5000, questions ~5000. For '*' search: 5000 iterations, each rfind scans prefix average length 25000 -> 125M char scans, plus slicing copies 125M. For '?' similar. Total ~500M char operations. In C, memcpy/rfind ~ maybe 0.05-0.1s. Python loop 10000 iterations negligible. So <200ms likely. Good.

S7 n=8000 -> ~32M? Actually 4000 stars * avg 16000 = 64M per char, total 128M. ~20ms. Good.

S5 n=6000 stars only, length ~ 6000*(3+2)=30000, 6000 stars. For '*' search loops 6000 iterations avg 15000 = 90M. Then returns 0, no '?' call. ~20ms. Good.

S6 n=6000 questions only, length ~30000. First '*' search: rfind '*' returns -1 after scanning full string once O(30k) fast. Then '?' search loops 6000 iterations avg 15000 = 90M. ~20ms. Good.

S1 n=2000 stars only length ~10000, 2000 iterations avg 5000 = 10M. ~2ms. Good.

All above 1ms? S1 maybe 1-2ms. Fine. But requirement one call roughly 1ms to 200ms. S1 maybe 2ms. Good.

Could add a case with no wildcards but very long to test fast path? But would be <1ms and dropped. Not needed. We need 8 measured; they keep 4 most work. So fine.

Checks: 
- ("empty", lambda: ("",))
- ("single-star", lambda: ("*",))
- ("none", lambda: (None,))
Maybe also escaped single char. 3 max. Use empty, escaped-star, None.

Need ensure checks may raise; None will raise TypeError in len. Original and modified both. Fine.

Now output code. Need import random and is_glob_pattern. Module-level build.

One subtlety: The function under test is `is_glob_pattern` imported directly. The thunk returns tuple of args. So lambda: (_S1,) etc.

Let's write.

Double-check generator: For chars="*", c = "*", parts.append("\\" + c) -> "\\*". Good. For mixed, rng.choice("*?") returns single char. Good.

For unescaped at beginning, we do "*" + _escaped_string(6000, seed, "*"). But then the string begins with unescaped star, and all other stars are escaped. Good. However the last star in string is escaped, so loop goes through all. At the end, finds star at index 0. The backslashes before index 0 = 0 even -> returns 0. Good.

For question case: "?" + _escaped_string(6000, seed, "?"). The first call for '*' scans entire string rfind('*') returns -1. Then '?' call loops through all escaped questions, then finds '?' at index 0 returns 0. Good.

Need maybe vary seeds. Use seeds 0..7.

Let's produce final code block.