# Inputs for src/python/dxpy/dx_extract_utils/germline_utils.py::infer_genotype_type, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

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
        loci.append(
            {
                "locus_id": f"{chrom}_{pos}_{ref}_{alt}",
                "chromosome": chrom,
                "starting_position": pos,
                "ref": ref,
            }
        )
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


# ---- module level: build all inputs once ----
_S1, _L1, _E1 = _make_data(3000, 10, 0.1, 0)          # many loci, few samples, sparse
_S2, _L2, _E2 = _make_data(50, 600, 0.1, 1)           # few loci, many samples, sparse
_S3, _L3, _E3 = _make_data(300, 80, 0.9, 2)           # dense coverage
_S4, _L4, _E4 = _make_data(1500, 20, 0.0, 3)          # no results at all -> all inferred
_S5, _L5, _E5 = _make_data(400, 50, 1.0, 4)           # fully covered -> nothing inferred
_S6, _L6, _E6 = _make_data(200, 50, 0.5, 5, dup=3)    # duplicated result rows
_S7, _L7, _E7 = _make_data(1000, 30, 0.3, 6)          # mixed medium
_S8, _L8, _E8 = _make_data(6000, 5, 0.2, 7)           # very many loci, tiny sample set


def checks():
    return [
        ("all-empty", lambda: ([], [], [], "ref")),
        (
            "single-inferred",
            lambda: (
                ["S1"],
                [
                    {
                        "locus_id": "1_100_A_T",
                        "chromosome": "1",
                        "starting_position": 100,
                        "ref": "A",
                    }
                ],
                [],
                "no-call",
            ),
        ),
        (
            "single-covered",
            lambda: (
                ["S1"],
                [
                    {
                        "locus_id": "1_100_A_T",
                        "chromosome": "1",
                        "starting_position": 100,
                        "ref": "A",
                    }
                ],
                [
                    {
                        "sample_id": "S1",
                        "allele_id": "1_100_A_AT",
                        "locus_id": "1_100_A_T",
                        "chromosome": "1",
                        "starting_position": 100,
                        "ref": "A",
                        "alt": "AT",
                        "genotype_type": "het-alt",
                    }
                ],
                "ref",
            ),
        ),
    ]


def cases():
    return [
        ("many-loci-few-samples", lambda: (_S1, _L1, _E1, "ref")),
        ("few-loci-many-samples", lambda: (_S2, _L2, _E2, "no-call")),
        ("dense-coverage", lambda: (_S3, _L3, _E3, "ref")),
        ("no-results", lambda: (_S4, _L4, _E4, "no-call")),
        ("fully-covered", lambda: (_S5, _L5, _E5, "ref")),
        ("duplicated-results", lambda: (_S6, _L6, _E6, "no-call")),
        ("mixed-medium", lambda: (_S7, _L7, _E7, "ref")),
        ("many-loci-tiny-samples", lambda: (_S8, _L8, _E8, "no-call")),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['many-loci-tiny-samples', 'many-loci-few-samples', 'no-results', 'mixed-medium']
_KEEP_CHECKS = ['all-empty', 'single-inferred', 'single-covered']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
