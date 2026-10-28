I need to reduce sizes. The big dicts are too slow (json parsing 50k keys ~2.7s). Let me shrink. Also the long escaped-colon strings are too slow (split_unescaped on 100k escaped colons ~2.3s).

Let me recalibrate. json-list-append with 150k ints was ok (under 1s). Let's estimate: 150k ints JSON parse ~ maybe 0.1s. Hmm, but 50k dict keys took 2.7s? That seems disproportionate. Actually object_pairs_hook=OrderedDict makes parsing slow. 50k OrderedDict entries... each key parse plus OrderedDict construction. 2.7s for 50k seems high but plausible with object_pairs_hook overhead.

Let me reduce dict to maybe 5,000 entries. That's 10x less -> ~0.27s. Good.

For the escaped-colon string: 100k "a\:b" = 100k colons. split_unescaped 2.3s. Reduce to 10k -> 0.23s. Good.

But wait, for spec-string-long, the input_class is 'string', so split_unescaped is still called first (val_substrings = split_unescaped(':', input_value)). Yes. So reduce.

For json-string-resolve, _LONG_PLAIN_JSON 300k chars - that was ok. Fine.

Let me also think: json-list-append 150k ints ok. Keep.

Now let me make sure each case does substantial but different work and stays under 1s.

Let me set:
- _BIG_DICT: 5,000 entries for dict cases.
- Actually I want different sizes for diversity but all under 1s.

Let me define:
- _DICT_5K = 5,000 keys
- _DICT_8K = 8,000 keys

For escaped colon string: 10,000 repeats.

Let me reconsider the json-dict-set case: no spec, unknown class, "meta" slot is a string "sentinel" (non-list) so parsed dict is set. json.loads with OrderedDict hook. 5k keys ~0.27s. Fine.

spec-hash-append: input_class 'hash' -> json.loads(input_value) without hook (default dict). 5k keys faster. Fine.

spec-arrayhash-append: json.loads default dict. Fine.

Actually let me use larger for the non-hook ones since they're faster. But simpler to keep same sizes.

Let me estimate json.loads default of 5k-entry dict: maybe 0.02s. Very fast. Could go bigger, say 50k -> 0.2s. Hmm but I need to be safe.

Let's be conservative:
- dict with hook (OrderedDict): 5,000 keys
- dict without hook: 20,000 keys

For escaped colon: 10,000 repeats.

Let me just write it.

Also need to double check job-jbor passed, json-list-append passed, json-string-resolve passed. Keep those.

Let me write final.

Actually, let me reconsider json-string-resolve: _LONG_PLAIN_JSON = json.dumps(300k char string) -> ~300k chars, parse ok. Keep.

Let me now write the code.

For diversity, I'll keep 8 cases:
1. json-list-append (ok) - 150k int list
2. json-dict-set - 5k dict with hook, non-list slot
3. spec-hash-append - 20k dict without hook, appended
4. spec-arrayhash-append - 20k dict without hook, appended (different slot, array)
5. json-string-resolve (ok)
6. spec-string-long - 10k escaped colons
7. job-jbor (ok)
8. name-colon-file-resolve - 10k escaped colons

Hmm 3 and 4 are similar. But they exercise the same code path. Let me differentiate: maybe spec-hash-append uses a large nested structure? Actually 'hash' class just does json.loads. array:hash same. Both similar. That's fine for diversity but let me make one use a big list instead? Actually 'hash' class with a list value would just parse the list. Let's keep dicts of different sizes.

Alternatively, replace one with a case where the spec class is 'array:file' (unknown class in the else branch -> requires_resolution with index 0). That's a different path. Let me do:

4. spec-arrayfile-resolve: input_spec says 'reads' is 'array:file' (unknown in the if-chain), value is a long string -> requires_resolution appended with (name, value, 'file', 0). This uses split_unescaped on the long string. Use moderate length.

Hmm that's similar to name-colon-file-resolve but different index (0 vs -1). Actually good diversity.

Let me restructure:
1. json-list-append: no spec, unknown class, big JSON list -> parsed & appended (list slot)
2. json-dict-set: no spec, unknown class, big JSON dict -> parsed & set (non-list slot)
3. spec-hash-append: spec 'hash', big JSON dict -> json.loads default, set
4. spec-arrayhash-append: spec 'array:hash', big JSON dict -> json.loads default, append
5. json-string-resolve: no spec, unknown class, JSON string -> requires_resolution (non-list, index -1)
6. spec-string-long: spec 'string', long escaped-colon string -> split_unescaped work
7. job-jbor: no spec, unknown class, job-xxx:field -> JBOR
8. name-colon-file-resolve: no spec, name 'reads:file', long string -> requires_resolution with class 'file', index -1

That's 8. Good.

Now sizes:
- _BIG_LIST: 150k ints (ok)
- _BIG_DICT_HOOK: 5k keys for case 2
- _BIG_DICT_20K: 20k keys for cases 3,4
- _LONG_PLAIN_JSON: 300k chars for case 5
- _LONG_STR: 10k escaped colons for cases 6,8

Wait, case 6 spec-string-long: input_class 'string' -> split_unescaped then assign input_value. 10k escaped colons.
Case 8: no spec, name 'reads:file' -> input_class='file', then split_unescaped on value (10k escaped colons), then not job -> requires_resolution. Same split work.

Hmm both use 10k. Let me use different lengths for diversity: case 6 uses 15k, case 8 uses 8k.

Actually let me just be safe and use 8k for both, maybe 5k. split_unescaped on 100k took 2.3s -> 10k ~0.23s. 15k ~0.35s. Fine.

Let me finalize.

Also need to make sure case 2's dict isn't too slow. 5k with hook. Let me estimate from 50k=2.72s -> 5k ~0.27s. Good.

Case 3,4: 20k default dict. json.loads 50k default maybe 0.1s? Should be fine. Let me use 30k to be substantial. Hmm, risk. Keep 20k.

Let me write it.