import json
U = []
def unit(name, sus):
    U.append({"step": 1, "unit": name, "suspicions": [
        {"label": l, "root_cause": rc, "lines": lines, "why": why} for (l, rc, lines, why) in sus]})

unit("incremental-search/search-suggestions/count_terms.py::process_docs", [
 ("a", "C3.S4", [100,101,102,103], "each unique term scans every per-document count dict with `term in doc` in a list comprehension (lines 100-103), so cost is terms x docs; the doc count could be incremented once per (doc, term) pair inside the loop at lines 93-97"),
 ("b", "C1.S1", [92], "`total_count = sum([...])` is computed for every document and never read")])
unit("incremental-search/search-suggestions/count_terms.py::count_terms", [
 ("a", "C10.S1", [59,60,61], "`not any(map(lambda word: word in common_words, window))` builds a lambda and a map object per window; `common_words.isdisjoint(window)` answers the same question in one C call"),
 ("b", "C1.S4", [60,62], "the window slice `doc[i : i + win_len]` is built twice per iteration, once at line 60 and again at line 62")])
unit("incremental-search/search-suggestions/count_terms.py::write_json_file", [
 ("a", "C10.S2", [27], "`re.sub(r\" \", \"/\", term)` runs once per term; `term.replace(\" \", \"/\")` gives the same string without the regex machinery")])
unit("incremental-search/search-suggestions/accepted_words.py::process_docs", [
 ("a", "C10.S3", [29,30,31,32], "`term_set.add(term)` is called once per term in two loops; one `update` per clean_text result does the same work in one call")])
unit("incremental-search/search-suggestions/accepted_words.py::write_to_file", [
 ("a", "C10.S3", [41,42], "`f.write(term+\"\\n\")` makes one Python-level write call per term over the whole vocabulary")])
unit("news/src/python/train_cold_start.py::read_bert_embeddings", [
 ("a", "C5.S3", [164,167], "`np.zeros([n, 512])` is float64, twice the size needed; the values are then cast to float32 by `torch.FloatTensor` on line 167")])
unit("news/src/python/train_cold_start.py::read_bert_embeddings_from_file", [
 ("a", "C8.S3", [180,183], "`data_loader.news()` is called on every line of the embeddings file, twice per line, for a map that does not change during the read")])
unit("news/src/python/train_cold_start.py::train_epoch", [
 ("a", "C6.S4", [99], "`total_loss += loss` adds a tensor that still carries its autograd graph, so activations of every batch stay alive until the epoch ends; `loss.item()` keeps only the scalar")])
unit("news/src/python/evaluate.py::read_impressions_file", [
 ("a", "C3.S6", [35,42,46], "every row of the impressions file is parsed into dicts and appended, then `calc_metrics` line 86 keeps `sample_size` rows with `random.sample`; only the sampled rows need parsing")])
unit("news/src/python/evaluate.py::find_hit", [
 ("a", "C3.S4", [56,57], "for each candidate news id, `predictions` calls this, which scans every hit child linearly, so one impression costs about len(news_ids) x len(children) comparisons")])
unit("news/src/python/metrics.py::ndcg_score", [
 ("a", "C8.S1", [28], "the ideal DCG `dcg_score(y_true, y_true, k)` is recomputed on every call, and callers evaluate k=5 and k=10 over the same label groups")])
unit("news/src/python/mind_data.py::MindData.read_data", [
 ("a", "C1.S5", [93,101], "`datetime.strptime` runs on every impression line and its result is stored under 'timestamp'; no reader of that key was found in news/src/python"),
 ("b", "C2.S1", [100], "`self.lookup_user_index` is a one-line wrapper around `lookup_index`, called once per impression line on the loader's hot path")])
unit("news/src/python/mind_data.py::MindData.read_news", [
 ("a", "C3.S5", [65,66,73], "every title and abstract entity is walked by add_entities, then line 73 keeps only the first two `entity_ids`; the walk could stop after two unique ids")])
unit("news/src/python/mind_data.py::MindData.sample_valid_data", [
 ("a", "C8.S2", [159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179], "the validation sample is rebuilt on every call with probability 1.0, so the same result is recomputed each epoch")])
