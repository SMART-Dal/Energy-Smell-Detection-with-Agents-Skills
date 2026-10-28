We need to write cases for harmonize_germline_results(results, fields_list). Simple function. Need 8 measured inputs, realistic scale. Results are list of dicts from a query, fields_list is a list of field names.

Need to make it do substantial work: e.g. results with many entries, fields_list with many fields, varying hit ratios.

Let's create inputs: results list of dicts with random subset of fields present, fields_list a list of field names (some present, some missing). Different sizes and distributions.

One call should take ~1ms-200ms. The function is O(len(results)*len(fields_list)). To reach ~10-50ms, we need e.g. 5000 results * 50 fields = 250k operations, maybe a few ms. Let's aim bigger: 20000 results * 100 fields = 2M dict ops ~ maybe 100ms. Let's be careful. Python dict operations are fast, ~50-100ns each. 2M -> ~0.2s maybe. Let's target moderate: 10000 results * 50 fields = 500k -> ~30ms. Good.

Let's design 8 cases:

1. typical: 5000 results, 20 fields, most fields present (hit ratio 0.9)
2. many fields: 2000 results, 100 fields, hit ratio 0.5
3. many results: 30000 results, 10 fields, hit ratio 0.8
4. sparse: 10000 results, 50 fields, hit ratio 0.1 (mostly missing)
5. dense: 10000 results, 50 fields, hit ratio 1.0 (all present)
6. empty results: ... but that's a check maybe. Cases must do substantial work, so avoid trivial.
7. varying field counts: 8000 results, 30 fields, hit ratio 0.6
8. duplicates? Fields list with duplicates? The function would overwrite; still same work. Maybe fields_list containing some fields not in results at all.
9. Large field names, etc.

Realistic: fields_list from genotype/allele table query. Fields like "variant_id", "genotype", etc. Use realistic names.

Let's build module-level data.

Need to ensure the function doesn't modify inputs in a way that persists. It doesn't modify results or fields_list (it creates new dicts). So can reuse same data across thunk calls. But wait: it returns new list of dicts; no mutation. So thunk can return the same data each time. Good.

But careful: the arguments are rendered before and after each call to see whether they changed. Since no mutation, fine.

Let's write helper to generate results.

We should use random.Random(0) fixed seed.

Fields names: create a pool of field names, e.g. ["variant_id", "locus_id", "genotype", "ref", "alt", "af", ...]. Let's make a pool of 200 names like f"field_{i}" plus realistic ones. But realistic names: use names like "variant_id", "genotype", "sample_id", "allele", "locus", "chromosome", "position", "ref", "alt", "filter", "qual", "info", "format", "genotype_quality", "read_depth", "allele_frequency", "clinical_significance", "gene", "transcript", "consequence", "hgvsc", "hgvsp", "rsid", "cosmic_id", "dbsnp", "gnomad_af", "exac_af", "1000g_af", etc. We can just generate names.

Let's create a pool of 300 field names.

Helper:

def _make_results(n, fields_pool, hit_ratio, seed, n_present):
    rng = random.Random(seed)
    results = []
    for i in range(n):
        d = {}
        for f in fields_pool:
            if rng.random() < hit_ratio:
                d[f] = rng.randint(0, 10**6)  # value
        results.append(d)
    return results

But if hit_ratio is 0.9 and fields_pool 50, each dict has ~45 keys. Fine.

Actually we want fields_list to be a list of fields, and results have some subset. The function iterates over fields_list for each result. So work = n * len(fields_list).

Let's define cases:

