import json
s1 = [json.loads(l) for l in open("/home/javad/energy-run/sample-apps/step1.jsonl")]
lines = {(r["unit"], s["label"]): s["lines"] for r in s1 for s in r["suspicions"]}
R = {}
def d(unit, what, *decs):
    out = []
    for dec in decs:
        label, verdict, why = dec[:3]
        ln = dec[3] if len(dec) > 3 else lines[(unit, label)]
        out.append({"label": label, "lines": ln, "verdict": verdict, "why": why})
    R[unit] = {"step": 2, "unit": unit, "what_it_does": what, "decisions": out}
A, X = "accepted", "rejected"
CT = "incremental-search/search-suggestions/count_terms.py"
d(CT+"::process_docs", "sums per-document term counts into `terms` and then, per term, counts how many per-document dicts contain it; the result goes to write_json_file",
  ("a", A, "each per-document dict has unique keys, so incrementing `terms[term]['docs']` inside the existing loop at lines 93-97 gives the same document frequency; the T x D generator scan with its 0/1 lists (lines 100-103) stops happening"),
  ("b", A, "`total_count` is never read; deleting line 92 removes one list build and sum per document"))
d(CT+"::process_doc", "counts n-grams of title and content separately and merges the two dicts by summing counts per term",
  ("a", A, "building the merged dict as a copy of `title_counts` and adding `content_counts` into it keeps the same key order (title keys, then new content keys) and values, without the two key lists or the duplicated `.get` sums for shared terms"))
d(CT+"::count_terms", "slides windows of 1..term_length words over the token list and counts those with no common word",
  ("a", A, "computing one boolean `is_common` list per document turns each window's test into `any()` over a list slice with no lambda calls, and the window is sliced once instead of twice"))
d(CT+"::write_json_file", "builds the update-feed list for every term and writes it with json.dump(indent=2)",
  ("a", A, "`term.replace(' ', '/')` produces the same id without entering the regex engine per term"))
d("incremental-search/search-suggestions/accepted_words.py::process_docs", "collects the set of all tokens from titles and contents of documents that have both",
  ("a", A, "`term_set.update(list)` inserts in C; the per-term bytecode loop and `add` attribute calls stop happening"))
d("news/src/python/evaluate.py::predictions", "for each news id of an impression, finds its hit in the Vespa result and collects its relevance",
  ("a", A, "one dict from news_id to the first matching child (first occurrence kept, missing -> None so None['relevance'] still raises TypeError) replaces a linear scan per id, turning O(n^2) dict reads into O(n)"))
d("news/src/python/metrics.py::dcg_score", "DCG@k: argsorts scores descending, takes the top-k gains and divides by log2 discounts",
  ("a", X, "argpartition would pick a different element among tied scores than the full argsort, changing gains for ties (labels are 0/1, so ties are common in ideal-DCG calls); the list-to-array conversion is needed anyway"))
d("news/src/python/metrics.py::group_auc", "mean of per-impression ROC AUC computed with sklearn",
  ("a", X, "a hand-written AUC would not reproduce sklearn's float summation and its ValueError on single-class impressions; no behaviour-preserving cheaper call exists"))
MD = "news/src/python/mind_data.py::MindData."
d(MD+"sample_valid_data", "builds per-impression tensors (user, news, category, subcategory, entity, labels) for evaluation, keeping only impressions with mixed labels",
  ("a", A, "moving the `sum(labels)` filter before the three comprehensions and the user_index list skips those lists for impressions that are discarded; `random.random()` is still drawn first, so the RNG stream is unchanged"),
  ("b", A, "computing `sum(labels)` once into a local removes the second pass over labels"))
d(MD+"read_data", "parses each impression line into user index, timestamp, news indices and labels appended to the given list",
  ("a", X, "the parsed `timestamp` is stored in each impression dict, which is part of the object's state that callers can see; dropping it changes `train_impressions`"))
