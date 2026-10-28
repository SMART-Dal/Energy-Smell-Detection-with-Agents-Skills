Let me analyze the function.

`infer_genotype_type(samples, loci, result_entries, type_to_infer)`:
- builds loci_dict from loci and result_entries
- for each locus, for each sample not in loci_dict[locus]["samples"], append inferred entry
- returns result_entries + inferred_entries

Key: `_produce_loci_dict` iterates over results_entries and does `loci_dict[entry["locus_id"]]["samples"].add(entry["sample_id"])`. So every entry's locus_id must be in loci_dict, else KeyError. So result_entries must reference loci present in loci.

Also the function returns `result_entries + inferred_entries` — new list, doesn't modify result_entries. But it does modify... no, inferred_entries is a new list. result_entries unchanged, loci unchanged. Actually `_produce_loci_dict` builds a new dict. So no mutation. Good, no need for copies.

Output size: result_entries + inferred. Inferred count = sum over loci of (samples not present). Keep under 100k values. Each entry is a dict with ~7 keys. "keep what it returns under about 100 000 values" — values probably means elements. Let's keep total entries modest, like tens of thousands.

Let's design cases with different shapes:
1. Many loci, few samples, sparse results (lots of inference) — type "ref".
2. Few loci, many samples, sparse.
3. Dense results (few inferred).
4. type_to_infer = "no-call".
5. Duplicates in results (same sample/locus repeated).
6. Loci with no results at all.
7. Large mixed.
8. etc.

Also note `samples` may contain duplicates? If samples has duplicates, inference would append duplicate entries. Realistic: samples unique.

Let's write helper to generate loci and result entries.

locus_id format: "1_1076145_A_T" — chromosome_startingposition_ref_alt.

Let me build:

```python
import random
from dxpy.dx_extract_utils.germline_utils import infer_genotype_type

def _make_loci(n, seed):
    rng = random.Random(seed)
    loci = []
    for i in range(n):
        chrom = str(rng.randint(1, 22))
        pos = 1000000 + i * 137 + rng.randint(0, 100)
        ref = rng.choice("ACGT")
        alt = rng.choice("ACGT")
        while alt == ref:
            alt = rng.choice("ACGT")
        loci.append({
            "locus_id": f"{chrom}_{pos}_{ref}_{alt}",
            "chromosome": chrom,
            "starting_position": pos,
            "ref": ref,
        })
    return loci
```

Need unique locus_ids. Use index i to guarantee uniqueness: pos = 1000000 + i*1000 + rng.randint(0,999) — unique since i differs by 1000. Good.

Samples: f"SAMPLE_{j}".

Result entries: choose subset of (locus, sample) pairs. Entry dict:
```
{
 "sample_id": sample,
 "allele_id": f"{chrom}_{pos}_{ref}_{alt2}",
 "locus_id": locus_id,
 "chromosome": chrom,
 "starting_position": pos,
 "ref": ref,
 "alt": alt2,
 "genotype_type": "het-alt",
}
```

We need entry fields consistent with locus.

Let me write a builder:

```python
def _make_data(n_loci, n_samples, density, seed, dup=1):
    rng = random.Random(seed)
    loci = _make_loci(n_loci, seed)
    samples = [f"SAMPLE_{j}" for j in range(n_samples)]
    entries = []
    for locus in loci:
        for s in samples:
            if rng.random() < density:
                for _ in range(dup if ... ):
                    ...
    return samples, loci, entries
```

Hmm, duplicates: dup factor for some cases.

Output size: inferred = n_loci * n_samples * (1 - density) roughly. Let's keep n_loci*n_samples <= ~40000 so output entries <= 40000. That's fine. Actually each entry is a dict of 7 keys — "under about 100 000 values" — 40k dicts is fine I think. Let's keep total entries (results + inferred) under ~50k.

Timing: one call ~1ms-200ms. The loops: for each locus, for each sample: membership check in set. n_loci*n_samples iterations. 40k iterations is fast (< 10ms). To get more work, need bigger. Let's aim for a few hundred thousand iterations for the big cases. But output size constraint... output entries ≤ 100k. Hmm.

