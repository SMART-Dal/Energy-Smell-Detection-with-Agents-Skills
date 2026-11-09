import json
U = []
def unit(u, *sus):
    U.append({"step": 1, "unit": u, "suspicions": [
        {"label": chr(ord("a") + i), "root_cause": rc, "lines": lines, "why": why}
        for i, (rc, lines, why) in enumerate(sus)]})

unit("feed-split.py::split_text",
     ("C10.S4", [97], "`text = text + \"\\n\" + line` copies the whole accumulated section text on every markdown line; the left operand is still referenced by `text`, so CPython cannot append in place and each section costs quadratic copying"))
unit("feed-split.py::what_language",
     ("C1.S4", [20, 24, 26], "`el.text` (a full get_text() walk of the code block) is evaluated up to three times for one `el`"))
unit("colbert-long/scripts/convert.py::remove_control_characters",
     ("C10.S1", [7], "per-character generator calling `unicodedata.category(ch)[0]` over every character of every chunk, where a C-level table translate would do the same filtering"))
unit("use-case-shopping/create_suggestions.py::filter_content",
     ("C10.S3", [68, 69], "`for f in invalid_starts: if text.startswith(f)` makes one method call per prefix; a single `startswith` with a tuple does the same test in one call"))
unit("use-case-shopping/create_suggestions.py::filter",
     ("C4.S2", [60, 61], "`len(text) < 3` already returned True at line 58, so `text.startswith(\"/\") and len(text) < 3` on line 60 can never be true"))
unit("use-case-shopping/convert_meta.py::main",
     ("C10.S2", [67], "`json.dumps(output_data, indent=2)` uses the pure-Python encoder path; dropping indent would enable the C encoder"))
unit("use-case-shopping/convert_reviews.py::main",
     ("C10.S2", [58], "`json.dumps(output_data, indent=2)` uses the pure-Python encoder path"))
unit("incremental-search/search-suggestions/count_terms.py::process_docs",
     ("C1.S1", [92], "`total_count = sum([count for count in counts.values()])` is bound and never read"),
     ("C3.S4", [100, 101, 102, 103], "for each unique term, `sum([1 if term in doc for doc in doc_counts])` scans every document's dict, so the document-count pass is O(terms x docs); the count could be taken while the per-doc counts are summed"))
unit("incremental-search/search-suggestions/count_terms.py::write_json_file",
     ("C10.S2", [27], "`re.sub(r\" \", \"/\", term)` runs a literal one-character replacement through the regex engine for every term; `term.replace(\" \", \"/\")` gives the same string"),
     ("C9.S1", [38, 39], "`json.dump(feed_list, f, indent=2)` writes the output in many small chunks through the file object; building the string once and writing it in one call does the same work with fewer calls"))
unit("incremental-search/search-suggestions/count_terms.py::count_terms",
     ("C10.S1", [59, 60, 61], "`not any(map(lambda word: word in common_words, doc[i:i+win_len]))` runs a Python lambda per word per window where `common_words.isdisjoint(...)` is one C-level call"))
unit("incremental-search/search-suggestions/accepted_words.py::process_docs",
     ("C10.S3", [28, 29, 30, 31, 32], "`term_set.add(term)` is called once per term in two loops; `term_set.update(clean_text(...))` does each loop's work in one call"))
unit("incremental-search/search-as-you-type/feed_to_vespa.py::vespa_feed",
     ("C9.S1", [83, 86], "`vespa_post` starts one `curl` subprocess per document, so the feed pays a process spawn per document instead of one bulk feed"))
unit("incremental-search/search-as-you-type/feed_to_vespa.py::vespa_remove",
     ("C9.S1", [75, 80], "`vespa_delete` spawns a separate `curl` process for each doc id in `doc_ids`"))
unit("incremental-search/search-as-you-type/feed_to_vespa.py::update_endpoint",
     ("C8.S4", [149, 167], "the feed file is parsed by `get_feed_docids` (line 149) and parsed again by `vespa_feed`/`get_docs` (line 167) although the first parse's data is still in scope"))