case 1: ("typical", 5000 results, fields_list 20 fields, hit 0.9)
case 2: ("wide-fields", 2000 results, fields_list 100 fields, hit 0.5)
case 3: ("many-results", 30000 results, fields_list 10 fields, hit 0.8)
case 4: ("sparse", 10000 results, fields_list 50 fields, hit 0.1)
case 5: ("dense", 10000 results, fields_list 50 fields, hit 1.0)
case 6: ("mixed", 8000 results, fields_list 40 fields, hit 0.6)
case 7: ("extra-fields", 5000 results, fields_list 30 fields, results have extra fields not in fields_list, hit 0.7)
case 8: ("long-strings", 4000 results, fields_list 25 fields, hit 0.9, values are long strings) - maybe values being strings vs ints doesn't matter much for dict copy. But could make it different.

Actually the function just copies values by reference. Value type doesn't matter. So make diverse sizes.

Let's check timing: 30000 * 10 = 300k -> ~10ms. 2000*100 = 200k. 10000*50 = 500k -> ~20ms. 5000*20=100k. Total maybe 8 cases ~ maybe 100ms combined per run. That's fine.

But we want each case to be substantial, roughly 1ms-200ms. 100k dict ops maybe ~5-10ms. Good.

Maybe bump up some: case 3: 50000 results * 15 fields = 750k. case 5: 15000 * 60 = 900k. Let's be moderate to avoid >1s.

Let's estimate: Python loop with dict lookup and assignment: maybe 100ns per iteration? Actually a simple loop iteration with a couple dict ops might be ~150-250ns. 900k * 200ns = 180ms. That's near upper but ok. Let's keep max around 1M ops.

Case list final:

1. typical: 5000 results, 20 fields, hit 0.9 -> 100k ops
2. wide: 3000 results, 80 fields, hit 0.5 -> 240k
3. many results: 40000 results, 12 fields, hit 0.8 -> 480k
4. sparse: 15000 results, 50 fields, hit 0.1 -> 750k (mostly None assignment)
5. dense: 12000 results, 60 fields, hit 1.0 -> 720k
6. mixed: 10000 results, 35 fields, hit 0.6 -> 350k
7. extra fields: 8000 results, 40 fields, hit 0.7 -> 320k
8. large results: 25000 results, 25 fields, hit 0.5 -> 625k

Total ~3.5M ops per full run of 8 cases. That might be ~0.5-1s per run? But each case is run many times in a row... The measurement runs each input many times. Hmm, "each input many times in a row". So total time could be large. But the harness decides. We just need one call ~1ms-200ms. Our biggest is maybe 150ms. That's acceptable but maybe near upper. Let's reduce a bit to be safe, target 20-100ms.

Let me estimate more carefully: a Python function call overhead plus loop. For 750k iterations, each iteration does `if field in result` (hash lookup) and assignment. That's maybe 100-150ns each? Actually dict `in` is ~30-50ns, assignment ~50ns, loop overhead ~30ns. So ~150ns * 750k = 112ms. Okay.

Let's scale down slightly: max ~500k ops.

Revised:

1. typical: 5000 results, 20 fields, hit 0.9 -> 100k
2. wide: 2000 results, 80 fields, hit 0.5 -> 160k
3. many results: 25000 results, 12 fields, hit 0.8 -> 300k
4. sparse: 10000 results, 50 fields, hit 0.1 -> 500k
5. dense: 8000 results, 60 fields, hit 1.0 -> 480k
6. mixed: 8000 results, 35 fields, hit 0.6 -> 280k
7. extra fields: 6000 results, 40 fields, hit 0.7 -> 240k
8. large: 15000 results, 25 fields, hit 0.5 -> 375k

Total ~2.4M ops per full run. Fine.

Now checks(): 2-3 small edge inputs. E.g. empty results, empty fields_list, result with None values or odd types.

checks:
- ("empty-results", lambda: ([], ["a", "b"]))
- ("empty-fields", lambda: ([{"a": 1}], []))
- ("none-values", lambda: ([{"a": None}], ["a", "b"]))

These are small, never measured.

Now code structure:

import random