Actually the constraint "keep what it returns under about 100 000 values" — 100k entries. Each entry has 7 values. Maybe values means entries. Let's be safe and keep total returned entries ≤ ~50,000.

With inferred count = n_loci*n_samples*(1-density), and result entries = n_loci*n_samples*density. Total = n_loci*n_samples (plus dup extras). So n_loci*n_samples ≤ 50,000.

That gives maybe 50k iterations of the inner loop — quite fast, maybe 20-30ms including dict creation. Fine, within 1ms-200ms range. Good.

Hmm, but we need 8 diverse cases. Let's think about what varies:
- density (hit ratio): 0.0 (all inferred), 0.5, 0.9, 1.0
- type_to_infer: "ref" vs "no-call"
- sizes: large loci small samples, small loci large samples
- duplicates in result entries
- loci with no matching entries

Also note: the `samples` list contains all samples. In repository, `samples = list(selected_samples.intersection(samples))` — samples is a list of sample ids.

Let's design 8:

1. "sparse-many-loci": n_loci=4000, n_samples=10, density=0.1, type "ref". total pairs 40000, inferred ~36000.
2. "sparse-many-samples": n_loci=50, n_samples=800, density=0.1, type "no-call". pairs 40000.
3. "dense": n_loci=500, n_samples=100, density=0.95, type "ref". pairs 50000, inferred 2500.
4. "no-results": n_loci=2000, n_samples=25, density=0.0, type "no-call". pairs 50000, all inferred.
5. "all-covered": n_loci=1000, n_samples=50, density=1.0, type "ref". pairs 50000, inferred 0.
6. "duplicates": n_loci=200, n_samples=50, density=0.5, dup=3 → result entries = 200*50*0.5*3 = 15000. inferred = 200*50*0.5=5000. total 20000.
7. "medium-mixed": n_loci=1000, n_samples=40, density=0.3, type "no-call". pairs 40000.
8. "big-loci": n_loci=8000, n_samples=5, density=0.2, type "ref". pairs 40000.

Wait, need to check that result entries' locus_id must be in loci_dict. Yes we build from loci.

Also samples in result_entries must be in samples? Not required, but realistic. The `samples` param is used to iterate. If a result entry has a sample not in samples, it's just in the set. Fine, but let's keep consistent.

Now, output comparison: function returns result_entries + inferred_entries. result_entries is the same list object passed in (returned first). The comparison compares outputs of original and modified. Fine.

One concern: the function returns `result_entries + inferred_entries` — a new list. But does it mutate result_entries? No. loci? No. So thunk can return the same objects each call. Wait — but "Its arguments are rendered before and after each call to see whether it changed them". Since it doesn't change them, fine. But rendering large args each call... 50k dicts rendered. That's the harness's problem, keep under 1M values. 50k dicts * 7 = 350k values. Under 1M. OK.

Actually result_entries up to 50k dicts — rendering might be slow but fine.

Hmm, but total: loci (up to 8000 dicts * 4 keys = 32k) + samples + result entries. Fine.

Let's reduce risk: keep n_loci*n_samples around 40k.

Now generation time: building 50k dicts, fast.

Let me write the code.

```python
import random
from dxpy.dx_extract_utils.germline_utils import infer_genotype_type


def _make_loci(n, rng):
    loci = []
    for i in range(n):
        chrom = str(rng.randint(1, 22))
        pos = 1_000_000 + i * 1000 + rng.randint(0, 999)
        ref = rng.choice("ACGT")
        alt = rng.choice("ACGT")
        while alt == ref:
            alt = rng.choice("ACGT")
        loci.append({
            "locus_id": f"{chrom}_{pos}_{ref}_{alt}",
            "chromosome": chrom,
            "starting_position": pos,
            "ref": ref,
        })
    return loci


def _make_entry(rng, locus, sample):
    ref = locus["ref"]
    alt = rng.choice("ACGT")
    while alt == ref:
        alt = rng.choice("ACGT")
    return {
        "sample_id": sample,
        "allele_id": f"{locus['chromosome']}_{locus['starting_position']}_{ref}_{alt}",
        "locus_id": locus["locus_id"],
        "chromosome": locus["chromosome"],
        "starting_position": locus["starting_position"],
        "ref": ref,
        "alt": alt,
        "genotype_type": rng.choice(["het-alt", "hom-alt", "het-ref", "hom-ref"]),
    }


def _make_data(n_loci, n_samples, density, seed, dup=1):
    rng = random.Random(seed)
    loci = _make_loci(n_loci, rng)
    samples = [f"SAMPLE_{j}" for j in range(n_samples)]
    entries = []
    for locus in loci:
        for s in samples:
            if rng.random() < density:
                for _ in range(dup):
                    entries.append(_make_entry(rng, locus, s))
    return samples, loci, entries
```