unit("incremental-search/search-as-you-type/feed_to_vespa.py::get_docs",
     ("C6.S6", [90, 91], "`file = open(index, ...)` is never closed; `json.load(file)` leaves the handle to the garbage collector"))
unit("feed_to_vespa.py::vespa_remove",
     ("C9.S1", [66, 67, 68], "one synchronous `session.delete` HTTP request per stale document id, while the same tool already bulk-feeds through `vespa feed`"))
unit("feed_to_vespa.py::update_endpoint",
     ("C8.S1", [164, 166], "`get_feed_docids` re-parses every feed file with `json.load` on each endpoint's pass; the id set depends only on file, namespace and doc_type"),
     ("C1.S5", [153, 154], "`get_indexed_docids` pages the whole namespace over HTTP even when neither `do_remove_index` nor `do_feed` is set; the result then feeds only a printed count"))
unit("text-search/python/collect_training_data.py::build_dataset",
     ("C5.S1", [71, 75], "`processed_queries` is a list (built by load_processed_queries) and `int(qid) not in processed_queries` runs once per query, so membership is O(n) and the loop quadratic"),
     ("C9.S1", [98, 99], "`PROCESSED_QUERIES_FILE` is opened and appended once per query because the `with` sits outside the `if` on line 75"))
unit("text-search/python/extract-msmarco.py::extract_documents",
     ("C9.S1", [85], "`out.tell()` runs per document on a text-mode file; TextIOWrapper.tell() flushes the write buffer, so each document costs a write"))
unit("text-search/python/extract-msmarco.py::load_msmarco_queries",
     ("C3.S6", [25, 26, 27], "every query is regex-normalised and stored, although only qids present in qrel are used later; the `qrel` parameter is accepted and ignored"))
unit("text-search/python/extract-msmarco.py::getcontent",
     ("C8.S2", [68, 69, 70, 71], "four `re.sub` calls with string patterns per document are looked up through re's cache each time rather than compiled once"))
unit("text-search/python/sample-queries-and-documents.py::select_documents",
     ("C10.S3", [56, 57, 58], "a per-docid `selected_doc_ids.add` loop over each query's docs where one `set.update` per query does the same"),
     ("C10.S1", [60], "`[docid for docid in offsets.keys()]` hand-copies the key list where `list(offsets)` does the same in C"))
unit("text-video-search/src/python/embedding.py::sample_images",
     ("C6.S2", [34, 36], "`np.array(images)` copies every decoded frame into a new array and then fancy-indexes it, so the sampled frames are copied twice; indexing the list would copy only the sample"))
unit("text-video-search/src/python/embedding.py::extract_images",
     ("C3.S6", [49, 50, 51, 52], "every frame of the video is decoded and retained, although sample_images keeps only number_frames of them"),
     ("C10.S1", [49, 50, 51], "a hand-written append loop with an unused index `i` where `list(reader)` builds the same list in C"))
unit("text-video-search/src/python/embedding.py::VideoFeedDataset.__getitem__",
     ("C10.S3", [96, 97, 98, 99], "the CLIP image encoder runs once per frame (batch of one through _from_image_to_vector) where stacking the frames into one encode_image call would do the same"),
     ("C3.S2", [100, 103], "`ntpath.basename(video_file_name)` and `.split(\".mp4\")[0]` are recomputed for every frame although constant per video"))
unit("text-video-search/src/python/embedding.py::search_video_file_names",
     ("C1.S4", [285, 288], "`video[\"children\"][0][\"children\"][0]` is walked again for both the video_file_name and relevance fields"))
unit("multilingual-search/ext/evaluate.py::search",
     ("C3.S1", [12, 13], "`query_group.iterrows()` builds a Series per row only to keep the last `query`; `query_group['query'].iloc[-1]` gives the same value without row iteration"))
unit("news/src/python/evaluate.py::read_impressions_file",
     ("C3.S6", [35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46], "every impression in the behaviours file is parsed into dicts, though calc_metrics keeps only `sample_size` (default 1000) of them with random.sample"))
