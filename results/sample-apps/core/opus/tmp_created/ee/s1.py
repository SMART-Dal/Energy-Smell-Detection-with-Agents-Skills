import json
U = []
def u(unit, *s):
    U.append({"step": 1, "unit": unit, "suspicions": [{"label": chr(97+i), "lines": l, "why": w} for i, (l, w) in enumerate(s)]})

CT = "incremental-search/search-suggestions/count_terms.py"
u(CT+"::process_docs",
  ([100,101,102,103], "for every distinct term the document frequency is computed by scanning all of `doc_counts` and building a list of 0/1 per document: O(terms x docs) work, while the per-document dicts are already iterated once at lines 91-97 where a +1 per term would give the same count"),
  ([92], "`total_count = sum([...])` is computed for every document and never read"))
u(CT+"::process_doc",
  ([77,78,79], "the merge iterates `list(title_counts.keys()) + list(content_counts.keys())`, building two lists and recomputing the sum for every term present in both dicts"))
u(CT+"::count_terms",
  ([59,60,61,62], "each window calls a lambda per word through `any(map(...))` and slices `doc[i:i+win_len]` twice; common-word membership is re-tested for the same word once per window length"))
u(CT+"::write_json_file",
  ([27], "`re.sub(r\" \", \"/\", term)` runs the regex engine (and a cache lookup) for every term to replace one literal character, where `str.replace` does the same"))
u("incremental-search/search-suggestions/accepted_words.py::process_docs",
  ([29,30,31,32], "terms are added to `term_set` one at a time in a Python loop, where `set.update` consumes the list in C"))

u("news/src/python/evaluate.py::predictions",
  ([64,65,66], "for each news_id `find_hit` linearly scans all `hits['root']['children']`, O(n^2) per impression; one dict from news_id to first hit would answer each lookup in O(1)"))
u("news/src/python/metrics.py::dcg_score",
  ([19,20,21,23], "a full `argsort` of every score list to take the top k, and list-to-array conversions in `np.shape`/`np.take`, repeated for each of the separate k=5 and k=10 calls"))
u("news/src/python/metrics.py::group_auc",
  ([9,10,11,12,13,14], "sklearn `roc_auc_score` is called once per impression; its input validation and type checks dominate on short label lists"))
MD = "news/src/python/mind_data.py::MindData."
u(MD+"sample_valid_data",
  ([166,167,168,169], "category, subcategory, entity and user index lists are built for every impression before the filter at line 170 discards impressions whose labels are all 0 or all 1"),
  ([170], "`sum(labels)` is computed twice"))
u(MD+"read_data",
  ([93,101], "`datetime.strptime` runs on every impression line to fill a `timestamp` key that nothing in news/src/python reads"))
u(MD+"add_entities",
  ([79,80], "`entity_id not in entity_ids` is a list membership test, and every entity is collected although read_news keeps only the first 2"))
u(MD+"add_impressions",
  ([189,190,191,198,199,200], "`self.news_content[index]` is looked up three times per positive and per sampled negative, for a mapping that never changes"))
u("news/src/python/train_cold_start.py::write_embeddings",
  ([159,160], "each row is fetched with `embeddings[index]` (a tensor indexing op on a tensor that requires grad, recording an autograd node) and converted with `.tolist()` separately; converting the whole tensor once avoids N tensor ops"))
u("news/src/python/train_cold_start.py::save_embeddings",
  ([151,152], "user and news embeddings are computed outside `torch.no_grad()`, so autograd records a graph over every user and news item that is never back-propagated"))
u("news/src/python/train_cold_start.py::train_model",
  ([120], "`save_embeddings` runs every epoch and overwrites both TSVs; only the last epoch's files survive"))
u("news/src/python/train_cold_start.py::train_epoch",
  ([99], "`total_loss += loss` accumulates the autograd tensor, chaining an AddBackward node per batch for the whole epoch"))
u("news/src/python/train_cold_start.py::read_bert_embeddings_from_file",
  ([180,182,183], "`data_loader.news()` called twice per line and the vector built as a Python float list before assignment into the numpy row"))