d(MD+"add_entities", "appends unique WikidataIds of the given entities to entity_ids",
  ("a", X, "entity_ids is the caller-visible output list and holds a handful of ids; stopping after 2 would change the list contents and a set beside it costs more than scanning a list of a few strings"))
d(MD+"add_impressions", "for one impression appends positive and sampled negative rows to six parallel lists",
  ("a", A, "binding `content = self.news_content[idx]` once per row replaces three dict lookups with one; values appended are identical"))
d("news/src/python/train_cold_start.py::write_embeddings", "writes one TSV line per id with the embedding row formatted to 6 decimals",
  ("a", A, "`embeddings.tolist()` once (a single C conversion, no autograd nodes) and indexing the Python list per id replaces N tensor indexing ops on a grad-requiring tensor plus N small tolist calls; the formatted floats are identical"))
d("news/src/python/train_cold_start.py::save_embeddings", "computes user and news embeddings for all ids and writes them to two TSV files",
  ("a", A, "running the two forward computations under `torch.no_grad()` stops autograd from recording and keeping a graph over all users and news; the values written are the same"))
d("news/src/python/train_cold_start.py::train_model", "trains for `epochs` epochs, evaluating twice and saving embeddings after each epoch",
  ("a", A, "only the final epoch's files survive, so calling save_embeddings once after the loop (guarded for epochs > 0) leaves the same files and removes epochs-1 full embedding computations and writes"))
d("news/src/python/train_cold_start.py::train_epoch", "one pass over the training batches with backprop, printing total and average loss",
  ("a", X, "replacing `total_loss += loss` by `loss.item()` changes the printed text, which currently includes the tensor repr with grad_fn"))
d("news/src/python/train_cold_start.py::read_bert_embeddings_from_file", "reads BERT vectors from a TSV into rows of the embedding matrix for known news ids",
  ("a", A, "binding `news = data_loader.news()` once removes two method calls per line; the per-line float list is kept since numpy assignment needs a sequence anyway"))
d("news/src/python/train_mf.py::write_embeddings", "writes one TSV line per id with the embedding row formatted to 6 decimals",
  ("a", A, "same as train_cold_start.write_embeddings: one `tolist()` of the whole tensor instead of N indexing ops and N tolist calls"))
d("news/src/python/train_mf.py::save_embeddings", "looks up user and news embedding tables for all ids and writes them",
  ("a", A, "wrapping the lookups in `torch.no_grad()` stops autograd graph recording over full tables that are never back-propagated"))
d("news/src/python/train_mf.py::main", "seeds, loads MIND data, trains MF, evaluates on train and dev, saves embeddings",
  ("a", X, "removing the duplicate evaluation removes printed metric lines, which is visible output"))
d("news/src/python/create_bert_embeddings.py::write_embedding", "writes a tab and the comma-separated embedding values with 4 decimals",
  ("a", A, "one `f.write('\\t' + ','.join(...))` produces the same bytes with one write call instead of about two per float"))
d("news/src/python/create_bert_embeddings.py::create_embeddings", "reads news titles and abstracts, runs BERT per document and writes the CLS vector per line",
  ("a", A, "`outputs[0][0, 0].tolist()` converts the 512 needed floats instead of the whole [1, seq, 512] hidden state to nested lists"),
  ("b", A, "`categories` and `subcategories` are never read; dropping the two dict stores per line removes their work"),
  ("c", A, "caching tokenizer and model in a module-level value avoids the second load from disk when main calls the function for dev"))
d("news/src/python/convert_embeddings_to_vespa_format.py::convert_user_embeddings", "reads user embeddings and writes them as a Vespa put feed",
  ("a", A, "`embedding.tolist()` converts once to Python floats (float32 -> float64 is exact), so \"%.6f\" gives identical text without boxing a numpy scalar per element"))
