```python
import random


class _Descriptor(object):
    """Data holder standing in for the object returned by DXDataset.get_descriptor().

    The function under test only ever reads ``rec_descriptor.assays``.
    """

    def __init__(self, assays):
        self.assays = assays


_TABLE = ["0/0", "0/1", "1/1", "0|1", "1|0", "./.", ".|.", "0/1", "1/1"]
_OTHER_MODELS = ["somatic_variant", "expression", "unknown"]


def _germline_assay(i, rich, ref_none=False):
    a = {
        "name": "germline_assay_%d" % i,
        "uuid": "germline-%08d" % i,
        "generalized_assay_model": "genetic_variant",
    }
    if rich:
        a["reference_genome"] = None if ref_none else {"name": "GRCh38.92.genome"}
        a["entities"] = {
            "genotype": {"fields": {"type": {"mapping": {"table": list(_TABLE)}}}}
        }
        a["exclude_refdata"] = True
        a["exclude_halfref"] = False
        a["exclude_nocall"] = True
    return a


def _somatic_assay(i, rich):
    a = {
        "name": "somatic_assay_%d" % i,
        "uuid": "somatic-%08d" % i,
        "generalized_assay_model": "somatic_variant",
    }
    if rich:
        a["reference"] = {"name": "GRCh38", "annotation_source_version": "v92"}
    return a


def _build(factory, n_target, n_other, rich_idx, seed, ref_none=False):
    """Interleave target assays (in order) with 'other' assays.

    Only the target at position ``rich_idx`` carries the nested reference /
    entities / reference_genome payload, exactly as the real descriptors do.
    """
    rng = random.Random(seed)
    assays = []
    for i in range(max(n_target, n_other)):
        if i < n_target:
            if factory is _germline_assay:
                assays.append(factory(i, i == rich_idx, ref_none))
            else:
                assays.append(factory(i, i == rich_idx))
        if i < n_other:
            assays.append({
                "name": "other_%d" % i,
                "uuid": "other-%08d" % i,
                "generalized_assay_model": rng.choice(_OTHER_MODELS),
            })
    return assays


_G1 = _Descriptor(_build(_germline_assay, 25000, 5000, 0, 0))
_G2 = _Descriptor(_build(_germline_assay, 20000, 3000, 12000, 1))
_S1 = _Descriptor(_build(_somatic_assay, 20000, 10000, 0, 2))
_S2 = _Descriptor(_build(_somatic_assay, 15000, 5000, 7000, 3))
_G3 = _Descriptor(_build(_germline_assay, 15000, 15000, 0, 4, ref_none=True))
_G4 = _Descriptor(_build(_germline_assay, 30000, 2000, 0, 5))
_S3 = _Descriptor(_build(_somatic_assay, 20000, 3000, 0, 6))
_G5 = _Descriptor(_build(_germline_assay, 15000, 20000, 0, 7))


def checks():
    return [
        # empty assay list -> err_exit("No valid assays in the dataset.")
        ("no-assays", lambda: (False, None, "record-xxxx", "germline", _Descriptor([]))),
        # --list-assays -> prints names then sys.exit(0)
        ("list-assays", lambda: (True, None, "record-xxxx", "germline",
                                 _Descriptor([_germline_assay(0, True)]))),
        # unknown friendly type -> `assay_type` never assigned -> NameError
        ("unknown-friendly-type", lambda: (False, None, "record-xxxx", "expression",
                                           _Descriptor([_germline_assay(0, True)]))),
    ]


def cases():
    return [
        ("germline-default", lambda: (False, None, "record-xxxx", "germline", _G1)),
        ("germline-named-mid", lambda: (False, "germline_assay_12000", "record-xxxx", "germline", _G2)),
        ("somatic-default", lambda: (False, None, "record-xxxx", "somatic", _S1)),
        ("somatic-named-mid", lambda: (False, "somatic_assay_7000", "record-xxxx", "somatic", _S2)),
        ("germline-no-ref-genome", lambda: (False, None, "record-xxxx", "germline", _G3)),
        ("germline-many-targets", lambda: (False, None, "record-xxxx", "germline", _G4)),
        ("somatic-many-targets", lambda: (False, None, "record-xxxx", "somatic", _S3)),
        ("germline-many-others", lambda: (False, None, "record-xxxx", "germline", _G5)),
    ]
```