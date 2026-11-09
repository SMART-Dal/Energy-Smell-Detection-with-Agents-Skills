import json
subs=[json.loads(l) for l in open('submissions.jsonl')]
S2=[json.loads(l) for l in open('step2.jsonl')]
key={ # (unit,label)->submission id
}
labels={"C3S4-predictions-index":"a","C3S4-process_docs-docs-count":"a","C3S2-count_terms-common-once":"a","C1S5-sample_valid_data-filter-first":"a",
"C10S1-remove_control_characters-translate":"a","C1S8-extract_documents-tell":"a","C10S4-split_text-join":"a","C1S4-what_language-text-once":"a",
"C1S4-ndcg_score-discounts-once":"a","C8S3-add_impressions-content-once":"a","C10S2-float_to_binary-bool":"a","C3S2-prepare_sim_map-seq-length":"a",
"C6S2-sample_images-index-first":"a","C3S6-process_users-limit-first":"a","C8S2-should_filter_token-compiled-default":"a",
"C10S2-category_ctrs-read_impressions-reader":"a","C2S1-lookup_news_index-inline":"a","C10S3-train_cold_start-write_embeddings-tolist-once":"a",
"C3S5-read_news-lazy-abstract":"a","C1S1-process_docs-total_count":"b","C10S3-accepted_words-process_docs-update":"a","C3S2-select_documents-bound":"a",
"C10S2-evaluate-read_impressions-reader":"a","C8S3-read_bert_embeddings_from_file-news-once":"a","C10S2-write_json_file-replace":"a",
"C6S2-gen_similarity_maps-no-copy":"c","C3S2-gen_similarity_maps-filter-once":"b"}
status={s['id']:s['agent_measurement']['status'] for s in subs}
msg={s['id']:(s['agent_measurement'].get('message') or s['agent_measurement'].get('reason') or '') for s in subs}
for s in subs: key[(s['unit'],labels[s['id']])]=s['id']
key_same={("news/src/python/mind_data.py::MindData.sample_valid_data","b"):"C1S5-sample_valid_data-filter-first"}
requested={"news/src/python/create_category_ctrs.py::read_content_file","incremental-search/search-suggestions/count_terms.py::process_doc","news/src/python/create_category_ctrs.py::read_impressions_file"}
blocked_units={
"visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.gen_similarity_maps":"inputs.py: the unit's module does not load here: AttributeError: SimMapGenerator is not defined here: loading the module skipped line 19 `class SimMapGenerator:` (TypeError), with stand-ins for colpali_engine",
"examples/embedder-auto-training-evaluation/training-evaluation/train.py::TrainDataset.__getitem__":"inputs.py: it cannot run here: `TrainDataset.__getitem__` always finishes by constructing a `sentence_transformers.InputExample`, and `sentence_transformers` is not available in this environment (it is stubbed)",
}
net=("calls a live Vespa, HTTP endpoint, LLM or cloud service in its body; not asked for inputs",)
out=[]
for r in S2:
    outs=[]
    for d in r['decisions']:
        if d['verdict']!='accepted': continue
        k=(r['unit'],d['label'])
        if k in key_same:
            outs.append({"label":d['label'],"outcome":"same_repair_as","submission":key_same[k],"why":None}); continue
        if k in key:
            sid=key[k]; st=status[sid]
            if st in('no_inputs',):
                outs.append({"label":d['label'],"outcome":"blocked","submission":None,"why":"verify.py: no_inputs: the unit's module does not load here: AttributeError: SimMapGenerator is not defined here: loading the module skipped line 19 `class SimMapGenerator:` (TypeError), with stand-ins for colpali_engine (repair is written in submissions.jsonl as "+sid+")"})
            elif st=='over_limit':
                if r['unit'] in blocked_units:
                    outs.append({"label":d['label'],"outcome":"blocked","submission":None,"why":blocked_units[r['unit']]+" (repair written in submissions.jsonl as "+sid+")"})
                else:
                    outs.append({"label":d['label'],"outcome":"deferred","submission":None,"why":"submitted as "+sid+" but over_limit: 20 repairs already had a verdict, so it was not measured"})
            else:
                outs.append({"label":d['label'],"outcome":"submitted","submission":sid,"why":None})
            continue
        if r['unit'] in blocked_units:
            outs.append({"label":d['label'],"outcome":"blocked","submission":None,"why":blocked_units[r['unit']]}); continue
        if r['unit'] in requested:
            why="inputs were requested and the unit is runnable here, but the 20 measured places went to repairs expected to save more, so no repair was submitted"
        else:
            why="outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)"
        outs.append({"label":d['label'],"outcome":"deferred","submission":None,"why":why})
    if outs: out.append({"step":3,"unit":r['unit'],"outcomes":outs})
open('step3.jsonl','w').write("\n".join(json.dumps(x,ensure_ascii=False) for x in out)+"\n")
print(len(out), sum(len(x['outcomes']) for x in out))