d("news/src/python/convert_embeddings_to_vespa_format.py::convert_news_embeddings", "reads news embeddings and writes them as a Vespa update feed",
  ("a", A, "same per-element numpy scalar boxing as convert_user_embeddings removed by one `tolist()`"))
d("news/src/python/convert_embeddings_to_vespa_format.py::read_embeddings", "parses a TSV of id and comma-separated floats into float32 arrays",
  ("a", A, "`np.fromstring(vector, dtype=np.float32, sep=',')` parses the text in C without creating a list of Python strings; equivalence of float32 rounding to be confirmed by measurement inputs"))
d("news/src/python/convert_to_vespa_format.py::read_impressions_file", "counts impressions and clicks per news id from behaviors.tsv",
  ("a", A, "a plain csv.reader row with `row[4]` (None when short, as DictReader's restval) avoids building a 5-key dict per line; same counts"))
d("news/src/python/convert_to_vespa_format.py::convert_file", "writes each unseen news document as a JSON put with random date and click stats",
  ("a", A, "`output.write(json.dumps(doc))` uses the C encoder and one write per document, producing the same bytes as json.dump's pure-Python iterencode with many writes"))
d("news/src/python/create_category_ctrs.py::read_impressions_file", "accumulates impressions and clicks per category",
  ("a", A, "csv.reader row access instead of a DictReader dict per line, and one `click_map[category]` lookup bound to a local per impression"))
d("news/src/python/create_category_ctrs.py::read_content_file", "maps news id to category for all news lines",
  ("a", A, "csv.reader row access avoids building an 8-key dict per line to read two fields"))
d("news/src/python/vespa_client.py::query_user_embedding", "queries Vespa for a user's embedding vector",
  ("a", A, "a module-level requests.Session reuses the TCP/TLS connection across the thousands of calls made by evaluate.py instead of a handshake each"))
d("text-search/python/sample-queries-and-documents.py::select_documents", "collects docs of selected queries then adds random docs until the target size",
  ("a", X, "if any query doc id is not in `offsets`, the loop can stop before every offset id is drawn, so the result depends on the random draws; returning all ids would change it, and skipping draws changes the RNG stream"))
d("text-search/python/collect_training_data.py::build_dataset", "for each unprocessed query, collects rank features from Vespa and appends them to a CSV, recording processed qids",
  ("a", A, "testing `int(qid)` against a set built once from `processed_queries` is one hash lookup instead of a list scan per query"),
  ("b", X, "moving the processed-file append inside the if changes the file contents the script writes"))
d("text-search/python/extract-msmarco.py::getcontent", "reads a document line by offset and normalizes title and body with regexes",
  ("a", X, "re's internal cache makes a string pattern one dict lookup; the regex passes over the body dominate and are needed"))
d("colbert-long/scripts/convert.py::remove_control_characters", "drops all characters whose Unicode category starts with C",
  ("a", A, "computing the category once per distinct character (set(s)) and deleting the control ones with str.translate removes a Python-level category call and generator step per character; same output"))
d("multilingual-search/ext/evaluate.py::search", "sends the group's query to Vespa and writes TREC-style result lines",
  ("a", A, "`query_group['query'].iloc[-1]` gives the same last query without building a Series per row via iterrows"))
d("msmarco-ranking/python/evaluate_passage_run.py::get_result", "formats the query template and posts it to Vespa, returning hit ids",
  ("a", X, "a 5-key dict rescan per query is noise next to the HTTP round trip and needs `args` state set in main"))
LG = "rag-blueprint/eval/train_lightgbm.py::perform_cross_validation"
d(LG, "loads training CSV, cross-validates LightGBM, writes feature importance, trains a final model and exports it as JSON with original feature names",
  ("a", X, "removing the train set from valid_sets changes the lines printed by log_evaluation and early_stopping, which show train AUC"),
  ("b", A, "one `re.sub` with an alternation of the renamed features and a dict-lookup callback replaces F full passes over the model JSON string; replacements are disjoint quoted tokens so the result is the same"),
  ("c", A, "`stripped_feature_mapping.get(col, col)` replaces a list membership scan per column"),
  ("d", A, "an inverted dict from original to renamed name replaces the nested scan; first match per name is kept as in the break"),
  ("e", X, "DataFrame.nunique applies Series.nunique per column internally, so the same work remains"))