unit("text-video-search/src/python/embedding.py::sample_images", [
 ("a", "C6.S2", [34], "`np.array(images)[idx]` copies every decoded frame into a new array and then keeps only the sampled indices")])
unit("text-video-search/src/python/embedding.py::extract_images", [
 ("a", "C6.S3", [50,51], "every decoded frame is appended to a list, then `sample_images` keeps `number_frames` of them")])
unit("colbert-long/scripts/convert.py::remove_control_characters", [
 ("a", "C10.S1", [7], "a generator calls `unicodedata.category(ch)` for every character of every chunk; a translate table built once does the removal in C")])
unit("feed-split.py::split_text", [
 ("a", "C10.S4", [97], "`text = text + \"\\n\" + line` copies the accumulated section once per markdown line")])
unit("text-search/python/extract-msmarco.py::extract_documents", [
 ("a", "C9.S1", [85], "`out.tell()` runs once per document on a text file; on a TextIOWrapper that flushes the buffer, so each document forces a write")])
unit("text-search/python/convert-to-vespa-format.py::main", [
 ("a", "C10.S2", [62], "`json.dump(doc, out)` issues one `write` per encoded chunk; `out.write(json.dumps(doc))` makes one call per document")])
unit("text-search/python/sample-queries-and-documents.py::select_documents", [
 ("a", "C3.S2", [61], "`min(len(docids), documents_to_generate)` is recomputed on every iteration of the while loop, and its value never changes")])
unit("text-search/python/collect_training_data.py::build_dataset", [
 ("a", "C5.S1", [75], "`processed_queries` is a list, so `int(qid) not in processed_queries` scans it for every query"),
 ("b", "C9.S1", [98,99], "the processed-queries file is opened in append mode and written once per query, including queries already processed")])
unit("rag-blueprint/eval/train_lightgbm.py::perform_cross_validation", [
 ("a", "C1.S5", [188], "`valid_sets` includes `lgb_train`, so LightGBM computes the training AUC on every boosting round"),
 ("b", "C8.S2", [151,152,153,154,155,156,257,258,259], "a new lgb.Dataset is built from pandas and binned for every fold and again for the final model")])
unit("visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.float_to_binary_embedding", [
 ("a", "C10.S3", [168,169,170], "`np.where(x > 0, 1, 0)` builds an int64 array per vector before `np.packbits`; `np.packbits` accepts the boolean array directly")])
unit("visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.gen_similarity_maps", [
 ("a", "C6.S2", [85,86,87], "each image is fully decoded to RGB and copied only so its `.size` can be read; `processed_images` is never read and `_blend_image` does not use `img`"),
 ("b", "C3.S2", [99], "`self.should_filter_token(token)` depends only on the token but is evaluated for every (image, token) pair")])
unit("visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator._prepare_similarity_map_tensor", [
 ("a", "C3.S2", [147,148,149,150], "the `hasattr(self.processor, 'image_seq_length')` test and its lookup are repeated for every cell although the processor does not change inside the loop"),
 ("b", "C10.S3", [154,155,156,157,158,159], "the tensor is filled one scalar index assignment per cell")])
unit("visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.should_filter_token", [
 ("a", "C8.S2", [253], "`re.compile` runs on every call; the pattern is a constant")])
unit("visual-retrieval-colpali/prepare_feed_deploy.py::float_to_binary_embedding", [
 ("a", "C10.S3", [585,586,587,588,589,590,591,592], "one np.array, np.where, packbits and tolist chain per patch vector, roughly 1000 vectors per page")])
unit("visual-retrieval-colpali/prepare_feed_deploy.py::generate_embeddings", [
 ("a", "C10.S3", [555,556,557,558,559,560,561,562,563,564,565,566,567,568], "the DataLoader is built without `batch_size`, so the model runs one page per forward pass and the batch_size parameter is ignored")])
unit("examples/workshop-ecommerce/preprocess.py::process_products", [
 ("a", "C3.S1", [152,153,154,155,156,157,158,159,160,161,162], "`df_merged.iterrows()` builds a pandas Series for every row to read a few values that a dict per row would give")])
unit("examples/workshop-ecommerce/preprocess.py::process_users", [
 ("a", "C3.S1", [202,203,204,205,206,207,208,209], "`user_purchases_df.iterrows()` builds a Series for every purchase row of every user"),
 ("b", "C3.S6", [181,182,183,184,185,186,187,188], "in sample mode (default limit 10) the whole order_products table is merged with orders and grouped, although only the first `limit` users are written")])