_FIELD_POOL = [...]
def _make_results(n, fields, hit_ratio, seed):
    rng = random.Random(seed)
    results = []
    for _ in range(n):
        d = {}
        for f in fields:
            if rng.random() < hit_ratio:
                d[f] = rng.randint(0, 10**9)
        results.append(d)
    return results

But fields_list may include fields not in results; that's fine.

We need to generate fields_list separately, maybe as a slice of the pool. Since function iterates fields_list, we want fields_list length as specified.

Let's define at module level:

_POOL = [f"field_{i}" for i in range(200)] + realistic names... Actually just use a pool of 300 names.

Let's make realistic names first:

_REALISTIC = [
    "variant_id", "locus_id", "genotype", "sample_id", "allele", "chromosome",
    "position", "ref", "alt", "filter", "qual", "info", "format",
    "genotype_quality", "read_depth", "allele_frequency", "clinical_significance",
    "gene", "transcript", "consequence", "hgvsc", "hgvsp", "rsid",
    "cosmic_id", "dbsnp", "gnomad_af", "exac_af", "thousand_genomes_af",
    "splice_ai", "cadd_score", "revel_score", "polyphen", "sift",
    "mutation_taster", "fathmm", "metasvm", "metalr", "provean",
    "gerp", "phastcons", "phylop", "gtex_expression", "tissue",
    "disease", "inheritance", "zygosity", "parent_of_origin", "phase",
    "supporting_reads", "total_reads", "vaf", "depth", "mq", "bq",
    "strand_bias", "left_align", "right_align", "caller", "caller_version",
    "pipeline_version", "assembly", "species", "build", "source",
    "annotation_version", "db_version", "date", "batch", "run_id",
    "lane", "flowcell", "barcode", "library", "center", "project",
    "consent", "phenotype", "sex", "age", "ethnicity", "family_id",
    "proband", "affected", "carrier", "homozygous", "heterozygous",
    "hemizygous", "compound_het", "de_novo", "segregation", "coverage",
    "gc_content", "mapq", "baseq", "clip", "insert_size", "duplicate",
    "proper_pair", "secondary", "supplementary", "chimeric", "split",
    "discordant", "mate", "pair_orientation", "read_group", "platform",
    "instrument", "run_date", "analysis_date", "review_status", "reviewer",
    "comment", "flag", "tag", "label", "category", "group", "subgroup",
    "priority", "severity", "confidence", "score", "rank", "index",
    "version", "revision", "status", "state", "type", "kind", "class",
    "level", "stage", "step", "phase", "mode", "method", "algorithm",
    "model", "parameter", "threshold", "cutoff", "limit", "bound",
    "range", "min", "max", "mean", "median", "std", "var", "sum",
    "count", "total", "average", "percentile", "quantile", "zscore",
    "pvalue", "qvalue", "fdr", "bonferroni", "odds_ratio", "risk_ratio",
    "hazard_ratio", "confidence_interval", "lower_bound", "upper_bound",
    "effect_size", "power", "sample_size", "population", "cohort",
    "case", "control", "exposed", "unexposed", "treated", "untreated",
    "response", "outcome", "event", "time", "duration", "follow_up",
    "survival", "recurrence", "metastasis", "stage_ajcc", "grade",
    "histology", "morphology", "differentiation", "invasion", "lymph_node",
    "margin", "size_cm", "location", "laterality", "multifocal",
    "synchronous", "metachronous", "recurrence_type", "treatment_type",
    "chemotherapy", "radiation", "surgery", "targeted_therapy",
    "immunotherapy", "hormonal_therapy", "clinical_trial", "protocol",
    "dose", "frequency", "route", "duration_days", "start_date",
    "end_date", "adverse_event", "toxicity", "grade_toxicity",
    "response_rate", "progression_free", "overall_survival",
]

That's plenty (~200). We can just use these.

Actually simpler: generate field names programmatically: `[f"f{j}" for j in range(300)]`. But realistic names are nice. Let's use a mix: realistic names plus generated.