d("rag-blueprint/eval/train_logistic_regression.py::perform_cross_validation", "prints feature statistics, cross-validates a standardized logistic regression, prints metrics and coefficients, saves the expression",
  ("a", A, "computing mean, std, min and max directly per feature skips describe's count and three quantiles (each a partition of the column); printed values identical"),
  ("b", A, "deriving `y_pred` as `classes_[(proba > 0.5)]` reuses the predict_proba pass instead of a second decision_function evaluation"))
d("rag-blueprint/eval/evaluate_match_phase.py::match_semantic_query_fn", "returns the Vespa query body for semantic match evaluation",
  ("a", A, "the YQL string is independent of the arguments; building it once and reusing the string removes the querybuilder tree construction and serialization per query"))
d("rag-blueprint/eval/train_lightgbm.py::strip_feature_prefix", "removes a leading rank_ or match_ from a feature name",
  ("a", X, "called once per feature per run; the regex cache lookup is not measurable work"))
d("examples/in-context-learning/categorize_group.py::inference", "posts one grouping query to local Vespa and parses the returned examples",
  ("a", A, "building only `query_request_bm25_no_group_10` removes 11 unused dict constructions per call"),
  ("b", A, "a module-level requests.Session reuses the connection over the 1000 queries"))
d("examples/in-context-learning/categorize_group.py::get_label", "prompts the LLM with retrieved examples and maps its answer to a label",
  ("a", A, "a set of label names makes each membership test one hash lookup instead of a scan over 77 strings"))
PP = "examples/workshop-ecommerce/preprocess.py::"
d(PP+"process_users", "builds per-user profile and purchase list docs from orders and train order products and writes JSONL",
  ("a", A, "zipping the four column lists (`.tolist()`) gives the same ints without building a pandas Series per purchase row"),
  ("b", A, "`usecols` restricted to the four used columns parses less of orders.csv; the merge uses only those columns"))
d(PP+"process_orders", "per eval_set, aggregates product ids per order, merges with orders and writes JSONL",
  ("a", A, "iterating zipped column lists instead of iterrows avoids a Series per order row"),
  ("b", A, "the filtered frame is only merged, never mutated, so the `.copy()` is a full copy for nothing"),
  ("c", X, "`.agg(list)` still calls a Python callable per group; no work removed"))
d(PP+"process_products", "merges products with aisles and departments and writes product docs",
  ("a", A, "zipped column lists instead of iterrows avoid a Series per product"),
  ("b", A, "a left merge preserves left row order, so merging `df_products.head(limit)` when not full yields the same first rows with less merge work"))
EU = "examples/ecommerce-user-preferences/webapp/app.py::"
d(EU+"load_system_prompt", "reads system_prompt.txt next to the module",
  ("a", A, "caching the file contents in a module-level value read only by this function avoids an open and read per request"))
d(EU+"get_wikipedia_image", "looks up a car image URL on Wikipedia with several API calls, caching hits",
  ("a", A, "a shared requests.Session reuses the TLS connection across the 3+ calls per lookup"))
d(EU+"query_vespa", "builds the Vespa query for preferences and posts it, returning hits",
  ("a", X, "the pretty-printed query is printed output; removing it changes behaviour"),
  ("b", X, "the trace is part of the response returned to the browser; dropping it changes the returned data"))
