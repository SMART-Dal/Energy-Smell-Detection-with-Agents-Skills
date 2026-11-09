import json
st=json.load(open(".energy-inputs/status.json"))["units"]
def reason(unit):
    for k,v in st.items():
        if k==unit and v.get("state")=="failed":
            return "inputs.py: "+str(v.get("reason"))[:230]
sub={ # (basename::qual,label)->id
("spelling_corrector.py::_known_edits2","a"):"spell-edits2",
("resolver.py::get_first_pos_of_char","a"):"resolver-first-pos",
("resolver.py::get_last_pos_of_char","a"):"resolver-last-pos",
("resolver.py::split_unescaped","a"):"resolver-split",
("resolver.py::_maybe_convert_stringified_dxlink","a"):"resolver-dxlink",
("resolver.py::resolve_path","a"):"resolver-colon",
("pretty_print.py::escape_unicode_string","a"):"pp-escape",
("pretty_print.py::format_table","a"):"pp-table-len",
("pretty_print.py::flatten_json_array","a"):"pp-flatten",
("dxlog.py::DXLogHandler.truncate_message","a"):"dxlog-encode",
("dxlog.py::DXLogHandler.truncate_message","b"):"dxlog-bsearch",
("cohort_filter_payload.py::generate_pheno_filter","a"):"cohort-pheno-reduce",
("dataset_utilities.py::DXDatasetDictionary.create_coding_name_dframe","a"):"dd-coding-index",
("dataset_utilities.py::DXDatasetDictionary.load_data_dictionary","a"):"dd-load-assign",
("filter_to_payload.py::validate_JSON","a"):"fp-validate",
("germline_utils.py::harmonize_germline_results","a"):"gu-harmonize-results",
("germline_utils.py::infer_genotype_type","a"):"gu-infer-hoist",
("output_handling.py::write_expression_output","a"):"oh-sets",
("nextflow_templates.py::get_nextflow_src","a"):"nt-concat",
("nextflow_builder.py::prepare_custom_inputs","b"):"nb-required-set",
("nextflow_builder.py::prepare_custom_inputs","c"):"nb-insert",
("describe.py::format_currency","a"):"describe-locale",
("system_requirements.py::SystemRequirementsDict.override_cluster_spec","a"):"sr-cluster-copy",
("search.py::_find","a"):"search-limit",
}
same={("spelling_corrector.py::correct","a"):"spell-edits2"}
subm={json.loads(l)["id"]:json.loads(l) for l in open("submissions.jsonl")}
out=[]
for l in open("step2.jsonl"):
    r=json.loads(l)
    if not any(d["verdict"]=="accepted" for d in r["decisions"]): continue
    p,q=r["unit"].split("::"); base=p.split("/")[-1]+"::"+q
    oc=[]
    for d in r["decisions"]:
        if d["verdict"]!="accepted": continue
        k=(base,d["label"]); lab=d["label"]
        if k in same:
            oc.append({"label":lab,"outcome":"same_repair_as","submission":same[k],"why":None}); continue
        if k in sub:
            sid=sub[k]; status=subm[sid]["agent_measurement"]["status"]
            if status=="no_inputs":
                oc.append({"label":lab,"outcome":"blocked","submission":sid,"why":"verify.py: no_inputs; "+(reason(r["unit"]) or "inputs could not be generated")})
            elif status=="over_limit":
                oc.append({"label":lab,"outcome":"deferred","submission":sid,"why":"over_limit: 20 repairs already had a verdict, so verify.py did not measure it"})
            else:
                oc.append({"label":lab,"outcome":"submitted","submission":sid,"why":None})
            continue
        rs=reason(r["unit"])
        if rs: oc.append({"label":lab,"outcome":"blocked","submission":None,"why":rs})
        else: oc.append({"label":lab,"outcome":"deferred","submission":None,"why":"outside the 20 repairs measured; no repair submitted, inputs not obtained"})
    out.append({"step":3,"unit":r["unit"],"outcomes":oc})
open("step3.jsonl","w").write("".join(json.dumps(o)+"\n" for o in out))
print(len(out), sum(len(o["outcomes"]) for o in out))
from collections import Counter
print(Counter(x["outcome"] for o in out for x in o["outcomes"]))