Let's just create a pool of 400 names: the realistic list plus f"extra_field_{i}" for i in range(200).

Now define module-level data for each case.

We need to be careful about memory: results list of dicts. For 25000 results with ~10 keys each, that's 250k entries, each dict overhead ~200 bytes -> ~50MB. That's okay but maybe a bit high. Let's keep total under 100MB. 25000 dicts * (dict overhead ~200 bytes + keys) ~ maybe 30-50MB. Fine.

Actually we have 8 cases simultaneously in memory. Sum of results:
- 5000 + 2000 + 25000 + 10000 + 8000 + 8000 + 6000 + 15000 = 79000 results.
Each with average maybe 30 keys -> 2.4M key-value pairs. Each dict entry ~50-100 bytes -> ~200MB. Hmm, that might exceed 100MB.

We need to be careful. 2.4M dict entries could be ~150-250MB. Let's reduce.

Better: reduce number of results and keys, or share data. Since the function doesn't mutate, we could reuse the same results list across cases with different fields_list? But cases should be diverse. We can generate results with fewer keys per dict, or smaller counts.

Let's recalc: dict entry overhead in CPython: a dict with n entries uses ~ 8 bytes per slot in table (plus overhead), and each key/value are references. Keys are strings (interned? not necessarily). The string objects themselves are shared if we reuse the same field name strings from the pool. So each dict has references to the same string objects. So per entry: ~16 bytes table + 8 bytes key ref + 8 bytes value ref = ~32 bytes, plus value int objects (each int ~28 bytes, but small ints cached; large ints unique). If values are unique ints, each int is ~28 bytes. So per entry ~60 bytes. 2.4M entries -> ~144MB. Plus dict overhead per dict (~64 bytes * 79000 = 5MB). So ~150MB. Too high.

We should reduce total entries. Target < 1M entries total across all cases.

Let's reduce sizes:

1. typical: 3000 results, 20 fields, hit 0.9 -> 2700 entries per result? No, 20 fields * 0.9 = 18 keys per result. 3000*18 = 54k entries.
2. wide: 1500 results, 60 fields, hit 0.5 -> 1500*30 = 45k
3. many results: 15000 results, 10 fields, hit 0.8 -> 15000*8 = 120k
4. sparse: 8000 results, 40 fields, hit 0.1 -> 8000*4 = 32k
5. dense: 5000 results, 50 fields, hit 1.0 -> 250k
6. mixed: 6000 results, 25 fields, hit 0.6 -> 90k
7. extra: 5000 results, 30 fields, hit 0.7 -> 105k
8. large: 10000 results, 15 fields, hit 0.5 -> 75k

Total entries ~771k. That's ~50MB. Good.

Now operations per call: n * len(fields_list):
1. 3000*20 = 60k
2. 1500*60 = 90k
3. 15000*10 = 150k
4. 8000*40 = 320k
5. 5000*50 = 250k
6. 6000*25 = 150k
7. 5000*30 = 150k
8. 10000*15 = 150k

Max 320k ops -> ~50ms. Good.

But wait, case 4 sparse has 8000 results * 40 fields = 320k, with mostly None assignments. Fine.

We could increase some to make them more substantial, but this is fine.

Let's also vary value types: some cases with string values, some with None values, etc. But function just copies.

Actually the function checks `if field in result`. If result is a dict with keys. Value type irrelevant.

Let's make case 8 have long string values to make memory larger but ops same. Not necessary.

Let's now write code.

Module-level:

import random

_FIELDS = [ ... ]  # realistic names

def _make_results(n, fields, hit_ratio, seed):
    rng = random.Random(seed)
    results = []
    for _ in range(n):
        d = {}
        for f in fields:
            if rng.random() < hit_ratio:
                d[f] = rng.randint(0, 10**9)
        results.append(d)
    return results

But fields_list for the function is a list of field names. We need to pick a subset of _FIELDS for each case.