d("commerce-product-ranking/scripts/evaluate.py::main", "loads ESCI examples and qrels, builds queries and recall strings, and runs a Vespa evaluation",
  ("a", A, "one combined boolean mask avoids two intermediate frames"),
  ("b", A, "one `set_index` reused for both dicts"),
  ("c", A, "a single zip over the three columns into dicts per qid replaces groupby.apply with per-group sub-frames"))
d("use-case-shopping/convert_meta.py::process", "converts one Amazon metadata record into a Vespa put document",
  ("a", A, "accumulating categories_text in a local and building prefixes incrementally avoids re-joining every prefix and reallocating the dict-held string"))
d("use-case-shopping/convert_reviews.py::process", "converts one review record into a Vespa put, or None if it contains \\u001a",
  ("a", X, "the illegal-char check reads the same fields, so building them first is needed; only two int conversions could be saved and they also raise on bad data, which must be preserved"))
d("use-case-shopping/create_suggestions.py::filter", "rejects texts of wrong length or containing any filter token",
  ("a", A, "one precompiled alternation regex search answers whether any of the 33 tokens occurs in a single scan in C instead of 33 Python-level `in` checks"),
  ("b", X, "the dead condition costs one startswith on short strings; nothing measurable"))
d("use-case-shopping/create_suggestions.py::filter_content", "returns True if text starts with an invalid start word",
  ("a", A, "`text.startswith(tuple)` does all prefix tests in one C call"))
IS = "incremental-search/search-as-you-type/feed_to_vespa.py::update_endpoint"
d(IS, "syncs one endpoint: lists indexed ids, optionally deletes them, then deletes ids not in the feed and feeds",
  ("a", A, "after a full removal the index is empty, so diffing against the stale set re-deletes documents; skipping the second removal when removal already ran avoids one curl process per stale id"),
  ("b", A, "`docids_in_feed.update(...)` grows the set in place"))
RF = "feed_to_vespa.py::"
d(RF+"update_endpoint", "syncs one endpoint: lists indexed ids, optionally deletes them, deletes ids not in the feed and feeds via vespa CLI",
  ("a", A, "after removing all indexed docs, recomputing removals from the stale set issues a second DELETE per stale doc; skip when removal ran (prints would change, so the printed lines must be kept)"),
  ("b", A, "`update` in place instead of union allocating a new set per file"),
  ("c", X, "the visit result is printed ('N documents found'); removing it changes output"))
d(RF+"get_feed_docids", "reads a feed file and returns the set of document ids it contains",
  ("a", A, "a set comprehension with the prefix formatted once avoids an intermediate list and a format per doc"))
d(RF+"get_indexed_docids", "visits all docs of an endpoint and returns escaped ids",
  ("a", X, "slicing at rfind instead of replace changes results when the docid text also occurs earlier in the id"))
FS = "feed-split.py::"
d(FS+"split_text", "converts the soup to markdown and splits it at headers into (id, header, text) paragraphs",
  ("a", A, "collecting lines in a list and joining once per section replaces a full copy of the section per line (the first `+` cannot resize in place); same text"),
  ("b", X, "markdownify re-parses with its own parser; converting the html5lib tree directly could produce different markdown"))
d(FS+"xml_fixup", "escapes XML inside highlight xml blocks",
  ("a", X, "a single re.sub with callback would only replace inside matches, while the original replaces every occurrence of the match text in the document; changed behaviour. Added `b`."),
  ("b", A, "skipping `text.replace` when `escape(match) == match` removes a full-document scan per block that has nothing to escape; same result", [39,40]))
d(FS+"what_language", "markdownify callback choosing the code language for a pre element",
  ("a", A, "reading `el.text` once into a local avoids up to two extra descendant walks and joins"))
d(FS+"split_lists", "moves linkable list items into their own containers",
  ("a", X, "the loop mutates the tree while iterating; changing the visit order or skipping revisits can change which items move"))
