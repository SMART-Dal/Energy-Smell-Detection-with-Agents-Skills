The function is simple: list comprehension filtering by key not in restricted_values. Need 8 cases with realistic data from extract_assay query results. Data dicts have keys like sample_id, allele_id, locus_id, chromosome, starting_position, ref, alt, genotype_type.

GENOTYPE_TYPES from input_validation. Let me not import it—actually I could import it but I don't know its content. Better to just use realistic genotype types. Actually the task says use only what's shown. I'll use strings like "ref", "het-alt", "hom-alt", "no-call", "half-ref".

The function is cheap—one dict lookup per entry. To get 1ms+ we need many entries. Let's make lists of ~50k-200k entries.

Note: outputs compared in full, keep under 100k values. So filtered results list should be under 100k. If we filter out few, output is near input size. Inputs under 1M values. Each dict has 8 values, so 100k entries = 800k values. Hmm, "keep each input's data under about 1 000 000 values". So up to ~100k dicts. But output must be under 100k values too. Each output entry is a dict of 8 values → 8 values per entry, so output ~12k entries max if counting each dict value. Hmm, ambiguous. Let's be conservative: use sizes around 20k-60k entries.

Let's make cases with varying sizes and restricted_values.

Build generator function for results.

Cases:
1. typical: 50k entries, key="genotype_type", restricted=["het-alt"], many genotype types.
2. large restricted list: 30k entries, restricted with 100 values.
3. small result: 2000 entries, restricted few.
4. key="chromosome", restricted many chromosomes.
5. key="sample_id" with many distinct samples.
6. mostly filtered out (restricted contains most values).
7. no matches (restricted empty) — heavy output.
8. duplicates and odd values.

Keep thunks cheap: data built at module level.

Note the function doesn't modify inputs, so returning same list is fine.

Let me write it.

Realistic fields: sample_id like "SAMPLE_2", allele_id "1_1076145_A_AT", locus_id "1_1076145_A_T", chromosome "1", starting_position int, ref, alt, genotype_type.

Let me build a generator.

```python
import random

_CHROMS = [str(i) for i in range(1, 23)] + ["X", "Y", "MT"]
_BASES = ["A", "C", "G", "T"]
_GENOTYPES = ["ref", "het-alt", "hom-alt", "no-call", "half-ref"]

def _make_results(n, seed, n_samples=100, genotype_pool=_GENOTYPES):
    rng = random.Random(seed)
    out = []
    for i in range(n):
        chrom = rng.choice(_CHROMS)
        pos = rng.randrange(1, 250_000_000)
        ref = rng.choice(_BASES)
        alt = rng.choice(_BASES)
        sample = rng.randrange(n_samples)
        out.append({
            "sample_id": f"SAMPLE_{sample}",
            "allele_id": f"{chrom}_{pos}_{ref}_{alt}",
            "locus_id": f"{chrom}_{pos}_{ref}_{alt[0]}",
            "chromosome": chrom,
            "starting_position": pos,
            "ref": ref,
            "alt": alt,
            "genotype_type": rng.choice(genotype_pool),
        })
    return out
```

Now cases with distinct workloads. Sizes must keep outputs under limits. Let's think: output size in values ~ n * 8. Keep under 100k → n < 12500 if output isn't reduced. Hmm that's restrictive. Let's keep the typical sizes around 10k-15k entries to be safe. Actually the instructions say "under about 100 000 values" — "about" so 8*15000=120k is borderline. Let's use n up to ~12k.

But then one call on original takes how long? 12k iterations of dict lookup — maybe 1ms. Good enough, roughly 1ms. Larger would be better for measurement. Let's push to ~30k-50k entries; output values ~400k. Hmm, risky.

The constraint is "keep what it returns ... under about 100 000 values". A list of 50k dicts is 50k values at top level arguably. The rendering counts values recursively probably. Hard to say. I'll be moderately conservative: use sizes 10k-40k, and for cases with big outputs use restricted_values to reduce output.

Let's design so each case's output is limited:

1. "typical" — 40k entries, key genotype_type, restricted=["het-alt"] → output ~32k entries. 32k*8 = 256k values. Might exceed. Hmm.

Let me just use n ~ 12k for large-output cases and use restriction-heavy for larger.

Alternative: keep sizes around 10k, but then timing ~1ms which is at the lower bound. That's acceptable ("roughly 1 ms to 200 ms").