unit("examples/workshop-ecommerce/preprocess.py::process_orders", [
 ("a", "C8.S4", [235], "`orders.csv` is read again here, although process_users already read the same file")])
unit("examples/ecommerce-user-preferences/webapp/app.py::get_wikipedia_image", [
 ("a", "C8.S1", [103,127,211,212,213,214], "a make and model with no usable image is looked up on Wikipedia again on every call, because only successful results are written to IMAGE_CACHE"),
 ("b", "C9.S1", [146,147,148,149,150,151,152,179,180,181,182,183,184,185], "one imageinfo request is sent per candidate title, one at a time, inside a request handler")])
unit("examples/ecommerce-user-preferences/webapp/app.py::load_system_prompt", [
 ("a", "C8.S2", [48], "system_prompt.txt is reopened and read on every chat turn although the content never changes")])
unit("examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::subgraph_GenerateKeywords", [
 ("a", "C8.S2", [48,52], "a ChatOpenAI client and the chain are built on every node call with the same fixed configuration")])
unit("examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::subgraph_EvaluateCategory", [
 ("a", "C8.S2", [99,103], "a ChatOpenAI client and the chain are built on every node call with the same fixed configuration")])
unit("examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::subgraph_EvaluateFilters", [
 ("a", "C8.S2", [149,153], "a ChatOpenAI client and the chain are built on every node call with the same fixed configuration")])
unit("examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::EvaluateResults", [
 ("a", "C8.S2", [197,201], "a ChatOpenAI client and the chain are built on every node call with the same fixed configuration")])
unit("examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/vespa_module/vespa_retriever.py::VespaRetriever", [
 ("a", "C8.S2", [67], "a new Vespa client is constructed on every retrieval call")])
unit("examples/agentic-streamlit-chatbot/simple_app/streamlit_vespa_app.py::VespaRetriever", [
 ("a", "C8.S2", [50,51,52], "a new Vespa client is constructed inside the tool body on every call")])
unit("examples/google-cloud/cloud-functions/python/main.py::getlogs", [
 ("a", "C4.S8", [61,63,69], "`blob.name.__contains__(...)` and `json_data['uri'].__contains__(...)` call the dunder method directly where the `in` operator is the idiom; line 69 runs once per decompressed log record")])
unit("examples/google-cloud/cloud-functions/python/main.py::get_blobs", [
 ("a", "C8.S2", [88], "a new storage.Client() is built on every HTTP request")])
unit("examples/in-context-learning/categorize_group.py::inference", [
 ("a", "C1.S1", [128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,194,195,196,197,198,199,200,201,202,203,204,205,206,207,208,209], "nine of the ten request dictionaries built here are never read; only the bm25_no_group_10 request is sent"),
 ("b", "C8.S2", [211], "`requests.post` is called without a Session, so each query opens a new connection")])
unit("examples/embedder-auto-training-evaluation/training-evaluation/positives-negatives.py::search", [
 ("a", "C4.S7", [22,23,24,25], "the Vespa POST runs even when `qrels.get(query_id, [])` is empty; the function then returns without writing anything, so a guard before the request would skip it")])
unit("examples/model-exporting/export_hf_model_from_hf.py::export_model", [
 ("a", "C1.S5", [43,44,45,46,47,48,49], "tokenizer.save_pretrained writes every tokenizer file and the loop then deletes all except tokenizer.json")])
unit("examples/model-exporting/export_model_from_hf.py::export_model", [
 ("a", "C1.S5", [42,43,44,45,46,47,48], "tokenizer.save_pretrained writes every tokenizer file and the loop then deletes all except vocab.txt")])
unit("news/src/python/create_bert_embeddings.py::create_embeddings", [
 ("a", "C10.S3", [51,52,53,54,55,56,57,58,59], "one document goes through BERT per forward pass; a padded batch would replace the per-row loop"),
 ("b", "C1.S5", [58], "the forward pass runs without torch.no_grad() or inference_mode(), so autograd builds a graph nobody uses"),
 ("c", "C5.S4", [59], "`outputs[0].tolist()[0][0]` converts the whole 1 x seq x 512 hidden state to nested Python lists to keep one 512-vector"),
 ("d", "C8.S2", [47,48], "the tokenizer and BERT model are loaded again for each call, and main calls create_embeddings once per split"),
 ("e", "C1.S1", [30,31,41,42], "`categories` and `subcategories` are filled for every row and never read")])