d("test/pseudo_terminal.py::Log.write", "pexpect log sink: stores the chunk and echoes it when verbose and not a sentinel",
  ("a", X, "with `_filter_pattern` None (run_expect before any run) the original raises TypeError even when not verbose; skipping the match would change that"))
d("test/test.py::process_liquid", "applies liquid site-variable and macro regex substitutions to a command",
  ("a", X, "string patterns hit re's cache; called a few times per page, nothing measurable"))
d("test/test.py::parse_file", "concatenates a file element's children into content",
  ("a", A, "an `isinstance(line, ProcessingInstruction)` check (which also covers XMLProcessingInstruction, as the name test does) avoids building a type repr string per node"))
d("billion-scale-vector-search/app/src/main/python/recall.py::compute_recall_with_distance_ties", "recall@count extended over ties in ground-truth distance",
  ("a", X, "the loop breaks at the first non-tie, usually after one element; a vectorized scan would compute over the whole row"))
d("reverse-image-search/script/feed.py::run", "streams a dataset split, saves images, embeds them with SigLIP and feeds Vespa",
  ("a", A, "decoding the PIL image from the bytes already encoded in memory removes one file read per image; the embedded image is the same decoded JPEG"),
  ("b", A, "one exists() result reused instead of a second stat"))
d("reverse-image-search/script/search.py::_search", "builds a nearestNeighbor query with float and binary vectors and posts it",
  ("a", A, "`astype(np.float32, copy=False)` and int8 `.tolist()` give identical lists without the two array copies"))
TV = "text-video-search/src/python/embedding.py::"
d(TV+"sample_images", "returns evenly spaced frames from a list of frames as an array",
  ("a", A, "stacking only the selected frames (`np.array([images[i] for i in idx])`) gives the same array without materializing every frame and then fancy-indexing a second copy"))
d(TV+"extract_images", "decodes the video at 1 fps and samples frames",
  ("a", A, "computing sample indices from the frame count and keeping only those frames avoids holding every decoded frame"))
d(TV+"VideoFeedDataset.__getitem__", "embeds sampled frames of one video and returns Vespa update docs",
  ("a", X, "batching frames changes CLIP numerics slightly; outputs would not be bit-identical"),
  ("b", A, "hoisting basename/split out of the frame loop and converting only row 0 (`image[0].tolist()`)"))
d(TV+"compute_and_send_video_embeddings", "for each model, builds a dataset over all videos and feeds embeddings",
  ("a", A, "decoding frames once and reusing them across models removes a full video decode per extra model"))
d("text-video-search/src/python/app.py::get_predefined_queries", "fetches the predefined query list over HTTP",
  ("a", X, "caching changes what is shown when the remote file changes"))
d("custom-embeddings/model.py::CustomEmbeddingSimilarity.forward", "MLP score of concatenated query and document embeddings",
  ("a", X, "splitting fc1 changes float summation order, so outputs are not identical; the forward runs once at ONNX export here"))
d("model-inference/src/main/application/models/pytorch_pairwise_ranker.py::PairwiseRankerModel.forward", "pairwise comparison of two query-doc representations",
  ("a", X, "splitting the query half changes float summation order; export-time forward only"))
d("billion-scale-image-search/app/src/main/python/ranker_export.py::Ranker.forward", "dot product of query with each document",
  ("a", X, "matmul uses a different accumulation order, so scores are not bit-identical; only traced once for export"))
d("hypencoder/model2onnx.py::QueryEncoderWrapper._get_weights_and_biases_static", "builds per-query hypernetwork weights for ONNX export",
  ("a", X, "the downstream attention's acceptance of broadcast shapes is unverified, and the cost is in ONNX Runtime, not this Python"))
d("colbert/model2onnx.py::VespaColBERT.__init__", "builds a BERT plus linear ColBERT wrapper",
  ("a", X, "installed transformers skips most init under from_pretrained; the class is constructed once"))