u("news/src/python/train_mf.py::write_embeddings",
  ([117,118], "same per-row `embeddings[index].tolist()` on a grad-requiring tensor as train_cold_start.write_embeddings"))
u("news/src/python/train_mf.py::save_embeddings",
  ([109,110], "embedding lookups over all users/news run outside `torch.no_grad()`, recording an unused autograd graph"))
u("news/src/python/train_mf.py::main",
  ([145,146], "with epochs=100 the final epoch of train_model already ran both evals on the same model; main repeats them"))
u("news/src/python/create_bert_embeddings.py::write_embedding",
  ([68,69,70,71,72,73], "two `f.write` calls per float (about 1024 per document) where one join and one write produce the same bytes"))
u("news/src/python/create_bert_embeddings.py::create_embeddings",
  ([57,58,59], "forward pass per document without `torch.no_grad()`, and `outputs[0].tolist()[0][0]` converts the whole [1,seq,512] hidden state to nested lists to read one CLS vector"),
  ([41,42], "`categories` and `subcategories` dicts are filled and never read"),
  ([47,48], "tokenizer and model are loaded inside the function, which main calls twice"))
u("news/src/python/convert_embeddings_to_vespa_format.py::convert_user_embeddings",
  ([135], "\"%.6f\" formatting iterates the float32 ndarray one numpy scalar at a time; `embedding.tolist()` first gives Python floats with identical formatting"))
u("news/src/python/convert_embeddings_to_vespa_format.py::convert_news_embeddings",
  ([149], "same per-numpy-scalar formatting as convert_user_embeddings"))
u("news/src/python/convert_embeddings_to_vespa_format.py::read_embeddings",
  ([124], "`np.array(vector.split(','), dtype=np.float32)` builds a list of strings and converts each through numpy's string parsing"))
u("news/src/python/convert_to_vespa_format.py::read_impressions_file",
  ([33,34], "csv.DictReader builds a 5-key dict per line, including the long history field, to read only `impressions`"))
u("news/src/python/convert_to_vespa_format.py::convert_file",
  ([71], "`json.dump(doc, output)` uses the pure-Python iterencode with many writes per document; `output.write(json.dumps(doc))` uses the C encoder for the same bytes"))
u("news/src/python/create_category_ctrs.py::read_impressions_file",
  ([32,33,36,37,38,39,40], "DictReader dict per line to read one field; `click_map[category]` indexed twice per impression"))
u("news/src/python/create_category_ctrs.py::read_content_file",
  ([51,52,53], "DictReader builds an 8-key dict per line to read 2 fields"))
u("news/src/python/vespa_client.py::query_user_embedding",
  ([235], "module-level `requests.get` creates a new Session and connection per call; evaluate.py calls it once per impression"))

u("text-search/python/sample-queries-and-documents.py::select_documents",
  ([60,61,62], "when the target count is the whole corpus, random.choice with replacement collects every id (about n ln n draws) and `min(...)` is re-evaluated per iteration; the result is then simply all ids"))
u("text-search/python/collect_training_data.py::build_dataset",
  ([75], "`int(qid) not in processed_queries` is a membership test on a list, O(Q x P)"),
  ([98,99], "the processed-queries file is opened and appended for every query, including those already processed, so each resume duplicates entries"))
u("text-search/python/extract-msmarco.py::getcontent",
  ([68,69,70,71], "four `re.sub` calls with string patterns per document, each paying a regex-cache lookup"))
u("colbert-long/scripts/convert.py::remove_control_characters",
  ([7], "`unicodedata.category` is called in a Python generator for every character of every chunk; the category only needs computing once per distinct character"))
u("multilingual-search/ext/evaluate.py::search",
  ([12,13], "`iterrows()` builds a Series for every row of the group only to keep the last row's `query`"))
u("msmarco-ranking/python/evaluate_passage_run.py::get_result",
  ([55,56,57,58,59,60,61], "the template dict is rescanned with `\"{query}\" in value` for every query although which keys need formatting never changes"))