Actually let me reconsider: input rendering constraint is 1M values, output 100k. With 8 fields per dict, output of n entries = 8n values → n ≤ 12500. Let's cap n at 12000 for cases where output is nearly full.

To get more work, use cases that filter out most entries? That reduces output. But then the work per call is similar (dict lookup). To make the function do substantial work we want large n. With n=100k and restricted removing 99%, output ~1k entries. That's allowed. Work = 100k lookups ~ 10ms.

So use variety: some large-n mostly-filtered, some small-n with big output.

Let me set:
1. typical: n=12000, genotype_type restricted=["het-alt"], pool 5 types → output ~9600 entries (77k values). OK.
2. mostly-filtered: n=100000, key genotype_type, restricted = 4 of 5 types → output ~20000... too much. restricted all 5 types? then output 0. Use restricted = pool minus one rare value; make one type rare. E.g. pool weights. Simpler: restricted = ["ref","het-alt","hom-alt","half-ref"] and pool such that "no-call" rare. Hmm rng.choice uniform. Let me create a pool list with duplicates to weight: ["ref","het-alt","hom-alt","half-ref"]*... 

Simpler: make a case where restricted_values covers all values present → output empty, n=200k. That's max work, tiny output. Good as one case.

Let me define pools:

- pool_a = ["ref", "het-alt", "hom-alt", "no-call", "half-ref"] (uniform)
- pool_b = weighted

Case plan:
1. typical: n=12000, uniform pool, restricted=["het-alt"], key genotype_type. Output ~9600.
2. large-list-mostly-kept: n=8000, restricted=["het-alt"] plus... same. Let's vary: key="chromosome", restricted=["1","2","3"], n=8000, 24 chroms → output ~7000. ~56k values.
3. large-n-all-filtered: n=200000, key genotype_type, restricted = all 5 types → output empty. Work huge ~ maybe 30ms.
4. large-n-mostly-filtered: n=150000, restricted=["ref","hom-alt"] with pool weighted so those dominate... uniform gives 40% filtered, 60% kept = 90k entries output — too much. Need heavy filtering: restricted = ["ref","het-alt","hom-alt","half-ref"] uniform → 80% filtered, 20% kept = 30k entries = 240k values. Too much.

Hmm. To have big n and small output, need restricted to cover nearly all values. With uniform pool of 5 and restricted 4, kept 20%. For n=150k → 30k kept. Too much.

Use a pool where one value is rare: e.g. pool = ["ref"]*40 + ["het-alt"]*40 + ["hom-alt"]*19 + ["no-call"]*1. Then restricted = ["ref","het-alt","hom-alt"] → kept ~1% → n=150k → 1.5k kept. 

But wait—rng.choice over a weighted list is fine.

Let me build a helper that takes pool list.

Actually simpler: generate genotype via rng.random() thresholds in the maker? Let's just allow passing a pool (list with repetition).

Case plan final:

1. ("typical-het-alt", n=12000, key="genotype_type", restricted=["het-alt"], pool uniform) → output ~9600 entries, ~77k values. Work ~12000 lookups.
2. ("chromosome-filter", n=8000, key="chromosome", restricted=["1","2","3","X"], pool uniform, 24 chroms) → output ~6667 entries ~53k values.
3. ("large-all-filtered", n=200000, key="genotype_type", restricted=all 5 types) → output 0. Work big.
4. ("large-mostly-filtered", n=200000, key="genotype_type", restricted=["ref","het-alt","hom-alt"], weighted pool with rare "no-call") → kept ~2000 entries, 16k values.
5. ("sample-id-filter", n=30000, key="sample_id", restricted=[f"SAMPLE_{i}" for i in range(50)], n_samples=200) → kept 75% = 22500 entries, too many. Use restricted 190 of 200 samples → kept 5% = 1500. Hmm but building restricted list of 190 strings fine.
   Let's do n_samples=200, restricted = SAMPLE_0..SAMPLE_189 (190 values), kept 10/200 = 5% → 1500 entries.
6. ("restricted-large-list", n=15000, key="genotype_type", restricted = large list of ~1000 values including some real ones) → kept ~ most. Output 15000 entries = 120k values. Too many. Reduce n to 10000 → 80k values. OK.
   Actually restricted list of 1000 values mostly non-matching: only "het-alt" matches. kept ~80%. n=10000 → 8000 entries, 64k values. Good.
