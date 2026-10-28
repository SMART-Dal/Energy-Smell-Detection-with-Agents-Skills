import json
import random

from dxpy.dx_extract_utils import filter_to_payload
from dxpy.dx_extract_utils.filter_to_payload import final_payload

# ---------------------------------------------------------------------------
# The function reads "return_columns_<type>.json" from the module global
# extract_utils_basepath.  Build those files under WORKDIR and point the
# repository's own module at them (setting data, not replacing code).
# ---------------------------------------------------------------------------
_BASEPATH = WORKDIR / "extract_utils_data"
_BASEPATH.mkdir(parents=True, exist_ok=True)
filter_to_payload.extract_utils_basepath = str(_BASEPATH)

_BASE_NAMES = [
    "allele_id", "locus_id", "sample_id", "chrom", "pos", "ref", "alt",
    "gnomad_alt_freq", "gnomad_af", "worst_effect", "consequence",
    "gene_id", "gene_name", "transcript_id", "hgvsc", "hgvsp",
    "clinvar", "dbsnp", "cadd_score", "polyphen", "sift", "phylop",
    "gerp", "af", "ac", "an", "dp", "gq", "qual", "filter_status",
    "variant_id", "variant_type", "functional_class", "impact",
    "transcript_biotype", "canonical", "exon_number", "intron_number",
]


def _make_fields(n, seed, include_locus, include_sample):
    """Build a realistic list of single-key return-column dicts."""
    rng = random.Random(seed)
    names = []
    if include_locus:
        names.append("locus_id")
    if include_sample:
        names.append("sample_id")
    base = [x for x in _BASE_NAMES if x not in ("locus_id", "sample_id")]
    rng.shuffle(base)
    names.extend(base)
    k = 0
    while len(names) < n:
        names.append("field_%d" % k)
        k += 1
    return [{name: name} for name in names[:n]]


_FIELD_SETS = {
    "allele": _make_fields(4000, 0, True, True),
    "annotation": _make_fields(5000, 1, False, False),
    "genotype": _make_fields(3500, 2, False, True),
    "genotype_only": _make_fields(3000, 3, True, False),
}

for _ftype, _fields in _FIELD_SETS.items():
    (_BASEPATH / ("return_columns_%s.json" % _ftype)).write_text(json.dumps(_fields))


def checks():
    return [
        # plain, minimal input
        ("empty-dict", lambda: ({}, "assay", "assay-1", "project-xxx", "38", "allele")),
        # keys whose value is None are skipped by generate_assay_filter
        ("none-values", lambda: ({"variant_id": None, "gene": None}, "assay",
                                 "assay-1", "project-xxx", "38", "annotation")),
        # odd type: generate_assay_filter calls .keys() on it -> raises
        ("none-input", lambda: (None, "assay", "assay-1", "project-xxx", "38", "genotype")),
    ]


def cases():
    return [
        ("allele-ordered",
         lambda: ({}, "assay", "assay-1", "project-xxx", "38", "allele")),
        ("allele-unordered",
         lambda: call({}, "assay", "assay-1", "project-xxx", "38", "allele", order=False)),

        ("annotation-ordered",
         lambda: ({}, "assay", "assay-1", "project-xxx", "38", "annotation")),
        ("annotation-unordered",
         lambda: call({}, "assay", "assay-1", "project-xxx", "38", "annotation", order=False)),

        ("genotype-ordered",
         lambda: ({}, "assay", "assay-1", "project-xxx", "38", "genotype")),
        ("genotype-unordered",
         lambda: call({}, "assay", "assay-1", "project-xxx", "38", "genotype", order=False)),

        ("genotype_only-ordered",
         lambda: ({}, "assay", "assay-1", "project-xxx", "38", "genotype_only")),
        ("genotype_only-unordered",
         lambda: call({}, "assay", "assay-1", "project-xxx", "38", "genotype_only", order=False)),
    ]