Wait, for density=1.0 with dup=1, all pairs covered. Good.

But careful: with dup, the same sample/locus appears multiple times in result entries. The set dedups. Fine.

Now cases:

```python
def cases():
    s1, l1, e1 = _make_data(4000, 10, 0.1, 0)
    s2, l2, e2 = _make_data(50, 800, 0.1, 1)
    s3, l3, e3 = _make_data(500, 100, 0.95, 2)
    s4, l4, e4 = _make_data(2000, 25, 0.0, 3)
    s5, l5, e5 = _make_data(1000, 50, 1.0, 4)
    s6, l6, e6 = _make_data(200, 50, 0.5, 5, dup=3)
    s7, l7, e7 = _make_data(1000, 40, 0.3, 6)
    s8, l8, e8 = _make_data(8000, 5, 0.2, 7)
    return [
        ("sparse-many-loci", lambda: (s1, l1, e1, "ref")),
        ...
    ]
```

Wait, for case 2: n_loci=50, n_samples=800, density 0.1, inferred = 50*800*0.9 = 36000. results ~4000. total 40000. OK.

Case 5 (all covered): inferred 0, results 50000. Output 50000 entries.

Case 4 (no results): density 0, all inferred = 50000. results 0. Output 50000.

Hmm 50000 entries each with 7 keys = 350k values. OK under 1M.

Case 8: 8000 loci, 5 samples = 40000 pairs, density 0.2 → results 8000, inferred 32000. Total 40000.

Good.

Now checks: small edge inputs.
- empty samples, empty loci, empty results → returns [] + [] = [].
- single locus, single sample, no results → one inferred entry.
- single locus with result covering sample → no inferred.
- odd type? maybe samples containing duplicates? Or type_to_infer None? Let's do a couple.

checks() returns 2-3.

```python
def checks():
    return [
        ("all-empty", lambda: ([], [], [], "ref")),
        ("single-inferred", lambda: (["S1"], [{"locus_id": "1_100_A_T", "chromosome": "1", "starting_position": 100, "ref": "A"}], [], "no-call")),
        ("single-covered", lambda: (["S1"], [{"locus_id": "1_100_A_T", "chromosome": "1", "starting_position": 100, "ref": "A"}], [{"sample_id": "S1", "allele_id": "1_100_A_AT", "locus_id": "1_100_A_T", "chromosome": "1", "starting_position": 100, "ref": "A", "alt": "AT", "genotype_type": "het-alt"}], "ref")),
    ]
```

These are all fine, no raises.

Now, is the import path correct? `from dxpy.dx_extract_utils.germline_utils import infer_genotype_type`. The task says import exactly as shown. OK.

Let me double check `_produce_loci_dict` handles duplicate locus_ids in loci: later overwrites. Our loci unique.

One more thought: the function's work is dominated by dict creation for inferred entries. The "modified version" presumably does something equivalent. Fine.

Data sizes in memory: e.g. case 5: 50000 entry dicts each ~8 keys. That's maybe 50000 * ~500 bytes = 25MB. Plus loci. OK under 100MB.

Actually wait, case 5 has density 1.0 so entries = 1000*50 = 50000 result entries, plus inferred 0. Each entry dict ~8 keys. ~25-30 MB. Fine.

Case 4: 2000 loci, 25 samples, density 0 → 0 result entries, inferred 50000. The inferred entries are created inside the function each call, not stored. Fine.