LG = "rag-blueprint/eval/train_lightgbm.py::perform_cross_validation"
u(LG,
  ([188], "the training Dataset is in `valid_sets`, so AUC on ~80% of rows is computed every boosting round, only to be logged every 100 rounds"),
  ([268,269,270,271,272,273,274,275], "model JSON is dumped to a string, scanned once per feature with `re.sub`, parsed again with json.loads, then dumped again: F full-string regex passes plus a parse/serialize round trip"),
  ([100,101], "`col in feature_cols` is a list membership test per column"),
  ([249,250,251,252,253,254], "nested loop scanning all of `feature_name_mapping` for each selected feature, O(F^2), instead of an inverted dict"),
  ([78], "`df[c].nunique(dropna=False)` is computed column by column in Python"))
u("rag-blueprint/eval/train_logistic_regression.py::perform_cross_validation",
  ([102,103], "`X[feature].describe()` per feature computes count and quartiles (a sort) of which only mean, std, min, max are printed"),
  ([138,139], "`model.predict` and `model.predict_proba` each compute the decision function on the same test set"))
u("rag-blueprint/eval/evaluate_match_phase.py::match_semantic_query_fn",
  ([53,54,55,56,57,58,59,60,61,62,63,64,65,66,67], "the querybuilder tree and its YQL string do not depend on `query_text` but are rebuilt and serialized for every query"))
u("rag-blueprint/eval/train_lightgbm.py::strip_feature_prefix",
  ([25], "`re.sub` with a string pattern per call pays a regex cache lookup where `removeprefix`-style checks would do"))

u("examples/in-context-learning/categorize_group.py::inference",
  ([128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,194,195,196,197,198,199,200,201,202,203,204,205,206,207,208,209], "12 request dicts are built per call and only `query_request_bm25_no_group_10` is used"),
  ([211], "bare `requests.post` per query without a Session, so no connection reuse over 1000 queries"))
u("examples/in-context-learning/categorize_group.py::get_label",
  ([66,68], "`result not in label_names` is a list membership test over 77 labels, up to twice per call"))
PP = "examples/workshop-ecommerce/preprocess.py::"
u(PP+"process_users",
  ([202,203,204,205,206,207,208,209], "`iterrows()` builds a pandas Series for every purchase row of every user, then four scalar lookups and int() per row"),
  ([175], "orders.csv read with every column although only four are used"))
u(PP+"process_orders",
  ([290,291,292,293,294,295,296,297,298,299,300,301,302,303], "`iterrows()` per order builds a Series per row (object dtype because of product_ids)"),
  ([238], "`.copy()` of a boolean-indexed frame that is only merged afterwards"),
  ([258,259,260], "`.agg({'product_id': lambda x: list(x)})` calls a Python lambda per group"))
u(PP+"process_products",
  ([152,153,154,155,156,157,158,159,160,161,162], "`iterrows()` per product builds a Series per row"),
  ([139,144,145,146], "the full product table is merged even when only `limit` rows are written"))
EU = "examples/ecommerce-user-preferences/webapp/app.py::"
u(EU+"load_system_prompt",
  ([46,47,48], "system_prompt.txt is opened and read from disk on every /api/chat request"))
u(EU+"get_wikipedia_image",
  ([86,96,118,146,179], "bare `requests.get` per call (no Session), one imageinfo request per candidate image, and misses are not cached so every repeat lookup repeats the whole sequence"))
u(EU+"query_vespa",
  ([279], "`json.dumps(query, indent=2)` pretty-prints the full query for a print line; requests serializes it again"),
  ([276], "`trace.level: 1` asks Vespa for trace output that nothing reads"))
u("commerce-product-ranking/scripts/evaluate.py::main",
  ([52,53,54,55], "three successive boolean filters each materialize a full intermediate frame"),
  ([75,76], "`grouped_df.set_index('query_id')` computed twice"),
  ([91,92,93,94,95], "`groupby.apply` with a Python lambda per group to build dicts"))
u("use-case-shopping/convert_meta.py::process",
  ([38,39,40], "`fields['categories_text'] +=` grows a string through a dict item (no in-place resize) and each prefix is re-sliced and re-joined, O(L^2) per category"))