unit("news/src/python/evaluate.py::predictions",
     ("C5.S2", [64, 65], "for each news_id, `find_hit` scans `hits[\"root\"][\"children\"]` linearly (n x m); one dict keyed by news_id built once per call would answer each lookup"))
unit("news/src/python/evaluate.py::calc_impression",
     ("C8.S4", [73], "`query_user_embedding` issues an HTTP request per impression although the same user recurs and the embedding does not change"))
unit("news/src/python/convert_embeddings_to_vespa_format.py::read_embeddings",
     ("C6.S3", [24, 25, 29], "the whole embeddings file is materialised as a dict of numpy arrays before the two convert functions walk it once each"),
     ("C5.S4", [28], "`np.array(vector.split(\",\"), dtype=np.float32)` converts text to float32 scalars that are later printed with \"%.6f\""))
unit("news/src/python/create_bert_embeddings.py::create_embeddings",
     ("C1.S1", [30, 31, 41, 42], "`categories` and `subcategories` are filled per row and never read"),
     ("C8.S2", [47, 48], "BertTokenizer and BertModel are reloaded with from_pretrained on every call; main calls create_embeddings twice"),
     ("C10.S3", [51, 57, 58], "the tokenizer and model run one document at a time (batch size one) inside the loop"),
     ("C1.S5", [57, 58], "the forward pass runs without torch.no_grad(), so an autograd graph is built per document and discarded after outputs[0] is read"),
     ("C5.S4", [59], "`outputs[0].tolist()[0][0]` converts the whole (1, L, 512) hidden-state tensor to nested lists just to keep the first token's 512 values"))
unit("news/src/python/create_bert_embeddings.py::write_embedding",
     ("C9.S1", [70, 71, 72, 73], "`f.write` is called once per float (512 per document) plus once per separator, where one joined string per embedding would be written"))
unit("news/src/python/create_category_ctrs.py::write_news_category_ctr_update",
     ("C3.S2", [79], "`'\"category_ctr_ref\": {\"assign\": \"%s\"}, ' % global_ctr_document_id` is re-formatted for every news item although global_ctr_document_id never changes"))
unit("news/src/python/mind_data.py::MindData.read_news",
     ("C1.S1", [57, 58, 59], "`title`, `abstract` and `url` are bound from the split line and never read"),
     ("C3.S5", [65, 66, 67, 73, 76, 80], "entity lists are fully parsed and deduplicated by add_entities although only the first two IDs are kept (`entity_ids[:entities_to_keep]`)"))
unit("news/src/python/mind_data.py::MindData.read_data",
     ("C1.S5", [93, 101], "datetime.strptime runs for every impression and its result is stored under \"timestamp\", a key that no code in the repository reads"))
unit("news/src/python/mind_data.py::MindData.sample_training_data",
     ("C4.S2", [145], "`random.random() <= prob` is evaluated per impression although every caller passes prob=1.0"))
unit("news/src/python/mind_data.py::MindData.add_impressions",
     ("C1.S5", [189, 190, 191, 198, 199, 200], "category, subcategory and entity indices are gathered per training sample, but train_mf.py discards them with `_` and train_cold_start.py reads only entities[:, 0]"),
     ("C1.S4", [189, 191, 198, 200], "`self.news_content[idx]` is looked up three or four times per positive and per negative sample where one local would serve"))
unit("news/src/python/mind_data.py::MindData.sample_valid_data",
     ("C1.S4", [170], "`sum(labels)` is computed twice in one condition"),
     ("C8.S1", [159, 179], "with prob=1.0 the result is deterministic but is rebuilt from scratch on every eval call (train_cold_start.py each epoch)"))
unit("news/src/python/train_cold_start.py::save_embeddings",
     ("C8.S2", [150], "`data_loader.get_news_content_tensors()` rebuilds identical tensors from unchanging news_content on every call"))
unit("news/src/python/train_cold_start.py::train_epoch",
     ("C6.S4", [83, 99], "`total_loss += loss` keeps a grad-tracking tensor, chaining autograd graph nodes across the epoch's batches"))
unit("news/src/python/train_mf.py::train_epoch",
     ("C6.S4", [47, 63], "`total_loss += loss` keeps a grad-tracking tensor, chaining autograd graph nodes across the epoch's batches"))
