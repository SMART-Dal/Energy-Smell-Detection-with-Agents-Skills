You are a performance testing expert. You will write the inputs for an energy measurement of one Python function from a real repository. We run the original function and a modified version of it on your inputs, each input many times in a row, and compare their energy use and their outputs.

# What to write
Python source defining two functions, `checks()` and `cases()`. Each returns a list of `(label, thunk)` pairs with distinct labels. A thunk takes no arguments and returns a tuple of positional arguments for the function, e.g. `lambda: (rows, 3)`. For keyword arguments the thunk returns `call(...)`, e.g. `lambda: call(rows, sep=",")`; `call` is provided, do not import or define it. A method is called as a plain function: the thunk builds the instance and passes it as the first argument (a classmethod gets its class there, a staticmethod nothing; the task says which).
**The thunk returns the arguments; it never calls the function under test.** We call the function with them, and time only that call.

# Instructions
1. **Setup is never timed**: everything that builds data, objects or files goes in the thunk or in module-level code. Thunks run before the timing starts; only the call of the function is timed.

2. **`cases()`: exactly 8 measured inputs.** We run them on the original function and keep the 4 that do the most work.
    - Define a real workload: the kind of data this function gets in this repository (see where the repository calls it). Use realistic scale and complexity, and a fixed random seed (`random.Random(0)`) when generating data.
    - Generate stressful inputs: complex, time-consuming, as diverse as possible. Each case should make the function do substantial and different work: different paths through its code, sizes, data distributions, hit and miss ratios, duplicates, lengths.
    - Avoid uniformity or patterns (repeating, sorted, same values) that a simple trick could exploit, unless that pattern is what the repository really passes.
    - One call should take roughly 1 ms to 200 ms on the original. Inputs where one call takes over 1 s are dropped. Keep the data in memory under about 100 MB, and building all inputs under about 10 s.
    - The function's output is compared in full after every input, so keep what it returns (and anything it writes) under about 100 000 values. Its arguments are rendered before and after each call to see whether it changed them, so keep each input's data under about 1 000 000 values.
    - Every case must run to completion on the original function without raising.

3. **`checks()`: 2 or 3 small edge inputs** (empty, one element, None, an odd type) checked only for identical behaviour, never measured. These may raise.

4. **Build real inputs; never replace code.** No mocks, no monkeypatching, no `unittest.mock`, no assigning functions or lambdas to attributes, and no subclass that overrides a method of a repository or library class -- a subclass whose `get` returns canned data instead of making the request is a mock too. Setting data (a module's configuration, an object's fields) to build an input is fine. No network access, no subprocesses. Do not fake the environment either: no stand-in programs on `PATH`, no fake system files.
    - Module globals the function reads must be set on the repository's own module (`import pricing; pricing.args = ...`, `hyperlink.slugs.update(...)`); a variable of the same name in your source is a different variable and the function never sees it.
    - Prepare the way the repository's own callers do: if a caller runs some setup before calling the function (adds a path, loads a config), do the same in the thunk.

5. **Files**: if the function reads files, create them under `WORKDIR` (a provided `pathlib.Path`; do not define it), in module-level code or in the thunk. Anything the function writes must go under `WORKDIR` too.

6. **Same work on every call**: the call is repeated many times, and every call gets the arguments of its own thunk call, all built and kept in memory before the timing starts. So keep a thunk cheap next to one call: build large data once, in module-level code, and have the thunk return it -- or a copy (`list(data)`, `dict(data)`) if the function changes it (adds to a dict, sorts or fills a list in place). Anything the function changes outside its arguments (a class attribute, a module global, a cache, a file) carries over from one call to the next, so if it caches or records what it has seen, give every thunk call new keys (e.g. with `itertools.count()`), so every call takes the same path. If it creates files, have the thunk remove them first. No time-dependent or unseeded random behaviour.

7. Import the repository's modules exactly as shown in the task. Use only the standard library, the repository itself and packages the repository already imports. Everything you can know about the repository is in the task: do not try to recall its code from memory, and build the inputs from the classes and functions shown there.