unit("news/src/python/vespa_client.py::query_news", [
 ("a", "C9.S1", [67], "requests.post runs without a Session, so every call opens a new connection and mTLS handshake")])
unit("news/src/python/vespa_client.py::query_user_embedding", [
 ("a", "C9.S1", [48], "requests.get runs without a Session, so every call opens a new connection and mTLS handshake")])
unit("news/src/python/evaluate.py::calc_impression", [
 ("a", "C8.S4", [73], "query_user_embedding runs once per impression with no cache by user_id, so repeated users fetch the same vector again")])
unit("rag-blueprint/eval/collect_pyvespa.py::feature_collection_second_phase_query_fn", [
 ("a", "C8.S1", [49,50], "embed() is called twice on the same text, once for query(embedding) and once for query(float_embedding)")])
unit("rag-blueprint/eval/collect_pyvespa.py::feature_collection_first_phase_query_fn", [
 ("a", "C8.S1", [95,96], "embed() is called twice on the same text for query(embedding) and query(float_embedding)")])
unit("rag-blueprint/eval/evaluate_ranking.py::rank_first_phase_query_fn", [
 ("a", "C8.S1", [55,56], "embed() is called twice on the same text for query(embedding) and query(float_embedding)")])
unit("rag-blueprint/eval/evaluate_ranking.py::rank_second_phase_query_fn", [
 ("a", "C8.S1", [85,86], "embed() is called twice on the same text for query(embedding) and query(float_embedding)")])
unit("rag-blueprint/eval/evaluate_match_phase.py::match_weakand_query_fn", [
 ("a", "C1.S5", [18], "the weakAnd query carries no nearestNeighbor term, yet the match-only profile declares query(embedding), so an embedding may be computed and never consumed")])
unit("text-video-search/src/python/embedding.py::VideoFeedDataset.__getitem__", [
 ("a", "C10.S3", [97,98,99], "each frame gets its own CLIP encode_image call on a batch of one, inside the loop"),
 ("b", "C3.S2", [100,103], "`ntpath.basename(video_file_name)` and `split('.mp4')` are recomputed for every frame although they depend only on the video")])
unit("text-video-search/src/python/embedding.py::TextProcessor.embed", [
 ("a", "C8.S1", [186], "the same query string is run through the CLIP text encoder again on every call, and nothing memoizes it")])
unit("text-video-search/src/python/embedding.py::TextProcessor.__init__", [
 ("a", "C6.S4", [174], "`self.model, _ = clip.load(model_name)` keeps the visual tower alive for the process lifetime, but embed() only calls encode_text")])
unit("text-video-search/src/python/app.py::get_predefined_queries", [
 ("a", "C8.S4", [34,35], "Streamlit reruns the script on each widget change, and each rerun re-reads predefined_queries.txt over HTTP with no cache")])
unit("incremental-search/search-as-you-type/feed_to_vespa.py::vespa_feed", [
 ("a", "C9.S1", [83,84,85,86], "one `curl` subprocess per document (fork, exec, new TLS connection), where one bulk feed would do")])
unit("incremental-search/search-as-you-type/feed_to_vespa.py::update_endpoint", [
 ("a", "C8.S4", [149,167], "the same feed JSON is parsed twice, once for the ids and again inside vespa_feed")])
unit("feed_to_vespa.py::vespa_remove", [
 ("a", "C9.S1", [64,65,66,67,68], "one HTTP DELETE per stale document id, each followed by a JSON parse")])
unit("feed_to_vespa.py::update_endpoint", [
 ("a", "C1.S6", [153,154], "get_indexed_docids pages through the whole index unconditionally, and its result is used only if do_remove_index or do_feed is set")])
unit("colbert/model2onnx.py::VespaColBERT.__init__", [
 ("a", "C1.S6", [16,17,18], "AutoModel.from_config builds a randomly initialised BERT, init_weights re-randomises it, and from_pretrained then overwrites it with the checkpoint")])