unit("news/src/python/train_cold_start.py::read_bert_embeddings",
     ("C5.S3", [164], "`np.zeros([num_news, 512])` allocates float64 for a buffer that torch.FloatTensor then copies to float32"))
unit("news/src/python/train_cold_start.py::read_bert_embeddings_from_file",
     ("C8.S3", [180, 183], "`data_loader.news()` is called again on each embedding line for a mapping that never changes"))
unit("news/src/python/vespa_client.py::query_user_embedding",
     ("C9.S1", [47, 48], "`requests.get` runs without a Session, so each per-impression call opens a new connection"))
unit("billion-scale-vector-search/app/src/main/python/recall.py::main",
     ("C1.S1", [96, 108, 109], "the `hits` list is appended with total_hits for every query and never read; `found_tie` from compute_recall_with_distance_ties is bound and never used"))
unit("commerce-product-ranking/scripts/evaluate.py::main",
     ("C9.S2", [52], "`pd.read_parquet(args.example_file)` loads every column, but only query_id, query, product_id, split, product_locale and small_version are read"),
     ("C1.S4", [75, 76], "`grouped_df.set_index(\"query_id\")` is computed twice, once for [\"query\"] and once for [\"recall\"]"))
unit("hypencoder/encode_query.py::main",
     ("C5.S4", [70, 71, 72], "`np.array(enc.ids, dtype=np.float32).tolist()` builds an ndarray only to convert it back to lists (about 64 elements per call)"))
unit("hypencoder/model2onnx.py::QueryEncoderWrapper.forward",
     ("C7.S5", [143], "`weights[i][0].transpose(0,1).contiguous()` cancels the `.transpose(2,1)` applied in _get_weights_and_biases_static, so the exported graph transposes twice per block weight per query"))
unit("hypencoder/model2onnx.py::_get_weights_and_biases_static",
     ("C7.S5", [112], "the `.transpose(2,1)` here cancels the transpose undone in QueryEncoderWrapper.forward (line 143)"))
unit("examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::subgraph_GenerateKeywords",
     ("C8.S2", [23, 24, 25, 26, 27, 28, 29, 31, 32, 33, 34, 52], "ChatOpenAI, the PromptTemplate and the StructuredOutputParser are rebuilt on every node call although they never change"))
unit("examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::subgraph_EvaluateCategory",
     ("C8.S2", [67, 68, 69, 70, 71, 72, 99, 100, 101, 102, 103], "the parser, prompt and ChatOpenAI client are rebuilt per call from constant inputs"))
unit("examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::subgraph_EvaluateFilters",
     ("C8.S2", [124, 153], "the schema, parser, prompt and ChatOpenAI(model=\"gpt-4o-mini\") are reconstructed on every invocation"))
unit("examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::EvaluateResults",
     ("C8.S2", [174, 201], "the parser, prompt and ChatOpenAI are rebuilt per call; the format instructions are recomputed inline at line 193"))
unit("examples/book-search/frontend/app.py::feed_catalog",
     ("C9.S1", [21, 25], "each JSONL line triggers its own feed_data_point HTTP call in the loop, where a batched feed would replace N round trips"))
unit("examples/ecommerce-user-preferences/webapp/app.py::chat",
     ("C8.S4", [435], "`load_system_prompt()` re-reads the unchanging system_prompt.txt from disk on every chat request"),
     ("C6.S2", [472, 475], "`session.get('preferences', {}).copy()` is copied again into json_data, so the first copy is redundant"),
     ("C9.S1", [498, 499, 500, 501, 502], "query_vespa and query_vespa_facets are two sequential POSTs to the same endpoint with the same preferences"),
     ("C1.S2", [464, 489, 493], "`session.modified = True` is set three times in one request; only the first set changes anything"))
unit("examples/ecommerce-user-preferences/webapp/app.py::update_preferences",
     ("C9.S1", [534, 537], "the results query and the facets query are two separate sequential Vespa POSTs for the same preferences"))
