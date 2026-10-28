import json
ROOT = "/home/javad/energy-run/sample-apps/"
s2 = [json.loads(l) for l in open(ROOT + "step2.jsonl")]
subs = {}
for l in open(ROOT + "submissions.jsonl"):
    s = json.loads(l); subs[s["unit"]] = s["id"]
C = "/".join  # noqa
P = "incremental-search/search-suggestions/count_terms.py::"
A = "incremental-search/search-suggestions/accepted_words.py::"
W = "examples/workshop-ecommerce/preprocess.py::"
V = "visual-retrieval-colpali/"
SUB = {
 (P+"process_docs","a"): "C3S4-process-docs-docs-in-loop",
 (P+"process_docs","b"): "C1S1-process-docs-dead-total",
 (P+"count_terms","a"): "C10S1-count-terms-isdisjoint",
 (P+"count_terms","b"): "C1S4-count-terms-window-once",
 (P+"write_json_file","a"): "C10S2-write-json-replace",
 (A+"process_docs","a"): "C10S3-accepted-process-update",
 (A+"write_to_file","a"): "C10S3-accepted-write-join",
 ("news/src/python/train_cold_start.py::read_bert_embeddings","a"): "C5S3-bert-float32-buffer",
 ("news/src/python/mind_data.py::MindData.read_data","a"): "C1S5-read-data-no-timestamp",
 ("text-video-search/src/python/embedding.py::sample_images","a"): "C6S2-sample-images-copy-kept",
 ("colbert-long/scripts/convert.py::remove_control_characters","a"): "C10S1-remove-control-fast-path",
 ("feed-split.py::split_text","a"): "C10S4-split-text-parts-list",
 ("text-search/python/extract-msmarco.py::extract_documents","a"): "C9S1-extract-docs-running-offset",
 ("text-search/python/convert-to-vespa-format.py::main","a"): "C10S2-convert-main-one-write",
 ("text-search/python/sample-queries-and-documents.py::select_documents","a"): "C3S2-select-documents-min-hoist",
 (W+"process_products","a"): "C3S1-products-records",
 (W+"process_users","a"): "C3S1-users-purchases-records",
 (W+"process_orders","b"): "C3S1-orders-records-new",
 (V+"prepare_feed_deploy.py::float_to_binary_embedding","a"): "C10S3-prepare-binary-packbits-bool",
 (V+"src/backend/vespa_app.py::VespaQueryClient.float_to_binary_embedding","a"): "C10S3-vespa-binary-packbits-bool",
}
NET = ("it cannot run here: network access is required, and no input can avoid it")
BLK = {
 "rag-blueprint/eval/collect_pyvespa.py::feature_collection_second_phase_query_fn": "the repair cannot be made to behave identically: the returned query body has two keys, input.query(embedding) and input.query(float_embedding), both embed(text); removing either key changes the returned dict, and sharing one embed value would change it too. Inputs were generated (ready), but no repair could keep the return value equal, so none was submitted.",
 "visual-retrieval-colpali/src/main.py::full_image": "the inputs that run here reach only 0% of the function (lines 327-329, 331-333, 335-337 never ran), so they would not measure its real work",
 "visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator._prepare_similarity_map_tensor": "the unit's module does not load here: AttributeError: SimMapGenerator is not defined here: loading the module skipped line 19 `class SimMapGenerator:` (TypeError), with stand-ins for colpali_engine",
 "visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.gen_similarity_maps": "it cannot run here: constructing `SimMapGenerator` loads the ColPali model from the HuggingFace hub (network access) as the repository's own caller does at startup, and the internal structure of the Vespa similarity maps consumed by the elided `_prepare_similarity_map_tensor` is not specified, so no valid input can be built.",
 "visual-retrieval-colpali/prepare_feed_deploy.py::generate_embeddings": "it cannot run here: `generate_embeddings` requires a pretrained ColPali model and processor from `ColPali.from_pretrained(MODEL_NAME)`, which needs network access to Hugging Face; the inputs.py generator reported this and no input can avoid it.",
 "text-search/python/collect_training_data.py::build_dataset": "it cannot run here: `build_dataset` calls `get_features`, which issues `requests.post` to a Solr server at http://localhost:8080/search/; no input can avoid the network request.",
 "news/src/python/create_bert_embeddings.py::create_embeddings": "it cannot run here: `create_embeddings` calls `BertTokenizer.from_pretrained('bert-base-uncased')` and `BertModel.from_pretrained('google/bert_uncased_L-8_H-512_A-8')`, which download pretrained models from the Hugging Face Hub and need network access.",
 "news/src/python/vespa_client.py::query_news": "it cannot run here: `query_news` performs `requests.post` to a Vespa search server; no input can avoid the network request.",
 "news/src/python/vespa_client.py::query_user_embedding": "it cannot run here: `query_user_embedding` performs a live `requests.get` to a Vespa search endpoint; no input can avoid the network request.",
 "text-video-search/src/python/embedding.py::TextProcessor.embed": "it cannot run here: `TextProcessor.embed` needs the CLIP model from `clip.load(\"ViT-B/32\")`, which downloads weights from the network; the `clip` package is not installed.",
 "text-video-search/src/python/embedding.py::VideoFeedDataset.__getitem__": "it cannot run here: the class's `__init__` loads the CLIP model via `clip.load(model_name)`, which downloads model weights from a remote server.",
 "examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::subgraph_GenerateKeywords": "it cannot run here: the node builds a `ChatOpenAI` model and invokes the chain, a network request to the OpenAI API; no input can avoid that.",
 "examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::subgraph_EvaluateCategory": "it cannot run here: the node builds a `ChatOpenAI` chain and invokes it, a request to the OpenAI API.",
 "examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::subgraph_EvaluateFilters": "it cannot run here: the node builds a `ChatOpenAI` model and invokes the chain, a request to the OpenAI API.",
 "examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::EvaluateResults": "it cannot run here: the node builds a `ChatOpenAI` model and invokes the chain, a request to the OpenAI API.",
 "examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/vespa_module/vespa_retriever.py::VespaRetriever": "it cannot run here: the node builds a `Vespa` client and queries a server at `VESPA_URL`, which needs network access and live credentials.",
 "examples/google-cloud/cloud-functions/python/main.py::get_blobs": "it cannot run here: get_blobs calls google.cloud.storage.Client() and list_blobs(bucket), an authenticated network request to Google Cloud Storage.",
 "examples/in-context-learning/categorize_group.py::inference": "it cannot run here: inference posts to http://localhost:8080/search/, which needs a running Vespa server.",
 "feed_to_vespa.py::vespa_remove": "it cannot run here: `vespa_delete` makes a live HTTP request for every document id, to a Vespa endpoint.",
 "incremental-search/search-as-you-type/feed_to_vespa.py::vespa_feed": "it cannot run here: `vespa_feed` posts every document to a Vespa endpoint through curl, a network request.",
}
DEF = {
 (V+"prepare_feed_deploy.py::float_to_binary_embedding","b"):None,
}
DEFER_WHY = {
 "news/src/python/mind_data.py::MindData.read_data": "accepted; the second part (lookup wrapper, line 100) is small and the 20 measurement places went to higher-expected repairs; not measured",
 W+"process_users": "accepted; the purchase-group filter before the merge is more code than the other repairs and was not measured; the 20 places were used",
 "news/src/python/train_cold_start.py::read_bert_embeddings_from_file": "accepted; its inputs are ready, but the 20 measurement places went to higher-expected repairs; not measured",
 "examples/ecommerce-user-preferences/webapp/app.py::get_wikipedia_image": "accepted; the batched imageinfo request needs Wikipedia, which cannot be reached here, and it was not requested",
 "examples/agentic-streamlit-chatbot/simple_app/streamlit_vespa_app.py::VespaRetriever": "accepted; it needs Vespa, and it was not requested because the 30-unit holding limit was reached",
 "news/src/python/evaluate.py::calc_impression": "accepted; it needs Vespa, and it was not requested because the 30-unit holding limit was reached",
 "rag-blueprint/eval/collect_pyvespa.py::feature_collection_first_phase_query_fn": "accepted; it needs Vespa, and it was not requested because the 30-unit holding limit was reached",
 "rag-blueprint/eval/evaluate_ranking.py::rank_first_phase_query_fn": "accepted; it needs Vespa, and it was not requested because the 30-unit holding limit was reached",
 "rag-blueprint/eval/evaluate_ranking.py::rank_second_phase_query_fn": "accepted; it needs Vespa, and it was not requested because the 30-unit holding limit was reached",
 "text-video-search/src/python/app.py::get_predefined_queries": "accepted; it fetches a remote URL, and it was not requested because the 30-unit holding limit was reached",
 "incremental-search/search-as-you-type/feed_to_vespa.py::update_endpoint": "accepted; it needs a Vespa endpoint, and it was not requested because the 30-unit holding limit was reached",
 "feed_to_vespa.py::update_endpoint": "accepted; it needs a Vespa endpoint, and it was not requested because the 30-unit holding limit was reached",
 "reverse-image-search/script/feed.py::run": "accepted; it needs a dataset download and a Vespa endpoint, and it was not requested because the 30-unit holding limit was reached",
 "examples/in-context-learning/categorize_group.py::inference": None,
 "commerce-product-ranking/scripts/evaluate.py::main": "accepted; it needs a Vespa endpoint and a parquet file not in the repository, and it was not requested because the 30-unit holding limit was reached",
 "colbert-long/scripts/evaluate.py::main": "accepted; it needs a Vespa endpoint, and it was not requested because the 30-unit holding limit was reached",
 "multilingual-search/ext/evaluate.py::search": "accepted; it needs a Vespa endpoint, and it was not requested because the 30-unit holding limit was reached",
 "visual-retrieval-colpali/src/main.py::get_and_store_sim_maps": "accepted; it needs Vespa, and it was not requested because the 30-unit holding limit was reached",
 "visual-retrieval-colpali/src/main.py::message_generator": "accepted; it calls the Gemini client after its wait loop, and it was not requested because the 30-unit holding limit was reached",
 "visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.query_vespa_bm25": "accepted; it needs Vespa, and it was not requested because the 30-unit holding limit was reached",
 "visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.get_suggestions": "accepted; it needs Vespa, and it was not requested because the 30-unit holding limit was reached",
}
out = []
missing = []
for r in s2:
    unit = r["unit"]
    outs = []
    for d in r["decisions"]:
        if d["verdict"] != "accepted":
            continue
        lab = d["label"]
        key = (unit, lab)
        if key in SUB:
            outs.append({"label": lab, "outcome": "submitted", "submission": SUB[key], "why": None})
        elif unit in BLK:
            outs.append({"label": lab, "outcome": "blocked", "submission": None, "why": BLK[unit]})
        elif unit in DEFER_WHY and DEFER_WHY[unit]:
            outs.append({"label": lab, "outcome": "deferred", "submission": None, "why": DEFER_WHY[unit]})
        elif unit == W+"process_users" and lab == "b":
            outs.append({"label": lab, "outcome": "deferred", "submission": None, "why": DEFER_WHY[W+"process_users"]})
        elif unit == "news/src/python/mind_data.py::MindData.read_data" and lab == "b":
            outs.append({"label": lab, "outcome": "deferred", "submission": None, "why": DEFER_WHY[unit]})
        else:
            missing.append((unit, lab))
    if outs:
        out.append({"step": 3, "unit": unit, "outcomes": outs})
if missing:
    print("UNMAPPED:", missing)
with open(ROOT + "step3.jsonl", "w") as f:
    for r in out:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
from collections import Counter
print(len(out), "unit records")
print(Counter(o["outcome"] for r in out for o in r["outcomes"]))