8. **If the function cannot run here at all** -- it needs network access, a remote service, credentials, special hardware, or a library that is not available -- and no input could avoid that, do not write code: reply with one line `CANNOT RUN: <the reason>`. A function whose work starts with a request to a server (an HTTP client's `get`, a database query) cannot run here, even if the rest of it only processes the answer.

Decide on the inputs and write the code: simple inputs that run are better than clever ones that do not.

# Output format
Exactly one ```python block holding the complete source. An example for a function `summarize(rows, top=10)`:
```python
import random

def _rows(n, columns, seed):
    rng = random.Random(seed)
    return [{f"c{j}": rng.randint(0, 10**6) for j in range(columns)} for _ in range(n)]

def checks():
    return [
        ("empty",      lambda: ([],)),                            # summarize([])
        ("none-value", lambda: ([{"c0": None}],)),
    ]

def cases():
    return [
        ("typical",    lambda: (_rows(2_000, 4, 0),)),            # summarize(rows)
        ("top-100",    lambda: call(_rows(5_000, 4, 1), top=100)), # summarize(rows, top=100)
        # ... 8 in total
    ]
```
A second example, for a method `Index.lookup(self, words)` of `search/index.py`. The instance is built in the thunk and passed first; the vocabulary file it reads is created under `WORKDIR`; a module setting it reads is set on the repository's own module; and because it records the words it has seen in `self.seen`, every thunk call gets words of its own, so that every call takes the same path:
```python
import itertools
import random
import search.index
from search.index import Index

search.index.CASE_SENSITIVE = False                  # a setting the method reads: data, set on its module
_VOCAB = WORKDIR / "vocab.txt"                       # a file it reads
_VOCAB.write_text("\n".join(f"w{i}" for i in range(50_000)))
_batch = itertools.count()

def _words(n, hit_ratio, seed):
    rng = random.Random(seed)
    b = next(_batch)                                 # fresh misses for every thunk call
    return [f"w{rng.randrange(50_000)}" if rng.random() < hit_ratio else f"x{b}_{i}"
            for i in range(n)]

def checks():
    return [("no-words", lambda: (Index(_VOCAB), []))]

def cases():
    return [
        ("mostly-hits",   lambda: (Index(_VOCAB), _words(20_000, 0.9, 0))),
        ("mostly-misses", lambda: (Index(_VOCAB), _words(20_000, 0.1, 1))),
        # ... 8 in total
    ]
```


=== USER ===

Repository: dx-toolkit
Function under test: `extract_assay_germline` in `src/python/dxpy/cli/dataset_utilities.py`
Import it as `from dxpy.cli.dataset_utilities import extract_assay_germline`.

## The function
```python
def extract_assay_germline(args):
    """
    Retrieve the selected data or generate SQL to retrieve the data from an genetic variant assay in a dataset or cohort based on provided rules.
    """
    ######## Input combination validation ########
    filter_given = False
    if args.retrieve_allele or args.retrieve_annotation or args.retrieve_genotype:
        filter_given = True
    #### Check if valid options are passed with the --json-help flag ####
    if args.json_help:
        if not filter_given:
            err_exit(
                'Please specify one of the following: --retrieve-allele, --retrieve-genotype or --retrieve-annotation" for details on the corresponding JSON template and filter definition.'
            )
        elif args.list_assays or args.assay_name or args.sql or args.output:
            err_exit(
                "Please check to make sure the parameters are set properly. --json-help cannot be specified with options other than --retrieve-annotation/--retrieve-allele/--retrieve-genotype."
            )
    #### Validate that other arguments are not passed with --list-assays ####
    if args.list_assays:
        if args.sql:
            err_exit("The flag, --sql, cannot be used with --list-assays.")
        elif args.output:
            err_exit(
                'When --list-assays is specified, output is to STDOUT. "--output" may not be supplied.'
            )
        elif filter_given:
            err_exit("--list-assays cannot be presented with other options.")

    #### Validate that a retrieve options infer_ref or infer_nocall are not passed with retrieve_allele or retrieve_annotation ####
    if args.infer_ref or args.infer_nocall:
        if args.retrieve_allele or args.retrieve_annotation or args.sql or args.list_assays:
            err_exit(
                "The flags, --infer-ref and --infer-nocall, can only be used with --retrieve-genotype."
            )

    #### Check if the retrieve options are passed correctly, print help if needed ####
    if args.retrieve_allele:
        if args.json_help:
            print(
                comment_fill('Filters and respective definitions', comment_string='# ') + '\n#\n' +
                comment_fill('rsid: rsID associated with an allele or set of alleles. If multiple values are provided, the conditional search will be, "OR." For example, ["rs1111", "rs2222"], will search for alleles which match either "rs1111" or "rs2222". String match is case sensitive. Duplicate values are permitted and will be handled silently.') + '\n#\n' +
                comment_fill('type: Type of allele. Accepted values are "SNP", "Ins", "Del", "Mixed". If multiple values are provided, the conditional search will be, "OR." For example, ["SNP", "Ins"], will search for variants which match either "SNP" or "Ins". String match is case sensitive.') + '\n#\n' +
                comment_fill('dataset_alt_af: Dataset alternate allele frequency, a json object with empty content or two sets of key/value pair: {min: 0.1, max:0.5}. Accepted numeric value for each key is between and including 0 and 1.  If a user does not want to apply this filter but still wants this information in the output, an empty json object should be provided.') + '\n#\n' +
                comment_fill('gnomad_alt_af: gnomAD alternate allele frequency. a json object with empty content or two sets of key/value pair: {min: 0.1, max:0.5}. Accepted value for each key is between 0 and 1. If a user does not want to apply this filter but still wants this information in the output, an empty json object should be provided.') + '\n#\n' +
                comment_fill('location: Genomic range in the reference genome where the starting position of alleles fall into. If multiple values are provided in the list, the conditional search will be, "OR." String match is case sensitive.') + '\n#\n' +
                comment_fill('JSON filter template for --retrieve-allele', comment_string='# ') + '\n' +
'{\n  "rsid": ["rs11111", "rs22222"],\n  "type": ["SNP", "Del", "Ins"],\n  "dataset_alt_af": {"min": 0.001, "max": 0.05},\n  "gnomad_alt_af": {"min": 0.001, "max": 0.05},\n  "location": [\n    {\n      "chromosome": "1",\n      "starting_position": "10000",\n      "ending_position": "20000"\n    },\n    {\n      "chromosome": "X",\n      "starting_position": "500",\n      "ending_position": "1700"\n    }\n  ]\n}'
            )
            sys.exit(0)
    elif args.retrieve_annotation:
        if args.json_help:
            print(
                comment_fill('Filters and respective definitions', comment_string='# ') + '\n#\n' +
                comment_fill('allele_id: ID of an allele for which annotations should be returned. If multiple values are provided, annotations for any alleles that match one of the values specified will be listed. For example, ["1_1000_A_T", "1_1010_C_T"], will search for annotations of alleles which match either "1_1000_A_T" or ""1_1010_C_T". String match is case insensitive.') + '\n#\n' +
                comment_fill('gene_name: Gene name of the annotation. A list of gene names whose annotations will be returned. If multiple values are provided, the conditional search will be, "OR." For example, ["BRCA2", "ASPM"], will search for annotations which match either "BRCA2" or "ASPM". String match is case insensitive.') + '\n#\n' +
                comment_fill('gene_id: Ensembl gene ID (ENSG) of the annotation. If multiple values are provided, the conditional search will be, "OR." For example, ["ENSG00000302118", "ENSG00004000504"], will search for annotations which match either "ENSG00000302118" or "ENSG00004000504". String match is case insensitive.') + '\n#\n' +
                comment_fill('feature_id: Ensembl feature id (ENST) where the range overlaps with the variant. Currently, only  coding transcript IDs are searched. If multiple values are provided, the conditional search will be, "OR." For example, ["ENST00000302118.5", "ENST00004000504.1"], will search for annotations which match either "ENST00000302118.5" or "ENST00004000504.1". String match is case insensitive.') + '\n#\n' +
                comment_fill('consequences: Consequence as recorded in the annotation. If multiple values are provided, the conditional search will be, "OR." For example, ["5_prime_UTR_variant", "3_prime_UTR_variant"], will search for annotations which match either "5 prime UTR variant" or "3 prime UTR variant". String match is case sensitive. For all supported consequences terms, please refer to snpeff: http://pcingola.github.io/SnpEff/se_inputoutput/#effect-prediction-details (Effect Seq. Ontology column). This filter cannot be specified by itself, and must be included with at least one of the following filters: "gene_id", "gene_name",or "feature_id".') + '\n#\n' +
                comment_fill('putative_impact: Putative impact as recorded in the annotation. Possible values are [ "HIGH", "MODERATE", "LOW", "MODIFIER"]. If multiple values are provided, the conditional search will be, "OR." For example, ["MODIFIER", "HIGH"], will search for annotations which match either "MODIFIER" or "HIGH". String match is case insensitive. For all supported terms, please refer to snpeff: http://pcingola.github.io/SnpEff/se_inputoutput/#impact-prediction. This filter cannot be specified by itself, and must be included with at least one of the following filters: "gene_id", "gene_name", or "transcript_id".') + '\n#\n' +
                comment_fill('hgvs_c: HGVS (DNA) code of the annotation. If multiple values are provided, the conditional search will be, "OR." For example, ["c.-49A>G", "c.-20T>G"], will search for annotations which match either "c.-49A>G" or "c.-20T>G". String match is case sensitive.') + '\n#\n' +
                comment_fill('hgvs_p: HGVS (Protein) code of the annotation. If multiple values are provided, the conditional search will be, "OR." For example, ["p.Gly2Asp", "p.Aps2Gly"], will search for annotations which match either "p.Gly2Asp" or "p.Aps2Gly". String match is case sensitive.') + '\n#\n' +
                comment_fill('JSON filter template for --retrieve-annotation', comment_string='# ') + '\n' +
                '{\n  "allele_id":["1_1000_A_T","2_1000_G_C"],\n  "gene_name": ["BRCA2"],\n  "gene_id": ["ENST00000302118"],\n  "feature_id": ["ENST00000302118.5"],\n  "consequences": ["5 prime UTR variant"],\n  "putative_impact": ["MODIFIER"],\n  "hgvs_c": ["c.-49A>G"],\n  "hgvs_p": ["p.Gly2Asp"]\n}'
            )
            sys.exit(0)
    elif args.retrieve_genotype:
        if args.json_help:
            print(
                comment_fill('Filters and respective definitions', comment_string='# ') + '\n#\n' +
                comment_fill('allele_id: ID(s) of one or more alleles for which sample genotypes will be returned. If multiple values are provided, any samples having at least one allele that match any of the values specified will be listed. For example, ["1_1000_A_T", "1_1010_C_T"], will search for samples with at least one allele matching either "1_1000_A_T" or "1_1010_C_T". String match is case insensitive.') + '\n#\n' +
                comment_fill('location: Genomic position in the reference genome of the starting position of the alleles.  If multiple values are provided in the list, the conditional search will be, "OR." String match is case sensitive.') + '\n#\n' +
                comment_fill('allele_id and location are mutually exclusive filters.') + '\n#\n' +
                comment_fill('sample_id: Optional, one or more sample IDs for which sample genotypes will be returned. If the provided object is a cohort, this further intersects the sample ids. If a user has a list of samples more than 1,000, it is recommended to use a cohort id containing all the samples.') + '\n#\n' +
                comment_fill('genotype_type: Optional, one or more genotype types for which sample genotype types will be returned.') + '\n' +
                comment_fill('One of:') + '\n' +
                comment_fill('\tref\t(homozygous for the reference allele\t\t\te.g. 0/0)') + '\n' +
                comment_fill('\thet-ref\t(heterozygous for the ref allele and alt allele\t\te.g. 0/1)') + '\n' +
                comment_fill('\thom\t(homozygous for the non-ref allele\t\t\te.g. 1/1)') + '\n' +
                comment_fill('\thet-alt\t(heterozygous with two distinct alt alleles\t\te.g. 1/2)') + '\n' +
                comment_fill('\thalf\t(only one allele is known, second allele is unknown\te.g. ./1)') + '\n' +
                comment_fill('\tno-call\t(both alleles are unknown\t\t\t\te.g. ./.)') + '\n#\n' +
                comment_fill('JSON filter templates for --retrieve-genotype', comment_string='# ') + '\n#\n' +
                comment_fill('Example using location:', comment_string='# ') + '\n' +
                pretty_print_json(
                    {
                        "sample_id": ["s1", "s2"],
                        "location": [
                            {"chromosome": "1", "starting_position": "10000"},
                            {"chromosome": "X", "starting_position": "500"},
                        ],
                        "genotype_type": ["ref", "het-ref", "hom", "het-alt", "half", "no-call"],
                    }
                ) + '\n' +
                comment_fill('Example using allele_id:', comment_string='# ') + '\n' +
                pretty_print_json({
                    "sample_id": ["s1", "s2"],
                    "allele_id": ["1_1000_A_T", "2_1000_G_C"],
                    "genotype_type": ["het-ref", "hom", "het-alt", "half"],
                }
                )
            )
            sys.exit(0)

    if args.retrieve_allele:
        filter_dict = json_validation_function("allele", args)
    elif args.retrieve_annotation:
        filter_dict = json_validation_function("annotation", args)
    elif args.retrieve_genotype:
        filter_dict = json_validation_function("genotype", args)

    #### Validate that a retrieve option is passed with --assay-name ####
    if args.assay_name:
        if not filter_given:
            err_exit(
                "--assay-name must be used with one of --retrieve-allele,--retrieve-annotation, --retrieve-genotype."
            )

    #### Validate that a retrieve option is passed with --sql ####
    if args.sql:
        if not filter_given:
            err_exit(
                "When --sql provided, must also provide at least one of the three options: --retrieve-allele <JSON>; --retrieve-genotype <JSON>; --retrieve-annotation <JSON>."
            )

    ######## Data Processing ########
    project, entity_result, resp, dataset_project = resolve_validate_record_path(args.path)

    if "CohortBrowser" in resp["recordTypes"] and any(
        [args.list_assays, args.assay_name]
    ):
        err_exit(
            "Currently --assay-name and --list-assays may not be used with a CohortBrowser record (Cohort Object) as input. To select a specific assay or to list assays, please use a Dataset Object as input."
        )
    dataset_id = resp["dataset"]
    rec_descriptor = DXDataset(dataset_id, project=dataset_project).get_descriptor()

    selected_assay_name, selected_assay_id, selected_ref_genome, additional_descriptor_info = get_assay_name_info(
        args.list_assays, args.assay_name, args.path, "germline", rec_descriptor
    )

    out_file, print_to_stdout = assign_output_method(args, resp["recordName"], "germline")

    filter_type = None
    if args.retrieve_allele:
        filter_type = "allele"
    elif args.retrieve_annotation:
        filter_type = "annotation"

    if filter_type and filter_given:
        payload, fields_list = final_payload(
            full_input_dict=filter_dict,
            name=selected_assay_name,
            id=selected_assay_id,
            project_context=project,
            genome_reference=selected_ref_genome,
            filter_type=filter_type,
        )

        add_germline_base_sql(resp, payload)

        if args.sql:
            sql_results = raw_query_api_call(resp, payload)

            if print_to_stdout:
                print(sql_results)
            else:
                with open(out_file, "w") as sql_file:
                    print(sql_results, file=sql_file)
        else:
            resp_raw = raw_api_call(resp, payload)
            ordered_results = sorted(resp_raw["results"], key=sort_germline_variant)

            csv_from_json(
                out_file_name=out_file,
                print_to_stdout=print_to_stdout,
                sep="\t",
                raw_results=ordered_results,
                column_names=fields_list,
                quote_char=str("|"),
            )

    if args.retrieve_genotype and filter_given:
        exclude_refdata: bool = additional_descriptor_info.get("exclude_refdata")
        exclude_halfref: bool = additional_descriptor_info.get("exclude_halfref")
        exclude_nocall: bool = additional_descriptor_info.get("exclude_nocall")
        inference_validation(
            args.infer_nocall,
            args.infer_ref,
            filter_dict,
            exclude_nocall,
            exclude_refdata,
            exclude_halfref
            )
        # in case of infer flags, we query all the genotypes and do the filtering post query
        if args.infer_ref or args.infer_nocall:
            types_to_filter_out = get_types_to_filter_out_when_infering(filter_dict.get("genotype_type", []))
            filter_dict["genotype_type"] = []

        # get a list of requested genotype types for the genotype table only queries
    # ... (truncated)
```

## Imports of its module
```python
from __future__ import print_function, unicode_literals, division, absolute_import, annotations
import sys
import collections
import copy
import json
import os
import re
import csv
import dxpy
import codecs
import subprocess
from functools import reduce
from typing import Optional
from ..utils.printing import fill
from ..bindings import DXRecord
from ..bindings.dxdataobject_functions import is_dxlink, describe
from ..bindings.dxfile import DXFile
from ..utils.resolver import resolve_existing_path, is_hashid, ResolutionError, resolve_path, check_folder_exists
from ..utils.file_handle import as_handle
from ..utils.describe import print_desc
from ..exceptions import (
    err_exit,
    DXError,
    PermissionDenied,
    InvalidInput,
    InvalidState,
    default_expected_exceptions,
)
from ..dx_extract_utils.filter_to_payload import validate_JSON, final_payload
from ..dx_extract_utils.germline_utils import (
    get_genotype_only_types,
    add_germline_base_sql,
    sort_germline_variant,
    harmonize_germline_sql,
    harmonize_germline_results,
    get_germline_ref_payload,
    get_germline_loci_payload,
    update_genotype_only_ref,
    get_genotype_types,
    infer_genotype_type,
    # ... (truncated)
```

## Definitions it uses from the same module
```python
def resolve_validate_record_path(path):

    project, folder_path, entity_result = resolve_existing_path(path)

    if project is None:
        raise ResolutionError(
            'Unable to resolve "'
            + path
            + '" to a data object or folder name in a project'
        )
    elif project != entity_result["describe"]["project"]:
        raise ResolutionError(
            'Unable to resolve "'
            + path
            + "\" to a data object or folder name in '"
            + project
            + "'"
        )

    if entity_result["describe"]["class"] != "record":
        err_exit(
            "{}: Invalid path. The path must point to a record type of cohort or dataset".format(path)
            
        )

    try:
        resp = dxpy.DXHTTPRequest(
            "/" + entity_result["id"] + "/visualize",
            {"project": project, "cohortBrowser": False},
        )
    except PermissionDenied:
        err_exit("Insufficient permissions", expected_exceptions=(PermissionDenied,))
    except (InvalidInput, InvalidState):
        err_exit(
            "%s : Invalid cohort or dataset" % entity_result["id"],
            expected_exceptions=(
                InvalidInput,
                InvalidState,
            ),
        )
    except Exception as details:
        err_exit(str(details))

    if resp["datasetVersion"] != "3.0":
        err_exit(
            "%s : Invalid version of cohort or dataset. Version must be 3.0"
            % resp["datasetVersion"]
        )

    if ("Dataset" in resp["recordTypes"]) or ("CohortBrowser" in resp["recordTypes"]):
        dataset_project = resp["datasetRecordProject"]
    else:
        err_exit(
            "%s : Invalid path. The path must point to a record type of cohort or dataset"
            % resp["recordTypes"]
        )

    return project, entity_result, resp, dataset_project

def raw_query_api_call(resp, payload):
    return viz_query_api_call(resp, payload, 'raw-query')

def raw_api_call(resp, payload, sql_message=True):
    resource_val = resp["url"] + "/data/3.0/" + resp["dataset"] + "/raw"
    try:
        resp_raw = dxpy.DXHTTPRequest(
            resource=resource_val, data=payload, prepend_srv=False
        )
        if "error" in resp_raw.keys():
            if resp_raw["error"]["type"] == "InvalidInput":
                err_message = "Insufficient permissions due to the project policy.\n" + resp_raw["error"]["message"]
            elif sql_message and resp_raw["error"]["type"] == "QueryTimeOut":
                err_message = "Please consider using `--sql` option to generate the SQL query and query via a private compute cluster.\n" + resp_raw["error"]["message"]        
            elif resp_raw["error"]["type"] == "DxApiError":
                err_message = resp_raw["error"]["message"]
            else:
                err_message = resp_raw["error"]
            err_exit(str(err_message))
    except Exception as details:
        err_exit(str(details))
    return resp_raw

def json_validation_function(filter_type, args):
    filter_arg = "args.retrieve_" + filter_type
    filter_value = str(vars(args)["retrieve_" + filter_type])
    filter = {}
    if filter_value.endswith(".json"):
        if os.path.isfile(filter_value):
            if os.stat(filter_value).st_size == 0:
                err_exit(
                    'No filter given for --retrieve-{filter_type} or JSON for "--retrieve-{filter_type}" does not contain valid filter information.'.format(
                        filter_type=filter_type
                    )
                )
            else:
                with open(filter_value, "r") as json_file:
                    try:
                        filter = json.load(json_file)
                    except Exception as json_error:
                        err_exit(
                            "JSON for variant filters is malformatted.",
                            expected_exceptions=default_expected_exceptions,
                        )
        else:
            err_exit(
                "JSON file {filter_json} provided does not exist".format(
                    filter_json=filter_value
                )
            )
    else:
        if filter_value == "{}":
            err_exit(
                'No filter given for --retrieve-{filter_type} or JSON for "--retrieve-{filter_type}" does not contain valid filter information.'.format(
                    filter_type=filter_type
                )
            )
        else:
            try:
                filter = json.loads(filter_value)
            except Exception as json_error:
                err_exit(
                    "JSON for variant filters is malformatted.",
                    expected_exceptions=default_expected_exceptions,
                )

    if filter_type in ["allele", "annotation", "genotype"]:
        validate_JSON(filter, filter_type)
    elif filter_type in ["variant"]:
        validate_somatic_filter(filter, filter_type)

    return filter

def assign_output_method(args, record_name, friendly_assay_type):
    #### Decide output method based on --output and --sql ####
    if args.sql:
        file_name_suffix = ".data.sql"
    elif friendly_assay_type == 'somatic' and args.retrieve_meta_info:
        file_name_suffix = ".vcf_meta_info.txt"
    else:
        file_name_suffix = ".tsv"
    file_already_exist = []
    files_to_check = []
    out_file = ""

    print_to_stdout = False
    if args.output is None:
        out_directory = os.getcwd()
        out_file = os.path.join(out_directory, record_name + file_name_suffix)
        files_to_check.append(out_file)
    elif args.output == "-":
        print_to_stdout = True
    elif os.path.exists(args.output):
        if os.path.isdir(args.output):
            err_exit("--output should be a file, not a directory.")
        else:
            file_already_exist.append(args.output)
    elif os.path.exists(os.path.dirname(args.output)) or not os.path.dirname(
        args.output
    ):
        out_file = args.output
    else:
        err_exit(
            "Error: {path} could not be found".format(path=os.path.dirname(args.output))
        )

    for file in files_to_check:
        if os.path.exists(file):
            file_already_exist.append(file)

    if file_already_exist:
        err_exit("Cannot specify the output to be an existing file.")
    return out_file, print_to_stdout

def get_assay_name_info(
    list_assays, assay_name, path, friendly_assay_type, rec_descriptor
):
    """
    Generalized function for determining assay name and reference genome
    """
    if friendly_assay_type == "germline":
        assay_type = "genetic_variant"
    elif friendly_assay_type == "somatic":
        assay_type = "somatic_variant"

    #### Get names of genetic assays ####
    if list_assays:
        (target_assays, other_assays) = get_assay_info(
            rec_descriptor, assay_type=assay_type
        )
        if not target_assays:
            err_exit("There's no {} assay in the dataset provided.".format(friendly_assay_type))
        else:
            for a in target_assays:
                print(a["name"])
            sys.exit(0)

    #### Decide which assay is to be queried and which ref genome is to be used ####
    (target_assays, other_assays) = get_assay_info(
        rec_descriptor, assay_type=assay_type
    )

    target_assay_names = [ga["name"] for ga in target_assays]
    target_assay_ids = [ga["uuid"] for ga in target_assays]
    other_assay_names = [oa["name"] for oa in other_assays]
    # other_assay_ids = [oa["uuid"] for oa in other_assays]

    if target_assay_names and target_assay_ids:
        selected_assay_name = target_assay_names[0]
        selected_assay_id = target_assay_ids[0]
    else:
        err_exit("There's no {} assay in the dataset provided.".format(friendly_assay_type))
    if assay_name:
        if assay_name not in list(target_assay_names):
            if assay_name in list(other_assay_names):
                err_exit(
                    "This is not a valid assay. For valid assays accepted by the function, `extract_assay {}`, please use the --list-assays flag.".format(
                        friendly_assay_type
                    )
                )
            else:
                err_exit(
                    "Assay {assay_name} does not exist in the {path}.".format(
                        assay_name=assay_name, path=path
                    )
                )
        else:
            selected_assay_name = assay_name
            for ga in target_assays:
                if ga["name"] == assay_name:
                    selected_assay_id = ga["uuid"]
    
    additional_descriptor_info = {}

    # ... (truncated)

def comment_fill(string, comment_string='#  ', **kwargs):
    width_adjustment = kwargs.pop('width_adjustment', 0) - len(comment_string)
    return re.sub('^', comment_string, fill(string, width_adjustment=width_adjustment, **kwargs), flags=re.MULTILINE)

def retrieve_samples(resp: dict, assay_name: str, assay_id: str) -> list:
    """
    Get the list of sample_ids from the sample table for the selected assay.
    """
    sample_payload = {
        "project_context": resp["datasetRecordProject"],
        "fields": [{"sample_id": "sample$sample_id"}],
        "raw_filters": {"assay_filters": {"name": assay_name, "id": assay_id}},
    }
    return [_["sample_id"] for _ in raw_api_call(resp, sample_payload)["results"]]
```

## Everything else its module defines (headers only)
```python
class VizserverError(Exception):
class DXDataset(DXRecord):
    def __init__(self, dxid=None, project=None):
    # methods: get_descriptor, get_dictionary
class DXDatasetDescriptor:
    def __init__(self, dxfile, **kwargs):
    # methods: get_dictionary
class DXDatasetDictionary:
    def __init__(self, descriptor, codings=None):
    # methods: load_data_dictionary, create_entity_dframe, get_join_path_to_entity_field_map, create_edge, load_coding_dictionary, create_coding_name_dframe, load_entity_dictionary, write
def viz_query_api_call(resp, payload, route):
def raw_cohort_query_api_call(resp, payload):
def viz_meta_codings_page(resp: dict, payload: dict) -> dict:
def _hierarchy_from_parents(codes_to_parent: dict, all_codes: list) -> list:
def _finalize_split_codings(codings: dict) -> dict:
def get_codings(resp: dict, project_context: str, limit: Optional[int] = None) -> dict:
def extract_dataset(args):
def get_assay_info(rec_descriptor, assay_type):
def retrieve_meta_info(resp, project_id, assay_id, assay_name, print_to_stdout, out_file_name):
def retrieve_entities(model):
def list_fields(model, main_entity, args):
def csv_from_json(
    out_file_name="",
    print_to_stdout=False,
    sep=",",
    raw_results=[],
    column_names=[],
    # ... (truncated)
def extract_assay_somatic(args):
def extract_assay_expression(args):
def resolve_validate_dx_path(path):
def validate_cohort_ids(descriptor, project, resp, ids):
    # Usually the name of the table
def has_access_level(project, access_level):
def validate_project_access(project, access_level="UPLOAD"):
def create_cohort(args):
```

## Signatures of what its module imports from the repository
```python
# from ..exceptions import err_exit
def err_exit(message='', code=None, expected_exceptions=default_expected_exceptions, arg_parser=None,
             ignore_sigpipe=True, exception=None):
    """Exits the program, printing information about the last exception (if"""
    ...

# from ..dx_extract_utils.filter_to_payload import final_payload
def final_payload(
    full_input_dict,
    name,
    id,
    project_context,
    genome_reference,
    filter_type,
    order=True,
    exclude_nocall=None,
    exclude_refdata=None,
    exclude_halfref=None
):
    """Assemble the top level payload.  Top level dict contains the project context, fields (return columns),"""
    ...

# from ..dx_extract_utils.germline_utils import get_genotype_only_types
def get_genotype_only_types(filter_dict, exclude_refdata, exclude_halfref, exclude_nocall):
    """Returns a list of genotype types for the filter that are use in genotype table only queries."""
    ...

# from ..dx_extract_utils.germline_utils import add_germline_base_sql
def add_germline_base_sql(resp, payload):
    ...

# from ..dx_extract_utils.germline_utils import sort_germline_variant
def sort_germline_variant(d):
    ...

# from ..dx_extract_utils.germline_utils import harmonize_germline_sql
def harmonize_germline_sql(sql):
    """Harmonize the SQL statement for genotype table only queries to include columns to UNION with genotype and allele"""
    ...

# from ..dx_extract_utils.germline_utils import harmonize_germline_results
def harmonize_germline_results(results, fields_list):
    """Harmonizes raw query results to include all columns in fields_list. Columns not in fields_list have value None."""
    ...

# from ..dx_extract_utils.germline_utils import get_germline_ref_payload
def get_germline_ref_payload(results, genotype_payload):
    """Create a payload to query locus_id/ref pairs from the allele table for genotypes missing ref column values."""
    ...

# from ..dx_extract_utils.germline_utils import get_germline_loci_payload
def get_germline_loci_payload(locations, genotype_payload):
    """Create a payload to query locus ids from the allele table with a location filter"""
    ...

# from ..dx_extract_utils.germline_utils import update_genotype_only_ref
def update_genotype_only_ref(results, locus_id_refs):
    """Update genotype results with ref column values from locus_id/ref query result"""
    ...

# from ..dx_extract_utils.germline_utils import get_genotype_types
def get_genotype_types(filter_dict):
    """Returns a list of genotype types for the filter that are use in genotype and allele table queries."""
    ...

# from ..dx_extract_utils.germline_utils import infer_genotype_type
def infer_genotype_type(
    samples: list, loci: list[dict], result_entries: list[dict], type_to_infer: str
) -> list[dict]:
    """If the result_entries does not contain entry with sample_id of specifific starting_position the the genotype type is either no-call or ref."""
    ...

# from ..dx_extract_utils.germline_utils import get_types_to_filter_out_when_infering
def get_types_to_filter_out_when_infering(
    requested_types: list[str],
) -> list:
    """Infer option require all genotypes types to be queried."""
    ...

# from ..dx_extract_utils.germline_utils import filter_results
def filter_results(
    results: list[dict], key: str, restricted_values: list
) -> list[dict]:
    """Filters results by key and restricted_values."""
    ...

# from ..dx_extract_utils.input_validation import inference_validation
def inference_validation(
    infer_nocall: bool,
    infer_ref: bool,
    filter_dict: dict,
    exclude_nocall: bool,
    exclude_refdata: bool,
    exclude_halfref: bool,
):
    ...

# from .output_handling import pretty_print_json
def pretty_print_json(json_dict: dict) -> str:
    """Pretty-prints the provided JSON object."""
    ...

# from ..utils.printing import fill
def fill(string, width_adjustment=0, **kwargs):
    ...

# from ..bindings.dxdataobject_functions import is_dxlink
def is_dxlink(x):
    """:param x: A potential DNAnexus link"""
    ...

# from ..bindings.dxdataobject_functions import describe
def describe(id_or_link, **kwargs):
    """:param id_or_link: String containing an object ID or dict containing a DXLink,"""
    ...

# from ..bindings.dxfile import DXFile
class DXFile(DXDataObject):
    _class = "file"
    _describe = staticmethod(dxpy.api.file_describe)
    _add_types = staticmethod(dxpy.api.file_add_types)
    _remove_types = staticmethod(dxpy.api.file_remove_types)
    _get_details = staticmethod(dxpy.api.file_get_details)
    _set_details = staticmethod(dxpy.api.file_set_details)
    _set_visibility = staticmethod(dxpy.api.file_set_visibility)
    _rename = staticmethod(dxpy.api.file_rename)
    _set_properties = staticmethod(dxpy.api.file_set_properties)
    _add_tags = staticmethod(dxpy.api.file_add_tags)
    _remove_tags = staticmethod(dxpy.api.file_remove_tags)
    _close = staticmethod(dxpy.api.file_close)
    _list_projects = staticmethod(dxpy.api.file_list_projects)
    _http_threadpool_size = DXFILE_HTTP_THREADS
    _http_threadpool = dxpy.utils.get_futures_threadpool(max_workers=_http_threadpool_size)
    NO_PROJECT_HINT = 'NO_PROJECT_HINT'
    @classmethod
    def set_http_threadpool_size(cls, num_threads):
        """.. deprecated:: 0.191.0"""
        ...
    def __init__(self, dxid=None, project=None, mode=None, read_buffer_size=DEFAULT_BUFFER_SIZE,
                 write_buffer_size=DEFAULT_BUFFER_SIZE, expected_file_size=None, file_is_mmapd=False):
        """:param dxid: Object ID"""
        ...
    next = next
    __next__ = next
    def set_ids(self, dxid, project=None):
        """:param dxid: Object ID"""
        ...
    def seek(self, offset, from_what=os.SEEK_SET):
        """:param offset: Position in the file to seek to"""
        ...
    def tell(self):
        """Returns the current position of the file read cursor."""
        ...
    def flush(self, multithread=True, **kwargs):
        """Flushes the internal write buffer."""
        ...
    def write(self, data, multithread=True, **kwargs):
    # ... (truncated)

# from ..utils.resolver import resolve_existing_path
def resolve_existing_path(path, expected=None, ask_to_resolve=True, expected_classes=None, allow_mult=False,
                          describe=True, all_mult=False, allow_empty_string=True, visibility="either"):
    """:param expected: one of the following: "folder", "entity", or None to indicate"""
    ...

# from ..utils.resolver import is_hashid
def is_hashid(string):
    ...

# from ..utils.resolver import ResolutionError
class ResolutionError(DXError):
    def __init__(self, msg):
        ...

# from ..utils.resolver import resolve_path
def resolve_path(path, expected=None, multi_projects=False, allow_empty_string=True):
    """:param path: A path to a data object to attempt to resolve"""
    ...

# from ..utils.resolver import check_folder_exists
def check_folder_exists(project, path, folder_name):
    """:param project: project id"""
    ...
```

## Where the repository calls it
No call sites found.

Write `checks()` and `cases()` for `extract_assay_germline`. Remember: setup in the thunk or at module level, never timed.