unit("examples/ecommerce-user-preferences/webapp/app.py::get_wikipedia_image",
     ("C8.S1", [103, 127, 207, 208], "a miss returns None without caching it, so each request for a make/model with no image repeats up to about six Wikipedia API calls"))
unit("examples/google-cloud/cloud-functions/python/main.py::get_blobs",
     ("C8.S2", [88], "`storage.Client()` is constructed on every call, including credential discovery, and could be created once per instance"))
unit("examples/google-cloud/cloud-functions/python/main.py::listfiles",
     ("C4.S8", [46], "`blob.name.__contains__(file_filter)` is the long-hand form of `file_filter in blob.name` and misses the operator's fast path"))
unit("examples/google-cloud/cloud-functions/python/main.py::getlogs",
     ("C4.S8", [61, 63, 69], "`blob.name.__contains__('.zst')`, `blob.name.__contains__(file_filter)` and `json_data['uri'].__contains__(uri_filter)` use the dunder spelling"))
unit("examples/in-context-learning/categorize_group.py::inference",
     ("C1.S1", [128, 134, 140, 147, 154, 161, 168, 175, 182, 189, 196, 203], "eleven of the twelve query_request_* dicts are built on every call and never used; only query_request_bm25_no_group_10 is sent"))
unit("examples/embedder-auto-training-evaluation/training-evaluation/evaluate.py::main",
     ("C11.S5", [82, 83, 84, 85, 86], "each query's blocking HTTP search runs one after another on a single session although the requests are independent"))
unit("examples/embedder-auto-training-evaluation/training-evaluation/positives-negatives.py::main",
     ("C11.S5", [91, 92, 93], "the same sequential per-query HTTP pattern as evaluate.py"),
     ("C6.S3", [95, 96, 97], "all of train_data is materialised before one write loop, where each record could be streamed as it is produced"))
unit("examples/embedder-auto-training-evaluation/training-evaluation/train.py::TrainDataset.__init__",
     ("C6.S3", [12, 18], "`file.readlines()` builds a full list of raw lines before parsing, holding the corpus as text twice; iterating the file object would stream"))
unit("examples/embedder-auto-training-evaluation/training-evaluation/train.py::TrainDataset.__getitem__",
     ("C5.S1", [27, 28, 29, 31, 32, 33], "pop(0) plus append rotates the positives and negatives lists on every access, making the most frequent operation O(n); a deque would make it O(1)"))
unit("examples/mcp-server-app/script/generate_data.py::generate_job",
     ("C1.S5", [68, 69, 70, 71, 72, 73], "`template.format(...)` eagerly draws adjective, project, action and skill via random.choice, though the chosen template may use only some of them"))
unit("examples/mcp-server-app/script/generate_data.py::save_vespa_feed",
     ("C6.S3", [124, 125, 126, 127, 128, 129, 130], "the full output list is built and joined into one string before writing, where per-item writes would stream"))
unit("examples/workshop-ecommerce/preprocess.py::process_orders",
     ("C8.S4", [234, 247], "re-reads dataset/orders.csv and dataset/order_products__train.csv although process_users already loaded the same files in the same run"),
     ("C3.S6", [253, 258, 308], "sort, groupby/agg (with a Python lambda) and merge run over every row of the eval set, though the loop breaks after `limit` orders at line 308"),
     ("C3.S1", [290], "`df_orders_vespa.iterrows()` builds a Series per order and upcasts dtypes row by row, though only scalar fields are read"))
unit("examples/workshop-ecommerce/preprocess.py::process_users",
     ("C3.S6", [181, 182, 183, 184, 185, 188], "the merge of df_order_products_train with df_order and the groupby over all rows run even in sample mode (limit 10), which writes only the first 10 groups"),
     ("C3.S1", [202], "`user_purchases_df.iterrows()` builds a Series per row for every user"))
unit("examples/workshop-ecommerce/preprocess.py::process_products",
     ("C3.S1", [152], "the same iterrows() per-row Series pattern over the products table"))
unit("rag-blueprint/eval/collect_pyvespa.py::feature_collection_first_phase_query_fn",
     ("C1.S4", [95, 96], "`embed(@query)` is written for both `embedding` and `float_embedding`, so the same text is embedded twice server-side"))
