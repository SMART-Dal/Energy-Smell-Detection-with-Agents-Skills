# Inputs for src/python/dxpy/system_requirements.py::SystemRequirementsDict.override_cluster_spec, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import random

from dxpy.system_requirements import SystemRequirementsDict


def _cluster_spec(n_fields, seed):
    rng = random.Random(seed)
    d = {
        "initialInstanceCount": rng.randint(1, 100),
        "type": rng.choice(["spark", "dnanexus", "generic"]),
        "version": "2.4.0",
        "bootstrapScript": "bootstrap_%d.sh" % rng.randint(0, 999),
    }
    for j in range(n_fields):
        d["p%d" % j] = "v%d_%d" % (rng.randint(0, 10 ** 6), j)
    return d


def _app(names, n_fields, seed, with_cluster_prob=0.9, wildcard=None, filler_fields=0):
    """Build an app-doc 'systemRequirements' entrypoints mapping."""
    rng = random.Random(seed)
    eps = {}
    for i, name in enumerate(names):
        ep = {}
        if rng.random() < with_cluster_prob:
            ep["clusterSpec"] = _cluster_spec(n_fields, seed * 100003 + i)
        if rng.random() < 0.5:
            ep["instanceType"] = "mem%d_ssd1_x%d" % (rng.randint(1, 4), rng.randint(2, 8))
        if filler_fields:
            ep["instanceTypeSelector"] = {
                "f%d" % j: "s%d" % rng.randint(0, 10 ** 6) for j in range(filler_fields)
            }
        eps[name] = ep
    if wildcard is not None:
        eps["*"] = {"clusterSpec": _cluster_spec(wildcard, seed * 7919 + 3)}
    return eps


def _srd(mapping):
    """Build a requested-instance-count SystemRequirementsDict entrypoints mapping."""
    return {k: {"clusterSpec": {"initialInstanceCount": v}} for k, v in mapping.items()}


# ---------------------------------------------------------------------------
# All inputs are built once, at module level; the thunks only hand them back.
# The method deep-copies self.entrypoints and never mutates self or srd, so the
# same instances can safely be reused for every timed call.
# ---------------------------------------------------------------------------

# A: wildcard request over a large app doc
_names_a = ["fn%04d" % i for i in range(500)]
_app_a = SystemRequirementsDict(_app(_names_a, 100, 1))
_srd_a = SystemRequirementsDict(_srd({"*": 5}))

# B: named request covering half the app entrypoints
_names_b = ["fn%04d" % i for i in range(500)]
_app_b = SystemRequirementsDict(_app(_names_b, 100, 2))
_srd_b = SystemRequirementsDict(_srd({n: (i % 7) + 1 for i, n in enumerate(_names_b[:250])}))

# C: mixed named + wildcard request, app doc also has a wildcard
_names_c = ["ep%04d" % i for i in range(400)]
_app_c = SystemRequirementsDict(_app(_names_c, 80, 3, wildcard=80))
_srd_c = SystemRequirementsDict(
    _srd(dict([(n, i % 5 + 1) for i, n in enumerate(_names_c[:200])] + [("*", 9)]))
)

# D: requested names absent from app doc, only the app's "*" has a clusterSpec
_app_d = SystemRequirementsDict({"*": {"clusterSpec": _cluster_spec(1000, 4)}})
_srd_d = SystemRequirementsDict(_srd({"fn%03d" % i: i % 9 + 1 for i in range(80)}))

# E: app doc with thousands of entrypoints, almost none with a clusterSpec
_names_e = ["ep%04d" % i for i in range(2000)]
_app_e = SystemRequirementsDict(_app(_names_e, 0, 5, with_cluster_prob=0.0, filler_fields=50))
_srd_e = SystemRequirementsDict(_srd({"*": 3}))

# F: few entrypoints but each clusterSpec has thousands of fields
_names_f = ["fn%02d" % i for i in range(10)]
_app_f = SystemRequirementsDict(_app(_names_f, 5000, 6))
_srd_f = SystemRequirementsDict(_srd({"*": 7}))

# G: requested names that match nothing and app doc has no "*"
_names_g = ["app%04d" % i for i in range(300)]
_app_g = SystemRequirementsDict(_app(_names_g, 100, 7))
_srd_g = SystemRequirementsDict(_srd({"req%04d" % i: i % 6 + 1 for i in range(300)}))

# H: medium app doc with sparse clusterSpecs, named + wildcard request
_names_h = ["fn%04d" % i for i in range(200)]
_app_h = SystemRequirementsDict(_app(_names_h, 200, 8, with_cluster_prob=0.7, wildcard=200))
_srd_h = SystemRequirementsDict(
    _srd(dict([(n, i % 4 + 1) for i, n in enumerate(_names_h[:100])] + [("*", 11)]))
)


def checks():
    return [
        ("empty",
         lambda: (SystemRequirementsDict({}), SystemRequirementsDict({}))),
        ("single-entrypoint",
         lambda: (SystemRequirementsDict(
             {"main": {"clusterSpec": {"initialInstanceCount": 1, "version": "2.4.0"}}}),
             SystemRequirementsDict(
                 {"main": {"clusterSpec": {"initialInstanceCount": 3}}}))),
        ("app-entry-without-cluster-spec",
         lambda: (SystemRequirementsDict({"main": {"instanceType": "mem1_ssd1_x2"}}),
                  SystemRequirementsDict(
                      {"*": {"clusterSpec": {"initialInstanceCount": 2}}}))),
    ]


def cases():
    return [
        ("wildcard-large-appdoc", lambda: (_app_a, _srd_a)),
        ("named-half-appdoc", lambda: (_app_b, _srd_b)),
        ("mixed-named-wildcard", lambda: (_app_c, _srd_c)),
        ("fallback-to-app-wildcard", lambda: (_app_d, _srd_d)),
        ("many-entrypoints-no-clusterspec", lambda: (_app_e, _srd_e)),
        ("field-heavy-clusterspec", lambda: (_app_f, _srd_f)),
        ("requested-names-all-miss", lambda: (_app_g, _srd_g)),
        ("sparse-clusterspec-mixed", lambda: (_app_h, _srd_h)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['fallback-to-app-wildcard', 'many-entrypoints-no-clusterspec', 'wildcard-large-appdoc', 'field-heavy-clusterspec']
_KEEP_CHECKS = ['empty', 'single-entrypoint', 'app-entry-without-cluster-spec']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