unit("reverse-image-search/script/feed.py::run", [
 ("a", "C1.S5", [136,140], "`ex['image']` is read and decoded before the skip test, so a resumed run decodes every image it then discards"),
 ("b", "C8.S4", [152,153], "a JPEG just written by _save_image is read back from disk and decoded again for base64"),
 ("c", "C11.S5", [180,181,182,183,184,185,186,187], "feed_iterable blocks the loop, so image I/O and inference of the next batch wait for the network")])
unit("hypencoder/encode_query.py::main", [
 ("a", "C5.S4", [70,71,72], "`np.array(enc.ids, dtype=np.float32).tolist()` converts small ints through a numpy array to get floats")])
unit("commerce-product-ranking/scripts/evaluate.py::main", [
 ("a", "C9.S2", [52], "`pd.read_parquet` loads every column, but the script uses six"),
 ("b", "C1.S4", [75,76], "`set_index('query_id')` is called twice on the same frame")])
unit("colbert-long/scripts/evaluate.py::main", [
 ("a", "C11.S5", [93,94], "queries run one at a time, each waiting on a network round trip")])
unit("multilingual-search/ext/evaluate.py::search", [
 ("a", "C10.S2", [12,13], "`query_group.iterrows()` builds a Series per row only to read one value; `query_group['query'].iloc[0]` gives it directly")])
unit("visual-retrieval-colpali/src/main.py::get_and_store_sim_maps", [
 ("a", "C8.S4", [263,264,265,266,267,268], "the same query, embeddings and base ranking are sent to Vespa a second time per search, once for the results and again for the sim maps")])
unit("visual-retrieval-colpali/src/main.py::message_generator", [
 ("a", "C8.S2", [368,369,370,371,372,373,374,375,376,377,378,379,380], "each 0.2 s poll resets images and reopens every image already on disk, although ready files stay ready"),
 ("b", "C1.S2", [403], "the replace over the whole accumulated response runs on every chunk; after the first pass there is no newline left, so it is an identity call")])
unit("visual-retrieval-colpali/src/main.py::full_image", [
 ("a", "C8.S2", [334,335,336], "a cached image is read from disk and base64-encoded again on every request")])
unit("visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.query_vespa_bm25", [
 ("a", "C9.S2", [130,142], "every BM25 query sends the full float embedding as input.query(qt); the bm25 profile's first phase never reads it")])
unit("visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.get_suggestions", [
 ("a", "C8.S1", [336,364], "every keystroke sends a fetch with leading and trailing wildcard matches, and nothing caches the result")])
unit("news/src/python/convert_embeddings_to_vespa_format.py::read_embeddings", [
 ("a", "C5.S4", [27,28], "each value goes from text to float32 and then back to text with '%.6f' in the writers")])
unit("news/src/python/train_mf.py::main", [
 ("a", "C1.S4", [145,146], "the final evaluation repeats the one already run at the last epoch on the same weights")])
unit("news/src/python/train_cold_start.py::train_model", [
 ("a", "C1.S5", [116,117,118,119,120], "every epoch runs a full train eval and a full valid eval and rewrites the embedding files, and nothing reads those files back during training")])
unit("visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.format_query_results", [
 ("a", "C1.S5", [100,101,102,103,104], "three values are computed only for a debug string, and the hits parameter is unused")])
unit("visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.get_result_from_query", [
 ("a", "C1.S5", [256,257], "a loop logs each child's keys at debug level on every search")])


unit("news/src/python/mind_data.py::MindData.add_impressions", [
 ("a", "C1.S5", [189,190,191,198,199,200], "category, subcategory and entity indices are looked up and appended for every positive and negative sample; train_mf.py discards them, though train_cold_start.py reads them")])
unit("use-case-shopping/create_suggestions.py::filter_content", [
 ("a", "C10.S1", [68,69,70], "a Python loop over eight invalid prefixes calls startswith for each noun chunk; `text.startswith(tuple(invalid_starts))` is one call")])
with open("/home/javad/energy-run/sample-apps/step1.jsonl", "w") as f:
    for u in U:
        f.write(json.dumps(u, ensure_ascii=False) + "\n")
print(len(U), "units")