unit("rag-blueprint/eval/collect_pyvespa.py::feature_collection_second_phase_query_fn",
     ("C1.S4", [49, 50], "`embed({query_text})` is written twice in one request dict, for input.query(embedding) and input.query(float_embedding)"))
unit("rag-blueprint/eval/evaluate_ranking.py::rank_first_phase_query_fn",
     ("C1.S4", [55, 56], "`embed({query_text})` is computed twice in one dict, for embedding and float_embedding"))
unit("rag-blueprint/eval/evaluate_ranking.py::rank_second_phase_query_fn",
     ("C1.S4", [85, 86], "same duplicate embed for embedding and float_embedding"))
unit("rag-blueprint/eval/evaluate_match_phase.py::match_weakand_query_fn",
     ("C1.S5", [18], "sends input.query(embedding) although its yql has no nearestNeighbor and the match-only profile does not read query(embedding)"))
unit("rag-blueprint/eval/train_lightgbm.py::perform_cross_validation",
     ("C3.S4", [249, 254], "for each selected feature a linear scan over feature_name_mapping.items() finds the renamed column (O(F x N)); a reverse dict would be O(F + N)"),
     ("C5.S4", [265, 275], "the model dict is dumped to a string, each feature name is regex-substituted across the whole JSON, then re-parsed and dumped again; renaming the dict directly avoids the round trip"))
unit("rag-blueprint/eval/train_logistic_regression.py::perform_cross_validation",
     ("C1.S5", [102, 103], "`X[feature].describe()` computes count, quartiles and std per feature, but only mean, std, min and max are read"))
unit("visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.gen_similarity_maps",
     ("C1.S1", [83, 88], "`processed_images` is filled at line 88 and never read"),
     ("C6.S2", [86], "`img_pil.copy()` makes a full-size copy of every image, though nothing mutates img_pil afterwards"),
     ("C3.S2", [97, 98, 99], "`self.should_filter_token(token)` depends only on token, yet it is recomputed inside the image loop for every image"))
unit("visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator._prepare_similarity_map_tensor",
     ("C3.S2", [147, 148, 149, 150], "the hasattr test and image_seq_length are recomputed for every cell in the innermost loop, though self.processor never changes"),
     ("C10.S3", [142, 159], "each cell does a scalar item assignment into the tensor, one tensor op per cell, where a single index_put would batch them"))
unit("visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.should_filter_token",
     ("C8.S2", [253, 256], "`re.compile(...)` builds the same pattern on every call; a compiled pattern could be derived once"))
unit("visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.format_query_results",
     ("C1.S5", [100, 101, 102, 103, 104], "query_time, count and result_text are computed eagerly and their only consumer is self.logger.debug(result_text)"))
unit("visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.get_result_from_query",
     ("C1.S3", [241, 248], "the colpali and hybrid branches make the identical query_vespa_colpali call, so the branch outcome does not change what runs"),
     ("C1.S5", [256, 257], "the loop over every child exists only to call logger.debug on the field keys"))
unit("visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.query_vespa_colpali",
     ("C5.S4", [405, 406, 407, 408], "the query tensor goes tensor -> tolist() (format_q_embs) -> np.array -> packbits; the sign bits could be taken on the tensor before the list conversion"))
unit("visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.get_suggestions",
     ("C10.S1", [364], "`set([item for sublist in questions for item in sublist])` is a hand-written flatten where `set().union(*questions)` does the same in C"))
unit("visual-retrieval-colpali/prepare_feed_deploy.py::generate_embeddings",
     ("C10.S3", [555, 559], "the batch_size parameter is never passed to DataLoader, so the default batch of one gives one model forward per page"))
unit("visual-retrieval-colpali/prepare_feed_deploy.py::float_to_binary_embedding",
     ("C10.S1", [587, 588, 589, 590, 591], "a Python loop calls np.array, np.where, np.packbits and tolist separately for each patch vector; one vectorised packbits over the stacked array does the same work"))