Let's define at module level:

_POOL = _FIELDS + [f"extra_{i}" for i in range(200)]

Then for each case, pick fields_list = _POOL[:k] (first k fields). And results generated from a possibly different subset, e.g. _POOL[:k+extra] or random subset.

To make hit/miss ratios meaningful, results should be generated with keys from the same field set as fields_list, plus possibly extra fields not in fields_list.

Let's define helper:

def _build_case(n, k, hit_ratio, seed, extra=0):
    fields_list = _POOL[:k]
    result_fields = _POOL[:k+extra]
    rng = random.Random(seed)
    results = []
    for _ in range(n):
        d = {}
        for f in result_fields:
            if rng.random() < hit_ratio:
                d[f] = rng.randint(0, 10**9)
        results.append(d)
    return results, fields_list

But we need to store them. Let's just create them as module-level variables.

Actually, to keep memory manageable, we can generate on the fly in the thunk? No, thunks run before timing, but they run each time the case is used? "Thunks run before the timing starts" - each thunk is called once to get the arguments, then the function is called many times with those arguments. So thunk is called once per measurement? Actually the harness likely calls the thunk once, then times the function call repeated many times. So building in thunk is fine, but building large data each thunk call could be expensive if thunk is called many times. The instructions say "build large data once, in module-level code, and have the thunk return it". So module-level is safer.

Let's build module-level data.

We can generate all cases at module level.

Let's write:

_POOL = _REALISTIC + [f"extra_field_{i}" for i in range(300)]

def _make_results(n, fields, hit_ratio, seed):
    rng = random.Random(seed)
    return [{f: rng.randint(0, 10**9) for f in fields if rng.random() < hit_ratio} for _ in range(n)]

Wait, dict comprehension with condition: `{f: rng.randint(...) for f in fields if rng.random() < hit_ratio}` - the condition is evaluated per field, and rng.random() is called. That's fine. But order of evaluation: for each f, check condition, then value. Good.

But careful: if hit_ratio is 1.0, rng.random() < 1.0 is always True (random returns [0,1)). Fine.

Now define cases data:

_CASE1 = (_make_results(3000, _POOL[:25], 0.9, 0), _POOL[:20])
_CASE2 = (_make_results(1500, _POOL[:80], 0.5, 1), _POOL[:60])
_CASE3 = (_make_results(15000, _POOL[:12], 0.8, 2), _POOL[:10])
_CASE4 = (_make_results(8000, _POOL[:50], 0.1, 3), _POOL[:40])
_CASE5 = (_make_results(5000, _POOL[:50], 1.0, 4), _POOL[:50])
_CASE6 = (_make_results(6000, _POOL[:30], 0.6, 5), _POOL[:25])
_CASE7 = (_make_results(5000, _POOL[:45], 0.7, 6), _POOL[:30])  # extra fields present
_CASE8 = (_make_results(10000, _POOL[:20], 0.5, 7), _POOL[:15])

Wait, for case 7, results have fields _POOL[:45] but fields_list is _POOL[:30], so extra fields are present but ignored. Good.

For case 1, results have _POOL[:25], fields_list _POOL[:20], so some extra fields.

Let's double-check memory: case 5: 5000 results * 50 keys = 250k entries. case 3: 15000 * ~9.6 = 144k. case 4: 8000 * 4 = 32k. case 6: 6000 * 18 = 108k. case 7: 5000 * 31.5 = 157k. case 8: 10000 * 10 = 100k. case 1: 3000*22.5=67k. case 2: 1500*40=60k. Total ~918k entries. ~55MB. Good.

Now thunks:

def cases():
    return [
        ("typical", lambda: (_CASE1[0], _CASE1[1])),
        ("wide-fields", lambda: (_CASE2[0], _CASE2[1])),
        ("many-results", lambda: (_CASE3[0], _CASE3[1])),
        ("sparse", lambda: (_CASE4[0], _CASE4[1])),
        ("dense", lambda: (_CASE5[0], _CASE5[1])),
        ("mixed", lambda: (_CASE6[0], _CASE6[1])),
        ("extra-fields", lambda: (_CASE7[0], _CASE7[1])),
        ("large", lambda: (_CASE8[0], _CASE8[1])),
    ]

Since function doesn't mutate, returning same list is fine.

But wait: the function returns a new list of new dicts. It doesn't modify results. So reuse is safe.

Checks:

def checks():
    return [
        ("empty-results", lambda: ([], ["a", "b"])),
        ("empty-fields", lambda: ([{"a": 1}, {"b": 2}], [])),
        ("none-values", lambda: ([{"a": None, "b": 1}], ["a", "b", "c"])),
    ]

These are small.

Now, is there any issue with the function reading module globals? No.

The import: `from dxpy.dx_extract_utils.germline_utils import harmonize_germline_results`. We just need to define checks and cases. The harness imports the function.

Let's ensure we don't import anything unnecessary. We import random.

One thing: the function's module imports `from .filter_to_payload import extract_utils_basepath` and `from .input_validation import GENOTYPE_TYPES`. Those should be available in the repo. We don't need to do anything.

Let's write the final code.

Wait, the task says "A thunk takes no arguments and returns a tuple of positional arguments for the function". So lambda: (results, fields_list) is correct.

Now, could there be an issue with the function's output size? Output is list of dicts, same size as results, ~15000 dicts max. Under 100k values? Each dict has len(fields_list) entries. For case 3: 15000 * 10 = 150k values. That's over 100k? "keep what it returns (and anything it writes) under about 100 000 values". Hmm, 150k values might be slightly over. Let's check each case output values = n * len(fields_list):

1: 3000*20 = 60k
2: 1500*60 = 90k
3: 15000*10 = 150k -> over 100k
4: 8000*40 = 320k -> way over
5: 5000*50 = 250k -> over
6: 6000*25 = 150k -> over
7: 5000*30 = 150k -> over
8: 10000*15 = 150k -> over

We need output under 100k values. So reduce n or fields_list length so that n * len(fields_list) <= 100k.

Let's adjust:

1: n=3000, k=20 -> 60k ok
2: n=1500, k=60 -> 90k ok
3: n=8000, k=10 -> 80k ok
4: n=2000, k=40 -> 80k ok
5: n=2000, k=50 -> 100k ok (exactly 100k, maybe slightly over? "under about 100 000" - 100k is borderline. Let's do 1800*50 = 90k)
6: n=3000, k=25 -> 75k ok
7: n=2500, k=30 -> 75k ok
8: n=5000, k=15 -> 75k ok

Now operations per call:
1: 3000*20 = 60k
2: 1500*60 = 90k
3: 8000*10 = 80k
4: 2000*40 = 80k
5: 1800*50 = 90k
6: 3000*25 = 75k
7: 2500*30 = 75k
8: 5000*15 = 75k

All around 60-90k ops. That's maybe 10-20ms per call. Good, within 1ms-200ms.

But wait, the function does more than just n*len(fields_list) operations? It also creates dicts. But roughly.

Memory: entries = n * (k+extra) * hit_ratio.

1: 3000 * 25 * 0.9 = 67.5k
2: 1500 * 80 * 0.5 = 60k
3: 8000 * 12 * 0.8 = 76.8k
4: 2000 * 50 * 0.1 = 10k
5: 1800 * 50 * 1.0 = 90k
6: 3000 * 30 * 0.6 = 54k
7: 2500 * 45 * 0.7 = 78.75k
8: 5000 * 20 * 0.5 = 50k

Total ~487k entries. Very safe.

But are these cases "stressful" enough? The instructions say "Each case should make the function do substantial and different work". 60-90k ops is okay, maybe a bit low. We could increase n and reduce k to keep output under 100k. For example, case 3: n=40000, k=2 -> output 80k, ops 80k. But then results have more entries? Entries = 40000 * (2+2) * 0.8 = 128k entries. Still fine. The function's work is n * len(fields_list). To make it more substantial, we need higher n * k, but output is n*k, so output constraint limits work. Wait, output values = n * len(fields_list) because each harmonized result has exactly len(fields_list) keys. So output size = n * k. Thus work = output size. So we can't have more work without more output. The constraint "keep what it returns under about 100 000 values" means max work is ~100k dict operations. That's the nature of this function. So 60-90k is near the max. Good.

Actually, the output is a list of dicts, each with len(fields_list) keys. So total values = n * len(fields_list). So we are limited to ~100k values. That's fine.

But wait, the function also iterates over results and checks `if field in result`. The number of checks is n * len(fields_list). Same as output. So work is bounded by output size.

Thus our cases are appropriately sized.

Let's finalize the code.

One more consideration: the function might be called with results that are not dicts? No.

Let's write the code cleanly.

```python
import random

_REALISTIC = [
    "variant_id", "locus_id", "genotype", "sample_id", "allele", "chromosome",
    "position", "ref", "alt", "filter", "qual", "info", "format",
    "genotype_quality", "read_depth", "allele_frequency", "clinical_significance",
    "gene", "transcript", "consequence", "hgvsc", "hgvsp", "rsid",
    "cosmic_id", "dbsnp", "gnomad_af", "exac_af", "thousand_genomes_af",
    "splice_ai", "cadd_score", "revel_score", "polyphen", "sift",
    "mutation_taster", "fathmm", "metasvm", "metalr", "provean",
    "gerp", "phastcons", "phylop", "gtex_expression", "tissue",
    "disease", "inheritance", "zygosity", "parent_of_origin", "phase",
    "supporting_reads", "total_reads", "vaf", "depth", "mq", "bq",
    "strand_bias", "left_align", "right_align", "caller", "caller_version",
    "pipeline_version", "assembly", "species", "build", "source",
    "annotation_version", "db_version", "date", "batch", "run_id",
    "lane", "flowcell", "barcode", "library", "center", "project",
    "consent", "phenotype", "sex", "age", "ethnicity", "family_id",
    "proband", "affected", "carrier", "homozygous", "heterozygous",
    "hemizygous", "compound_het", "de_novo", "segregation", "coverage",
    "gc_content", "mapq", "baseq", "clip", "insert_size", "duplicate",
    "proper_pair", "secondary", "supplementary", "chimeric", "split",
    "discordant", "mate", "pair_orientation", "read_group", "platform",
    "instrument", "run_date", "analysis_date", "review_status", "reviewer",
    "comment", "flag", "tag", "label", "category", "group", "subgroup",
    "priority", "severity", "confidence", "score", "rank", "index",
    "version", "revision", "status", "state", "type", "kind", "class",
    "level", "stage", "step", "phase", "mode", "method", "algorithm",
    "model", "parameter", "threshold", "cutoff", "limit", "bound",
    "range", "min", "max", "mean", "median", "std", "var", "sum",
    "count", "total", "average", "percentile", "quantile", "zscore",
    "pvalue", "qvalue", "fdr", "bonferroni", "odds_ratio", "risk_ratio",
    "hazard_ratio", "confidence_interval", "lower_bound", "upper_bound",
    "effect_size", "power", "sample_size", "population", "cohort",
    "case", "control", "exposed", "unexposed", "treated", "untreated",
    "response", "outcome", "event", "time", "duration", "follow_up",
    "survival", "recurrence", "metastasis", "stage_ajcc", "grade",
    "histology", "morphology", "differentiation", "invasion", "lymph_node",
    "margin", "size_cm", "location", "laterality", "multifocal",
    "synchronous", "metachronous", "recurrence_type", "treatment_type",
    "chemotherapy", "radiation", "surgery", "targeted_therapy",
    "immunotherapy", "hormonal_therapy", "clinical_trial", "protocol",
    "dose", "frequency", "route", "duration_days", "start_date",
    "end_date", "adverse_event", "toxicity", "grade_toxicity",
    "response_rate", "progression_free", "overall_survival",
]

_POOL = _REALISTIC + [f"extra_field_{i}" for i in range(300)]

def _make_results(n, fields, hit_ratio, seed):
    rng = random.Random(seed)
    return [
        {f: rng.randint(0, 10**9) for f in fields if rng.random() < hit_ratio}
        for _ in range(n)
    ]

# Module-level data for the 8 measured cases.
_CASE1 = (_make_results(3000, _POOL[:25], 0.9, 0), _POOL[:20])
_CASE2 = (_make_results(1500, _POOL[:80], 0.5, 1), _POOL[:60])
_CASE3 = (_make_results(8000, _POOL[:12], 0.8, 2), _POOL[:10])
_CASE4 = (_make_results(2000, _POOL[:50], 0.1, 3), _POOL[:40])
_CASE5 = (_make_results(1800, _POOL[:50], 1.0, 4), _POOL[:50])
_CASE6 = (_make_results(3000, _POOL[:30], 0.6, 5), _POOL[:25])
_CASE7 = (_make_results(2500, _POOL[:45], 0.7, 6), _POOL[:30])
_CASE8 = (_make_results(5000, _POOL[:20], 0.5, 7), _POOL[:15])

def checks():
    return [
        ("empty-results", lambda: ([], ["a", "b"])),
        ("empty-fields", lambda: ([{"a": 1}, {"b": 2}], [])),
        ("none-values", lambda: ([{"a": None, "b": 1}], ["a", "b", "c"])),
    ]

def cases():
    return [
        ("typical", lambda: (_CASE1[0], _CASE1[1])),
        ("wide-fields", lambda: (_CASE2[0], _CASE2[1])),
        ("many-results", lambda: (_CASE3[0], _CASE3[1])),
        ("sparse", lambda: (_CASE4[0], _CASE4[1])),
        ("dense", lambda: (_CASE5[0], _CASE5[1])),
        ("mixed", lambda: (_CASE6[0], _CASE6[1])),
        ("extra-fields", lambda: (_CASE7[0], _CASE7[1])),
        ("large", lambda: (_CASE8[0], _CASE8[1])),
    ]
```

Wait, the function under test is `harmonize_germline_results`. We don't need to import it in our code; the harness does. But we need to ensure our code doesn't shadow it. Fine.

One issue: `_POOL` length. _REALISTIC has about 200 names? Let's count roughly: it's long, maybe 200. Plus 300 extra = 500. We use up to _POOL[:80], so fine.

But wait, for case 2, fields_list is _POOL[:60], results fields _POOL[:80]. So 60 fields in fields_list, results have up to 80 fields. Good.

For case 5, hit_ratio 1.0, results fields _POOL[:50], fields_list _POOL[:50]. All present.

For case 4, hit_ratio 0.1, results fields _POOL[:50], fields_list _POOL[:40]. Mostly missing.

All good.

Let's double-check output values: 
1: 3000*20 = 60k
2: 1500*60 = 90k
3: 8000*10 = 80k
4: 2000*40 = 80k
5: 1800*50 = 90k
6: 3000*25 = 75k
7: 2500*30 = 75k
8: 5000*15 = 75k

All under 100k.

Input values (results entries): counted earlier, all under 100k? The constraint "keep each input's data under about 1 000 000 values". Input data: list of dicts, each dict has some keys. Total key-value pairs ~500k. Under 1M. Good.

Memory: fine.

Now, the function returns a new list of dicts. The harness compares outputs. Our outputs are deterministic.

One more thing: the function might be called with keyword arguments? No, it takes two positional.

I think this is good.

Let's write the final answer.