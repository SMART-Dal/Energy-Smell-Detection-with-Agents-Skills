```python
import random

_CHROMS = [str(i) for i in range(1, 23)] + ["X", "Y", "MT"]
_BASES = ["A", "C", "G", "T"]
_GENOTYPES = ["ref", "het-alt", "hom-alt", "no-call", "half-ref"]

# a heavily skewed genotype distribution: "no-call" is rare
_SKEWED_GENOTYPES = ["ref"] * 40 + ["het-alt"] * 40 + ["hom-alt"] * 19 + ["no-call"] * 1


def _make_results(n, seed, genotype_pool=None, n_samples=100):
    rng = random.Random(seed)
    pool = genotype_pool if genotype_pool is not None else _GENOTYPES
    out = []
    for _ in range(n):
        chrom = rng.choice(_CHROMS)
        pos = rng.randrange(1, 250_000_000)
        ref = rng.choice(_BASES)
        alt = rng.choice(_BASES)
        out.append(
            {
                "sample_id": f"SAMPLE_{rng.randrange(n_samples)}",
                "allele_id": f"{chrom}_{pos}_{ref}_{alt}",
                "locus_id": f"{chrom}_{pos}_{ref}_{alt}",
                "chromosome": chrom,
                "starting_position": pos,
                "ref": ref,
                "alt": alt,
                "genotype_type": rng.choice(pool),
            }
        )
    return out


# ---- module level data (built once, never timed) -------------------------

_TYPICAL = _make_results(12_000, 0)
_BY_CHROM = _make_results(8_000, 1)
_ALL_FILTERED = _make_results(60_000, 2)
_MOSTLY_FILTERED = _make_results(60_000, 3, genotype_pool=_SKEWED_GENOTYPES)
_BY_SAMPLE = _make_results(30_000, 4, n_samples=200)
_BIG_RESTRICTED = _make_results(10_000, 5)
_NO_FILTER = _make_results(9_000, 6)
_DUP_RESTRICTED = _make_results(12_000, 7)

# large restricted_values list, mostly values that never occur
_BIG_RESTRICTED_VALUES = [f"fake_{i}" for i in range(1000)] + ["het-alt"]

# 190 of the 200 sample ids are restricted out
_SAMPLE_RESTRICTED = [f"SAMPLE_{i}" for i in range(190)]

_SINGLE_KEPT = [
    {
        "sample_id": "SAMPLE_2",
        "allele_id": "1_1076145_A_AT",
        "locus_id": "1_1076145_A_T",
        "chromosome": "1",
        "starting_position": 1076145,
        "ref": "A",
        "alt": "AT",
        "genotype_type": "het-alt",
    }
]


def checks():
    return [
        ("empty-results", lambda: ([], "genotype_type", ["ref", "het-alt"])),
        ("single-kept", lambda: (_SINGLE_KEPT, "genotype_type", ["ref"])),
        ("missing-key", lambda: (_SINGLE_KEPT, "not_a_field", ["x"])),
    ]


def cases():
    return [
        # 1. the common repository usage: drop het-alt entries
        ("typical-genotype-type", lambda: (_TYPICAL, "genotype_type", ["het-alt"])),
        # 2. filter by chromosome, a handful of chromosomes removed
        ("chromosome-filter", lambda: (_BY_CHROM, "chromosome", ["1", "2", "3", "X"])),
        # 3. very large input, every entry filtered out
        ("large-all-filtered", lambda: (_ALL_FILTERED, "genotype_type", list(_GENOTYPES))),
        # 4. large input, only the rare genotype survives
        ("large-mostly-filtered", lambda: (_MOSTLY_FILTERED, "genotype_type", ["ref", "het-alt", "hom-alt"])),
        # 5. filter by sample id, most samples restricted out
        ("sample-id-filter", lambda: (_BY_SAMPLE, "sample_id", _SAMPLE_RESTRICTED)),
        # 6. big restricted_values list, almost nothing matches
        ("big-restricted-list", lambda: (_BIG_RESTRICTED, "genotype_type", _BIG_RESTRICTED_VALUES)),
        # 7. empty restricted list: everything is kept
        ("empty-restricted", lambda: (_NO_FILTER, "genotype_type", [])),
        # 8. duplicated values inside restricted_values
        ("duplicate-restricted", lambda: (_DUP_RESTRICTED, "genotype_type", ["ref", "ref", "het-alt"])),
    ]
```