unit("visual-retrieval-colpali/vespa_feed_to_hf_dataset.py::save_image",
     ("C1.S5", [22, 23, 24], "the JPEG bytes are decoded by PIL and re-encoded by img.save, though the raw bytes could be written directly"))
unit("visual-retrieval-colpali/src/main.py::get_and_store_sim_maps",
     ("C8.S1", [262, 263, 269, 281, 282, 283, 284, 285, 286, 287], "every search re-runs the Vespa _sim query and regenerates and rewrites every blended PNG, though the output is deterministic per (query, ranking) and keyed by query_id"),
     ("C6.S3", [273, 274, 275, 276, 277], "`all([os.path.exists(...) for ...])` materialises the full list of stat results every 0.2 s and does not short-circuit"),
     ("C4.S2", [278], "the post-loop `if not all([...])` re-stats every file even when the loop already exited because all files existed"))
unit("visual-retrieval-colpali/src/main.py::fetch_results",
     ("C11.S4", [205, 206, 207], "the synchronous get_query_embeddings_and_token_map (a ColPali forward pass) runs inside an async def, blocking the event loop for other tasks"))
unit("visual-retrieval-colpali/src/main.py::get_suggestions",
     ("C8.S1", [349, 350, 351, 352, 353, 354], "each request runs an uncached Vespa regex query for the same prefix; the unused backend cache.py LRU class would answer repeats"))
unit("visual-retrieval-colpali/src/main.py::message_generator",
     ("C3.S3", [369, 370, 371, 380], "Image.open re-runs for every already-ready document on each 0.2 s poll, reopening images that were opened on the previous pass"),
     ("C7.S5", [360, 365], "`min(num_images, len(doc_ids))` in the while condition is recomputed every iteration and equals num_images"),
     ("C10.S4", [395, 402, 403], "`response_text += chunk.text` followed by replace_newline_with_br rescans and recopies the whole accumulated string on every streamed chunk"),
     ("C1.S5", [372, 373, 374, 377, 378, 379], "the f-string log messages are formatted on every idx and every iteration and discarded at the default INFO level"))
unit("visual-retrieval-colpali/src/main.py::get_sim_map",
     ("C1.S5", [306, 307, 308], "the logger.debug f-string is built on every not-ready poll (one per token button every 0.5 s) and discarded at INFO level"))
unit("visual-retrieval-colpali/src/main.py::full_image",
     ("C5.S4", [332, 336], "a base64 image is decoded to bytes on a cache miss, and on a hit the file is read and base64-encoded again, a round trip a stored string would avoid"))
unit("visual-retrieval-colpali/src/frontend/app.py::SearchResult",
     ("C1.S4", [559, 560], "`key.split(\"_\")` is computed twice per sim_map key, once for token and again inside int(key.split(\"_\")[-1])"))
unit("visual-retrieval-colpali/src/frontend/app.py::ChatResult",
     ("C1.S6", [745, 746, 747, 748, 749], "`messages = Div(LoadingSkeleton())` is built unconditionally and then overwritten by the `if doc_ids:` branch"))
unit("visual-retrieval-colpali/src/frontend/app.py::SimMapButtonPoll",
     ("C9.S1", [500, 501, 502], "every not-ready token button sends its own hx_get to /get_sim_map every 0.5 s until it is ready, many small requests where one batched or pushed update would do"))
unit("reverse-image-search/script/feed.py::run",
     ("C4.S7", [136, 137, 138, 139, 140], "ex[\"image\"] and the isinstance check run before the cheap `abs_path.exists() and not refeed` skip, so already-fed rows still pay for image access"),
     ("C1.S4", [140, 144], "abs_path.exists() is evaluated at line 140 and again at line 144, a second stat for the same answer"),
     ("C8.S4", [152, 153], "abs_path.read_bytes() reads the JPEG and then Image.open(abs_path) re-reads and decodes the same file from disk"))

with open("/home/javad/energy-run/sample-apps/step1.jsonl", "w") as f:
    for rec in U:
        f.write(json.dumps(rec) + "\n")
print(len(U), "units written;", sum(len(r["suspicions"]) for r in U), "suspicions")