u("use-case-shopping/convert_reviews.py::process",
  ([94,95,96,97,98,99,100,101,102,103,104,106], "all fields (including int conversions) are built before `contains_illegal_chars` may reject the record"))
u("use-case-shopping/create_suggestions.py::filter",
  ([62,63,64], "33 separate substring scans per text in a Python loop; called for every title and every noun chunk"),
  ([60], "dead check: `len(text) < 3` already returned at line 58"))
u("use-case-shopping/create_suggestions.py::filter_content",
  ([68,69,70], "Python loop of `startswith` calls where one `startswith(tuple)` call does the same"))
IS = "incremental-search/search-as-you-type/feed_to_vespa.py::update_endpoint"
u(IS,
  ([141,155,156,157,158,159,160], "with both removal and feed enabled, every indexed document is deleted, then the stale `docids_in_index` is diffed and the same documents are deleted again, one curl process each"),
  ([149], "`docids_in_feed = docids_in_feed.union(...)` allocates a new set per feed file"))
RF = "feed_to_vespa.py::"
u(RF+"update_endpoint",
  ([156,157,158,172,173,174,175,176,177], "with both flags set, every indexed doc is deleted at 158, then docids_to_remove is computed from the stale set and those docs are deleted again"),
  ([166], "`docids_in_feed.union(...)` allocates a new set holding everything so far, per feed file"),
  ([153], "the whole index is visited even when neither removal nor feed is enabled and the result is unused"))
u(RF+"get_feed_docids",
  ([123,125,127], "`set([...])` builds an intermediate list; the namespace prefix is formatted per document"))
u(RF+"get_indexed_docids",
  ([107,113], "`ids` list built only to be iterated once; `id.replace(docid, encoded)` rescans the whole id although the suffix position is known"))
FS = "feed-split.py::"
u(FS+"split_text",
  ([97], "`text = text + \"\\n\" + line` concatenates a new copy of the section text for every line: the first `+` is not the last op before the store, so CPython's in-place resize cannot apply, making it quadratic in section length"),
  ([83], "`str(soup)` serializes the whole tree and markdownify re-parses it with BeautifulSoup"))
u(FS+"xml_fixup",
  ([37,38,39,40], "each match triggers a full-document `text.replace`, O(matches x len), including when the escaped text equals the original"))
u(FS+"what_language",
  ([20,24,26], "`el.text` walks and joins all descendant strings up to three times per element"))
u(FS+"split_lists",
  ([109,110,111], "recursive `find_all('li')` per list revisits inner items of nested lists once per enclosing list"))
u("test/pseudo_terminal.py::Log.write",
  ([31,32,33], "the regex match runs on every output chunk even when `_verbose` is False and its result is unused"))
u("test/test.py::process_liquid",
  ([176,177], "one `re.sub` with a string pattern per transform per call"))
u("test/test.py::parse_file",
  ([212,213], "`str(type(line))` builds a type-repr string per node only to test its type"))
u("billion-scale-vector-search/app/src/main/python/recall.py::compute_recall_with_distance_ties",
  ([63,64,65,66,67], "Python loop over ground-truth distances doing numpy-scalar arithmetic per element"))
u("reverse-image-search/script/feed.py::run",
  ([145,152,153], "the image is JPEG-encoded and written by `_save_image`, then read back from disk and decoded again to get a PIL image"),
  ([140,144], "`abs_path.exists()` called twice per image"))
u("reverse-image-search/script/search.py::_search",
  ([89,90], "`embedding.astype(np.float32)` copies an array that is already float32, and `binary_q.astype(int)` copies before tolist"))
TV = "text-video-search/src/python/embedding.py::"
u(TV+"sample_images",
  ([32,33,34], "`np.array(images)` stacks every frame into one big array, then fancy-indexes it (a second copy) to keep a few frames"))
u(TV+"extract_images",
  ([48,49,50,51,52], "every frame is decoded and kept in memory although only a handful are sampled"))
u(TV+"VideoFeedDataset.__getitem__",
  ([98,99], "each frame is encoded through the model as its own batch of 1"),
  ([100,103,106], "`ntpath.basename` and `.split('.mp4')` recomputed per frame; `image.tolist()[0]` converts the whole tensor to keep row 0"))