VC = "visual-retrieval-colpali/"
d(VC+"src/backend/colpali.py::SimMapGenerator.gen_similarity_maps", "loads result images, builds the normalized similarity tensor, and yields a base64 heatmap per image and token",
  ("a", A, "`img_pil.copy()` duplicates every decoded page and `processed_images` keeps a list nobody reads; appending the image itself removes one full-image copy per result"),
  ("b", A, "`_blend_image` ignores `img`, so only the size is needed; reading the size from the lazily opened image skips the full RGB decode (open still validates the header)"))
d(VC+"src/backend/colpali.py::SimMapGenerator._prepare_similarity_map_tensor", "scatters Vespa's quantized sim-map cells into a dense tensor",
  ("a", A, "hoisting the hasattr and attribute read out of the cell loop removes two attribute lookups per cell"),
  ("b", A, "collecting indices and values and doing one advanced-index assignment replaces a Python-level tensor __setitem__ per cell"))
d(VC+"src/backend/colpali.py::SimMapGenerator._blend_image", "resizes the sim map, applies viridis, and returns the PNG as base64",
  ("a", A, "`colormap(x, bytes=True)` returns the same uint8 (matplotlib applies (lut*255).astype(uint8)) without the float64 RGBA multiply and cast, and the no-op RGBA convert copy is dropped"))
d(VC+"src/backend/colpali.py::SimMapGenerator.should_filter_token", "returns whether a token matches the filter regex",
  ("a", A, "a class-level compiled pattern skips re.compile's cache lookup (flag check and tuple-keyed dict access) on every call; the match itself is on a short token so the lookup is a large share"))
d(VC+"src/backend/colpali.py::SimMapGenerator.get_query_embeddings_and_token_map", "embeds a query with ColPali and returns idx->token map",
  ("a", X, "convert_ids_to_tokens may not equal tokenize(decode(ids)); behaviour could change"))
d(VC+"src/backend/vespa_app.py::VespaQueryClient.float_to_binary_embedding", "binarizes each query token vector to packed int8 lists, truncated at 64 terms",
  ("a", A, "np.packbits accepts a boolean array; `np.packbits(np.asarray(vector) > 0)` skips the int64 np.where array per vector; identical bits"))
d(VC+"src/backend/vespa_app.py::VespaQueryClient.format_q_embs", "converts the query embedding tensor into {row index: list of floats}",
  ("a", A, "`dict(enumerate(q_embs.tolist()))` does one C conversion instead of creating a row tensor and calling tolist per row"))
d(VC+"src/backend/vespa_app.py::VespaQueryClient.get_result_from_query", "filters stopwords, runs the selected Vespa query and normalizes the result",
  ("a", X, "three splits of a short string per request beside a network query; nothing measurable"),
  ("b", X, "logger.debug returns early at INFO; the loop is a few calls per request"))
d(VC+"src/backend/vespa_app.py::VespaQueryClient.format_query_results", "logs a debug summary and returns the response json",
  ("a", A, "guarding with `logger.isEnabledFor(DEBUG)` skips three dict chains, round and the f-string when debug is off; logged records unchanged"))
d(VC+"prepare_feed_deploy.py::float_to_binary_embedding", "binarizes each patch vector of a page into packed int8 lists",
  ("a", A, "packbits on the boolean mask skips the int64 array from np.where per patch; identical bits"))
d(VC+"prepare_feed_deploy.py::generate_embeddings", "runs ColPali over page images and returns stacked embeddings",
  ("a", X, "passing batch_size changes batched model numerics; needs model and GPU"))
d(VC+"prepare_feed_deploy.py::download_pdf", "downloads one PDF with retries",
  ("a", X, "bounding the loop changes behaviour (the original never terminates on that path); it is a bug fix, not a behaviour-preserving repair"))
d(VC+"vespa_feed_to_hf_dataset.py::save_image", "decodes base64 image data and saves it to a file",
  ("a", X, "writing raw bytes gives a different file than PIL's re-encode"))
