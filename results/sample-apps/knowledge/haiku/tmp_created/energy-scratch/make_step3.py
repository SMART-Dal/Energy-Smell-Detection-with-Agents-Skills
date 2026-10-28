import json
R = "/home/javad/energy-run/sample-apps"
step2 = [json.loads(l) for l in open(f"{R}/step2.jsonl")]
subs = {json.loads(l)["id"]: json.loads(l) for l in open(f"{R}/submissions.jsonl")}
# (unit, label) -> submission id
SUB = {
 ("feed-split.py::split_text","a"):"C10S4-split-text",
 ("colbert-long/scripts/convert.py::remove_control_characters","a"):"C10S1-control-translate",
 ("incremental-search/search-suggestions/count_terms.py::process_docs","a"):"C1S1-dead-total",
 ("incremental-search/search-suggestions/count_terms.py::process_docs","b"):"C3S4-process-docs-docs",
 ("incremental-search/search-suggestions/count_terms.py::count_terms","a"):"C10S1-count-isdisjoint",
 ("incremental-search/search-suggestions/count_terms.py::write_json_file","a"):"C10S2-write-replace",
 ("incremental-search/search-suggestions/count_terms.py::write_json_file","b"):"C9S1-write-once",
 ("incremental-search/search-suggestions/accepted_words.py::process_docs","a"):"C10S3-accepted-update",
 ("text-video-search/src/python/embedding.py::sample_images","a"):"C6S2-sample-index",
 ("news/src/python/evaluate.py::predictions","a"):"C5S2-predictions-index",
 ("news/src/python/create_bert_embeddings.py::write_embedding","a"):"C9S1-embedding-join",
 ("visual-retrieval-colpali/prepare_feed_deploy.py::float_to_binary_embedding","a"):"C10S1-binary-vectorise",
 ("text-search/python/sample-queries-and-documents.py::select_documents","a"):"C10S3-select-update",
 ("use-case-shopping/create_suggestions.py::filter_content","a"):"C10S3-filter-tuple",
 ("rag-blueprint/eval/train_logistic_regression.py::perform_cross_validation","a"):"C1S5-describe-stats",
 ("feed-split.py::what_language","a"):"C1S4-what-language",
 ("visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.should_filter_token","a"):"C8S2-filter-compiled",
 ("text-search/python/extract-msmarco.py::extract_documents","a"):"C9S1-extract-offset",
 ("examples/embedder-auto-training-evaluation/training-evaluation/train.py::TrainDataset.__init__","a"):"C6S3-init-iterate",
 ("news/src/python/train_cold_start.py::read_bert_embeddings","a"):"C5S3-bert-float32",
 ("news/src/python/mind_data.py::MindData.add_impressions","b"):"C1S4-impression-lookup",
 ("examples/workshop-ecommerce/preprocess.py::process_users","b"):"C3S1-users-records",
}
BLOCK = {
 ("multilingual-search/ext/evaluate.py::search","a"):"inputs.py: it cannot run here: `search` performs an HTTP POST to `args.endpoint` via `requests.Session`, requiring a live Vespa endpoint; no input can avoid the network request.",
 ("text-search/python/collect_training_data.py::build_dataset","a"):"inputs.py: it cannot run here: `build_dataset` calls `get_features`, which performs `requests.post(url, json=body)` against a Vespa server; every measured call would need network access to a live search endpoint, which is unavailable here.",
 ("text-search/python/collect_training_data.py::build_dataset","b"):"inputs.py: it cannot run here: `build_dataset` calls `get_features`, which performs `requests.post(url, json=body)` against a Vespa server; every measured call would need network access to a live search endpoint, which is unavailable here.",
 ("examples/embedder-auto-training-evaluation/training-evaluation/train.py::TrainDataset.__getitem__","a"):"inputs.py: every call of `TrainDataset.__getitem__` returns a `sentence_transformers.InputExample`, which needs the sentence_transformers package; not installed in this venv, and its install was not attempted in this run.",
 ("examples/in-context-learning/categorize_group.py::inference","a"):"inputs.py: `inference` performs an HTTP POST to a Vespa server at http://localhost:8080/search/, which needs a running Vespa instance and network access that is not available here.",
 ("news/src/python/create_bert_embeddings.py::create_embeddings","a"):"inputs.py: `create_embeddings` calls BertTokenizer/BertModel.from_pretrained, which download weights from the HuggingFace Hub over the network; no local model directory is available.",
 ("news/src/python/create_bert_embeddings.py::create_embeddings","b"):"inputs.py: `create_embeddings` calls BertTokenizer/BertModel.from_pretrained, which download weights from the HuggingFace Hub over the network; no local model directory is available.",
 ("news/src/python/create_bert_embeddings.py::create_embeddings","c"):"inputs.py: `create_embeddings` calls BertTokenizer/BertModel.from_pretrained, which download weights from the HuggingFace Hub over the network; no local model directory is available.",
 ("news/src/python/create_bert_embeddings.py::create_embeddings","d"):"inputs.py: `create_embeddings` calls BertTokenizer/BertModel.from_pretrained, which download weights from the HuggingFace Hub over the network; no local model directory is available.",
 ("news/src/python/create_bert_embeddings.py::create_embeddings","e"):"inputs.py: `create_embeddings` calls BertTokenizer/BertModel.from_pretrained, which download weights from the HuggingFace Hub over the network; no local model directory is available.",
 ("visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator._prepare_similarity_map_tensor","a"):"inputs.py: the unit's module does not load here: AttributeError: SimMapGenerator is not defined here: loading the module skipped line 19 `class SimMapGenerator:` (TypeError), with stand-ins for colpali_engine.",
 ("visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.gen_similarity_maps","a"):"inputs.py: the unit's module does not load here: AttributeError: SimMapGenerator is not defined here: loading the module skipped line 19 `class SimMapGenerator:` (TypeError), with stand-ins for colpali_engine.",
 ("visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.gen_similarity_maps","b"):"inputs.py: the unit's module does not load here: AttributeError: SimMapGenerator is not defined here: loading the module skipped line 19 `class SimMapGenerator:` (TypeError), with stand-ins for colpali_engine.",
 ("visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.gen_similarity_maps","c"):"inputs.py: the unit's module does not load here: AttributeError: SimMapGenerator is not defined here: loading the module skipped line 19 `class SimMapGenerator:` (TypeError), with stand-ins for colpali_engine.",
 ("visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator._prepare_similarity_map_tensor","a"):"inputs.py: the unit's module does not load here: AttributeError: SimMapGenerator is not defined here: loading the module skipped line 19 `class SimMapGenerator:` (TypeError), with stand-ins for colpali_engine.",
}
out = []
for rec in step2:
    outs = []
    for d in rec["decisions"]:
        key = (rec["unit"], d["label"])
        if d["verdict"] == "rejected":
            continue
        if key in SUB:
            sid = SUB[key]
            if sid == "C8S2-filter-compiled":
                outs.append({"label": d["label"], "outcome": "blocked", "submission": None,
                             "why": "verify.py: no_inputs: no inputs could be generated for visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.should_filter_token: the unit's module does not load here: AttributeError: SimMapGenerator is not defined here (line 19 class statement skipped, TypeError, with stand-ins for colpali_engine). The line stays in submissions.jsonl, unmeasured."})
            elif sid == "C1S5-describe-stats":
                outs.append({"label": d["label"], "outcome": "blocked", "submission": None,
                             "why": "verify.py: not_equivalent on 'empty-file': before raised KeyError, after raised ValueError. The original raises KeyError('mean') on a header-only file whose feature column is non-numeric, and the describe-free repair cannot reproduce that exception. The line stays in submissions.jsonl, not counted as measured."})
            else:
                outs.append({"label": d["label"], "outcome": "submitted", "submission": sid, "why": None})
        elif key in BLOCK:
            outs.append({"label": d["label"], "outcome": "blocked", "submission": None, "why": BLOCK[key]})
        else:
            outs.append({"label": d["label"], "outcome": "deferred", "submission": None,
                         "why": "accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold."})
    if outs:
        out.append({"step": 3, "unit": rec["unit"], "outcomes": outs})
with open(f"{R}/step3.jsonl", "w") as f:
    for r in out: f.write(json.dumps(r, ensure_ascii=False) + "\n")
print("step3 units:", len(out))