u(TV+"compute_and_send_video_embeddings",
  ([145,146,147,148,149,150,151,152,153,154,155,156,157,158], "a new VideoFeedDataset per model name decodes every video again for each model"))
u("text-video-search/src/python/app.py::get_predefined_queries",
  ([33,34,35,36], "HTTP GET on every Streamlit rerun, uncached"))
u("custom-embeddings/model.py::CustomEmbeddingSimilarity.forward",
  ([17,18], "`torch.cat` copies query and document; fc1's query half is recomputed for every document of the same query"))
u("model-inference/src/main/application/models/pytorch_pairwise_ranker.py::PairwiseRankerModel.forward",
  ([16,17,18,19], "the query half of `query_doc_transform` is computed twice per pair and the query is copied twice by `torch.cat`"))
u("billion-scale-image-search/app/src/main/python/ranker_export.py::Ranker.forward",
  ([12], "`torch.sum(query*documents, 1)` materializes a batch x 768 product before reducing; a matmul computes the scores directly"))
u("hypencoder/model2onnx.py::QueryEncoderWrapper._get_weights_and_biases_static",
  ([106,112,117,123], "`repeat_interleave`/`repeat` copy base matrices per batch inside the exported graph although batch is 1 at serving time"))
u("colbert/model2onnx.py::VespaColBERT.__init__",
  ([16,17,18], "BERT is randomly initialized by from_config, re-initialized by init_weights, then overwritten by from_pretrained"))

VC = "visual-retrieval-colpali/"
u(VC+"src/backend/colpali.py::SimMapGenerator.gen_similarity_maps",
  ([86,88], "every decoded page image is copied with `img_pil.copy()` into `original_images`, and also kept in `processed_images`, which is never read"),
  ([85,104], "`_blend_image` never uses its `img` argument; full RGB decode of each page is only needed for its size"))
u(VC+"src/backend/colpali.py::SimMapGenerator._prepare_similarity_map_tensor",
  ([147,148,149,150], "`hasattr(self.processor, 'image_seq_length')` and the attribute read run for every cell though invariant"),
  ([154,155,156,157,158,159], "one tensor `__setitem__` per cell (tens of thousands of cells) instead of a single advanced-index assignment"))
u(VC+"src/backend/colpali.py::SimMapGenerator._blend_image",
  ([189,190], "colormap returns float64 RGBA that is multiplied by 255 and cast to uint8, then `.convert('RGBA')` copies an image that is already RGBA"))
u(VC+"src/backend/colpali.py::SimMapGenerator.should_filter_token",
  ([253,254,255], "`re.compile` (a regex cache lookup) on every call; called per image x token"))
u(VC+"src/backend/colpali.py::SimMapGenerator.get_query_embeddings_and_token_map",
  ([275,276,277], "input_ids are decoded to text and re-tokenized instead of converting ids to tokens directly"))
u(VC+"src/backend/vespa_app.py::VespaQueryClient.float_to_binary_embedding",
  ([167,168,169,170,171], "`np.where(np.array(vector) > 0, 1, 0)` allocates an int64 0/1 array per vector before packbits, which accepts the boolean mask directly"))
u(VC+"src/backend/vespa_app.py::VespaQueryClient.format_q_embs",
  ([214], "iterates the tensor row by row, creating a row tensor and calling `.tolist()` per row, where one `q_embs.tolist()` gives the same lists"))
u(VC+"src/backend/vespa_app.py::VespaQueryClient.get_result_from_query",
  ([239,240], "`ranking.split('_')` computed three times"),
  ([256,257], "per-result `logger.debug(... .keys())` loop runs even at INFO level"))
u(VC+"src/backend/vespa_app.py::VespaQueryClient.format_query_results",
  ([100,101,102,103,104], "query time, count and an f-string are built for a debug log on every call even when debug is off"))
u(VC+"prepare_feed_deploy.py::float_to_binary_embedding",
  ([588,589,590], "per row, `np.where(np.array(v) > 0, 1, 0)` allocates an int64 array before packbits, which takes the boolean mask directly"))
