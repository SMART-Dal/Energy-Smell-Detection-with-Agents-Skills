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