Total module-level memory across all cases: results sum ~ e1 4000 + e2 4000 + e3 47500 + e4 0 + e5 50000 + e6 15000 + e7 12000 + e8 8000 ≈ 140k dicts. ~70MB. Hmm, that might be close to 100MB. Let's reduce a bit.

Let me reduce: case 3 density 0.95 with 500*100=50000 → 47500 entries. Case 5 50000. These two are heavy. Let's reduce case 3 to 400 loci * 100 = 40000, density 0.95 → 38000. Case 5 to 800 loci * 50 = 40000.

Actually total memory ~140k dicts of 8 keys. A dict with 8 keys in CPython ~ 360 bytes plus strings. Strings are shared? allele_id strings are unique per entry. So maybe ~600 bytes each → 84MB. Risky.

Let's reduce overall. Keep total result entries under ~80k.

Revised:
1. 4000 loci, 10 samples, 0.1 → 4000 entries
2. 50 loci, 800 samples, 0.1 → 4000 entries
3. 500 loci, 80 samples, 0.9 → 36000 entries. pairs=40000.
4. 2000 loci, 20 samples, 0.0 → 0 entries. pairs=40000.
5. 800 loci, 50 samples, 1.0 → 40000 entries. pairs=40000.
6. 200 loci, 50 samples, 0.5, dup=3 → 15000 entries.
7. 1000 loci, 40 samples, 0.3 → 12000 entries.
8. 8000 loci, 5 samples, 0.2 → 8000 entries.

Total entries ≈ 4000+4000+36000+0+40000+15000+12000+8000 = 119000. Still ~70MB. Hmm.

Maybe reduce case 5: 500 loci * 50 = 25000 entries all covered, density 1.0. pairs 25000.
Case 3: 400 loci * 80 = 32000 pairs, density 0.9 → 28800 entries.

Total ≈ 4000+4000+28800+0+25000+15000+12000+8000 = 96800. ~55MB. Acceptable but let's trim more.

Actually let's reconsider: is memory really a concern? "Keep the data in memory under about 100 MB". 100k dicts is probably around 50-60MB. Let's just be moderate.

Let me settle:
1. 3000 loci, 10 samples, 0.1 → 3000 entries, pairs 30000
2. 50 loci, 600 samples, 0.1 → 3000 entries, pairs 30000
3. 400 loci, 80 samples, 0.9 → 28800 entries, pairs 32000
4. 1500 loci, 20 samples, 0.0 → 0 entries, pairs 30000
5. 600 loci, 50 samples, 1.0 → 30000 entries, pairs 30000
6. 200 loci, 50 samples, 0.5, dup=3 → 15000 entries
7. 1000 loci, 30 samples, 0.3 → 9000 entries, pairs 30000
8. 6000 loci, 5 samples, 0.2 → 6000 entries, pairs 30000

Total entries ~ 94800. Hmm still. Let's reduce case 5 to 400*50=20000, case 3 to 300*80=24000 pairs density 0.9 → 21600.

Total: 3000+3000+21600+0+20000+15000+9000+6000 = 77600. ~45MB. Good.

Actually the inferred entries are created fresh each call and discarded (well, returned and compared). During a call, output list holds result_entries + inferred. For case 4, 30000 inferred entries created. Fine.

OK. Let's also think: does the harness keep results from all cases simultaneously? Probably per-case. Fine.

Now let me finalize. Also need distinct labels.

Let me write final code.

One more check: `_make_entry` uses rng.choice on "ACGT" for alt; allele_id uses alt. Fine.

Also the genotype_type in result entries: use a few values.

Edge: in case 5 density=1.0, rng.random() < 1.0 always true (random() in [0,1)). Good.

In case 4 density=0.0, random() < 0.0 never. Good.

Let me write it.

Actually, one concern about checks: "single-covered" — result entry sample S1 is in samples; loci_dict has S1 in samples set, so no inferred. Output = result_entries. Good, no raise.

Let me also ensure loci dict in checks has required keys for _produce_loci_dict: locus_id, chromosome, starting_position, ref. Yes.

Final code.