u(VC+"prepare_feed_deploy.py::generate_embeddings",
  ([555,556,557,558,559,566,568], "`batch_size` is never passed to the DataLoader (batch of 1, one forward per image), and np.concatenate converts a list of tuples of tensors one by one"))
u(VC+"prepare_feed_deploy.py::download_pdf",
  ([266,267,268], "on an invalid filename `continue` skips `attempt += 1` and the sleep, so the same PDF is re-downloaded without bound"))
u(VC+"vespa_feed_to_hf_dataset.py::save_image",
  ([22,23,24], "already-JPEG bytes are decoded and re-encoded to write the file"))
u(VC+"refeed_from_hf.py::process_item_for_vespa",
  ([41,42,43,44,45], "every item's ~1040 keys are scanned with startswith/split to rebuild a key-to-index map that is the same for every row"))
u(VC+"refeed_from_hf.py::pil_to_base64",
  ([27,28], "decoded PIL image re-encoded to JPEG; `buffer.seek(0)` before `getvalue()` is unneeded"))
u(VC+"src/main.py::message_generator",
  ([402,403,404], "each chunk appends to `response_text` and then `replace_newline_with_br` rescans the whole accumulated text: O(n^2) in response length"),
  ([364,365,366,367,368,369,380], "every 0.2 s poll re-opens every image, including those already opened"))
u(VC+"src/main.py::get_and_store_sim_maps",
  ([273,274,275,276,278], "`all([os.path.exists(...)])` builds a list (no short circuit) every 0.2 s and is re-run after the loop"),
  ([288,289,290], "each PNG is base64-encoded by `_blend_image` and immediately base64-decoded to write the file"))
u(VC+"src/main.py::full_image",
  ([335,336], "cached JPEG is read and base64-encoded into a data URI on every request"))
u(VC+"src/backend/stopwords.py::filter",
  ([10], "`nlp(text)` on a blank pipeline builds a Doc via the full pipeline call where `nlp.tokenizer(text)` is equivalent"))
u(VC+"src/frontend/app.py::SearchResult",
  ([548,549,550,551,552,553,554,558,559,560], "dict comprehension scans all fields to find sim_map keys, then each key is split twice"))
u("examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/vespa_module/vespa_retriever.py::create_conditions",
  ([12,13,14,15,16,17,18,19,20], "the `operators` dict of lambdas is rebuilt on every call although invariant"))
u("examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::subgraph_GenerateKeywords",
  ([23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52], "response schemas, parser, prompt template, a new ChatOpenAI client and the chain are rebuilt on every call; same pattern in the other three subgraph nodes"))
u("examples/google-cloud/cloud-functions/python/main.py::getlogs",
  ([65,66,67,68,69,70], "every line of every decompressed blob is parsed with json.loads before the uri filter is tested"))
u("examples/google-cloud/cloud-functions/python/main.py::get_blobs",
  ([88], "a new storage.Client (credential discovery) per invocation"))
u("examples/embedder-auto-training-evaluation/training-evaluation/train.py::TrainDataset.__getitem__",
  ([27,28,29,30,31,32,33], "`list.pop(0)` plus append rotates positives/negatives in O(n) per item"))
u("examples/embedder-auto-training-evaluation/training-evaluation/train.py::TrainDataset.__init__",
  ([11,12,13,14,15,16,17,18,19,20], "`readlines()` materializes whole files and every document is kept with all fields though only text of referenced ids is used"))
u("examples/mcp-server-app/script/generate_data.py::generate_job",
  ([73,87], "`list(skills.keys())` and `datetime.now()` rebuilt per job"))
u("examples/model-exporting/export_hf_model_from_hf.py::export_model",
  ([43,44,45,46,47,48,49], "tokenizer.save_pretrained writes every tokenizer file and the loop deletes all but tokenizer.json"),
  ([52], "`import onnx` is unused"))

with open("/home/javad/energy-run/sample-apps/step1.jsonl", "w") as f:
    for r in U: f.write(json.dumps(r) + "\n")
print(len(U), sum(len(r["suspicions"]) for r in U))