7. ("no-filter-empty-restricted", n=9000, restricted=[]) → output all 9000 = 72k values. Work minimal.
8. ("duplicates-and-odd", n=12000, key="genotype_type", restricted=["ref","ref","het-alt"] with duplicate restricted values, pool uniform) → output ~7200.

Hmm case 3 with 200k entries: input values = 200k*8 = 1.6M > 1M limit! Constraint: input data under 1M values. So n ≤ 125000. Let's use n=100000 for the large cases. 100k*8 = 800k values. OK.

Redo:
3. n=100000, restricted all 5 → output 0. Work 100k lookups.
4. n=100000, weighted pool, restricted 3 types → kept ~1% = 1000.

Also memory: 100k dicts of 8 entries — fine (~100MB? each dict maybe 300 bytes + strings; strings repeated via interning? f-strings create new. ~ maybe 100MB). Hmm "keep the data in memory under about 100 MB". 100k dicts with 8 string fields, each string ~30 chars → ~80 bytes per string * 8 = 640 + dict overhead ~350 = ~1KB per entry → 100MB. Borderline. Let's reduce to 60000 entries for large cases → 480k values, ~60MB. Safer.

3. n=60000, all filtered.
4. n=60000, weighted, kept ~600.

For case 1, 12000 entries ~ 12MB. Fine.

Let's finalize. Also need checks: empty results, single entry, key not present (raises KeyError — allowed).

checks:
- ("empty-results", lambda: ([], "genotype_type", ["ref"])) → returns [].
- ("single-kept", lambda: ([entry], "genotype_type", ["ref"])) where entry genotype "het-alt".
- ("missing-key", lambda: ([entry], "no_such_key", ["x"])) → raises KeyError.

For missing-key, that's an odd input that may raise. Fine.

Now writing thunks: data built at module level, thunk returns (results, key, restricted). Function doesn't mutate, so returning same list each time is fine.

Let me write generator with weighted pool.

```python
def _make_results(n, seed, key_pool=None, n_samples=100):
```

Simpler: a function that takes n, seed, and a genotype chooser.

```python
import random

_CHROMS = [str(i) for i in range(1, 23)] + ["X", "Y", "MT"]
_BASES = ["A", "C", "G", "T"]
_GENOTYPES = ["ref", "het-alt", "hom-alt", "no-call", "half-ref"]

def _make_results(n, seed, genotype_pool=None, n_samples=100):
    rng = random.Random(seed)
    pool = genotype_pool if genotype_pool is not None else _GENOTYPES
    out = []
    for i in range(n):
        chrom = rng.choice(_CHROMS)
        pos = rng.randrange(1, 250_000_000)
        ref = rng.choice(_BASES)
        alt = rng.choice(_BASES)
        out.append({
            "sample_id": f"SAMPLE_{rng.randrange(n_samples)}",
            "allele_id": f"{chrom}_{pos}_{ref}_{alt}",
            "locus_id": f"{chrom}_{pos}_{ref}_{alt}",
            "chromosome": chrom,
            "starting_position": pos,
            "ref": ref,
            "alt": alt,
            "genotype_type": rng.choice(pool),
        })
    return out
```

Weighted pool: ["ref"]*40 + ["het-alt"]*40 + ["hom-alt"]*19 + ["no-call"]*1.

Case 4: restricted=["ref","het-alt","hom-alt"] → kept only "no-call" ~1%. n=60000 → ~600 kept. Good.

Case 3: restricted = all 5 → output 0. n=60000.

Case 6: restricted large list of 1000 values: ["fake_{i}" ...] + ["het-alt"] → kept ~80%.

Case 2: chromosome filter n=8000.

Case 5: sample filter.

Case 7: empty restricted, n=9000.

Case 8: duplicates restricted, n=12000.

That's 8 cases. Let's double check counts of distinct paths: different keys, different restricted sizes, empty, duplicates. Good.

Now, module-level build time: 60000+60000+12000+8000+30000+10000+9000+12000 ≈ 200k entries built. Should be well under 10s.

Wait case 5 uses n=30000 with n_samples=200. Fine.

Let me write final code.

One thing: the function under test imported as `from dxpy.dx_extract_utils.germline_utils import filter_results`. We don't call it in our code, just provide args. Good.

Checks: single entry dict.

Also note: `entry[key] not in restricted_values` — for restricted list large (1000), each lookup is O(1000), making it slower. That's realistic-ish. Fine.

Let's write.