d(VC+"refeed_from_hf.py::process_item_for_vespa", "converts a HF dataset row into a Vespa document",
  ("a", X, "rows may carry different key sets and the scan is small next to two JPEG encodes"))
d(VC+"refeed_from_hf.py::pil_to_base64", "JPEG-encodes a PIL image to base64",
  ("a", X, "the encode is the function's contract; seek(0) costs nothing"))
d(VC+"src/main.py::message_generator", "waits for images, streams Gemini's answer as SSE",
  ("a", A, "replacing newlines only in each new chunk and appending gives the same accumulated text without rescanning everything per chunk"),
  ("b", A, "keeping already-opened images across polls avoids re-opening the same files"))
d(VC+"src/main.py::get_and_store_sim_maps", "fetches sim maps, waits for images, and writes PNGs",
  ("a", A, "a generator inside all() short-circuits at the first missing file"),
  ("b", A, "returning PNG bytes from _blend_image (only caller chain) and writing them avoids a base64 encode and decode per map"))
d(VC+"src/main.py::full_image", "returns the full image as a data URI img, fetching from Vespa if missing",
  ("a", X, "the response contract is a data URI; serving a path changes the endpoint's output"))
d(VC+"src/backend/stopwords.py::filter", "removes spaCy stop words from a query",
  ("a", A, "with a blank pipeline `nlp.tokenizer(text)` yields the same Doc; the Language.__call__ wrapper work stops"))
d(VC+"src/frontend/app.py::SearchResult", "renders the search result cards",
  ("a", X, "a second split of a short key per button is noise next to building the FT element tree"))
d("examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/vespa_module/vespa_retriever.py::create_conditions", "parses condition strings into querybuilder conditions",
  ("a", A, "a module-level operators dict built once removes 7 lambda creations and a dict build per call"))
d("examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::subgraph_GenerateKeywords", "asks the LLM for search keywords",
  ("a", A, "building parser, template, client and chain once at module level removes their construction per call"))
d("examples/google-cloud/cloud-functions/python/main.py::getlogs", "streams log lines from GCS blobs filtered by uri",
  ("a", X, "a raw substring prefilter can miss JSON-escaped matches; behaviour could change"))
d("examples/google-cloud/cloud-functions/python/main.py::get_blobs", "lists blobs in a bucket",
  ("a", A, "a module-level storage client avoids credential discovery and client construction per invocation"))
d("examples/embedder-auto-training-evaluation/training-evaluation/train.py::TrainDataset.__getitem__", "returns an InputExample rotating positives and negatives",
  ("a", X, "lists hold a handful of ids; changing them to deques changes dataset state"))
d("examples/embedder-auto-training-evaluation/training-evaluation/train.py::TrainDataset.__init__", "loads corpus and queries",
  ("a", X, "filtering the corpus changes the object's state"))
d("examples/mcp-server-app/script/generate_data.py::generate_job", "generates one random job posting",
  ("a", X, "`list(skills.keys())` on 3-5 keys is negligible and hoisting datetime.now() changes values"))
d("examples/model-exporting/export_hf_model_from_hf.py::export_model", "exports a HF model to ONNX with its tokenizer",
  ("a", X, "needs the model download; writing only tokenizer.json via the backend may differ in content"),
  ("b", A, "the unused `import onnx` costs an import per call; removing it removes that import"))

out = []
for r in s1:
    rec = R[r["unit"]]
    labs = {s["label"] for s in r["suspicions"]}
    got = {x["label"] for x in rec["decisions"]}
    assert labs <= got, (r["unit"], labs, got)
    out.append(rec)
assert len(out) == len(R)
with open("/home/javad/energy-run/sample-apps/step2.jsonl", "w") as f:
    for r in out: f.write(json.dumps(r) + "\n")
print(len(out), sum(1 for r in out for x in r["decisions"] if x["verdict"]==A))
