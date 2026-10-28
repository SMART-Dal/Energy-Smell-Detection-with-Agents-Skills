D={}
def d(unit,what,*dec):
    D[unit]=(what,dec)
A,R="accepted","rejected"
CT="incremental-search/search-suggestions/count_terms.py::"
d(CT+"process_docs","builds per-term corpus counts from per-document count dicts, then a document frequency per term, returned as {term:{term,count,docs}}",
 ("a",A,"the second loop scans all of doc_counts for each distinct term (terms x docs); counts dicts have unique keys, so `term in doc` is true exactly once per (doc, term) pair already visited in the first loop, and `docs` can be incremented there; key order term,count,docs is kept by writing it at creation"),
 ("b",A,"`total_count` on line 92 is bound per document and read nowhere in the function; deleting the sum removes a list and a pass per document"))
d(CT+"count_terms","counts n-grams up to term_length in a token list, skipping windows that contain a common word, returns {ngram:count}",
 ("a",A,"`any(map(lambda word: word in common_words, window))` calls a Python lambda per word of every window; callers pass a set (default set(), read_common_words returns a set), so `not common_words.isdisjoint(window)` does the same test in C and still treats an empty window as passing"),
 ("b",A,"`doc[i:i+win_len]` is sliced at line 60 and again at line 62 in the same iteration; one local removes the second slice"))
d(CT+"process_doc","merges title and content n-gram counts for one document into one dict, or {} when either field is empty",
 ("a",A,"the comprehension iterates `list(title_counts.keys()) + list(content_counts.keys())`, two key lists and their concatenation per document; `itertools.chain(title_counts, content_counts)` yields the same sequence of terms (so the same dict order) without building them"))
d(CT+"read_common_words","reads a stop-word file into a set of stripped lines",
 ("a",A,"`f.readlines()` builds a list of every line, walked once; iterating the handle gives the same lines with one line held at a time"))
d(CT+"write_json_file","writes a Vespa update feed (JSON list) for the term dict, one record per term",
 ("a",A,"`re.sub(r\" \", \"/\", term)` runs the regex engine (cache probe plus match) per term for a single-character replacement; `term.replace(\" \", \"/\")` gives the same string"))
AW="incremental-search/search-suggestions/accepted_words.py::"
d(AW+"read_common_words","reads a stop-word file into a set of stripped lines",("a",A,"readlines() materialises the list that the next loop walks once; iterate the handle"))
d(AW+"process_docs","collects the distinct tokens of title and content of every document with both fields",
 ("a",A,"two per-term `term_set.add` loops where `term_set.update(clean_text(...))` does the same insertion in C; the also-flagged `doc['fields']` lookups sit on the same lines"))
d(AW+"write_to_file","writes the term set to accepted_words.txt, one per line",
 ("a",R,"`Looks like it, but is not` for C9.S1 card 4: the file object already buffers writes, so the per-term write is not one syscall each; the gain from one joined write is small and the card's measurement shows it can go either way"))
MD="news/src/python/mind_data.py::MindData."
d(MD+"sample_valid_data","builds one list of tensor tuples per validation impression that has both clicked and skipped items",
 ("a",A,"three index comprehensions and the user_index list are built before the filter `sum(labels) > 0 and sum(labels) != len(labels)` decides to drop the impression; testing the labels first skips that work for rejected impressions (random.random() call order is unchanged)"),
 ("b",A,"`sum(labels)` is evaluated twice in the condition; it is the same value, and one local removes one pass; same edit region as a but a different edit"),
 ("c",R,"`Looks like it, but is not` for C8.S1: the method draws random.random() per impression and returns fresh tensors the caller owns; caching would need the caller changed and prob<1 makes it non-deterministic"))
d(MD+"add_impressions","appends positive rows and sampled negative rows of one impression to six parallel lists",
 ("a",A,"`self.news_content[idx]` is looked up three times per appended row (lines 189-191 and 198-200); binding it once per row removes two dict lookups each"))
d(MD+"read_data","parses a behaviors file line by line into impression dicts with user index, news indices and labels",
 ("a",A,"strptime on impression_data[2] costs a format parse per line and the result is stored under 'timestamp'; grep of news/src/python finds no reader of that key, so both the parse and the store can be dropped (the dict loses a key nothing reads)"))
d(MD+"read_news","parses a news file into news_content, keeping the first two entity ids per article",
 ("a",R,"the entity JSON of both fields is needed when the title has fewer than two ids, and the order of entity_map insertion depends on parsing both before lookups; skipping the abstract parse needs a branch whose saving depends on data and risks changing lookup_entity_index order only if title yields 2 ids, which is the case it would skip, so the gain is a guess I could not size here"))
d(MD+"sample_training_data","builds the training DataLoader from impressions with per-impression negative sampling",
 ("a",R,"`find_clicked` is deterministic but cheap relative to the random.sample calls that follow, and a precomputed split would have to live on the impression dicts that other methods read; the repair is not confined to this unit and no measurable saving is shown"))
NE="news/src/python/evaluate.py::"
d(NE+"predictions","looks up each requested news id in a Vespa result and returns its relevance in request order",
 ("a",A,"`find_hit` scans hits['root']['children'] linearly per id (n x m); find_hit has no other caller (grep), so one dict {news_id: hit} built per call makes lookups O(1); a missing id still raises (TypeError on None['relevance'] becomes KeyError, so the repair keeps an explicit None lookup via .get)"))
d(NE+"calc_impression","fetches a user embedding and scores the impression's news ids through Vespa",
 ("a",R,"the repeated fetch is one HTTP call per impression and caching by user_id changes what the Vespa server is asked (and the timing the script reports); it needs a cache across calls, a behaviour change the card's near-miss about live sources applies to"))
d(NE+"calc_metrics","reads impressions, samples some, scores each through Vespa, returns auc, mrr, ndcg metrics",
 ("a",A,"the impressions are independent but each makes two blocking HTTP calls one after the other; a thread pool overlaps the waits; the result order is kept by map; energy may rise while time falls, so this needs a measurement to decide, and the unit needs a server"),
 ("b",R,"random.sample(impressions, sample_size) needs the full list to sample from; parsing lazily would change the sampled set for a given seed"))
TC="news/src/python/train_cold_start.py::"
d(TC+"train_epoch","runs one training epoch and prints the summed loss",
 ("a",A,"`total_loss += loss` keeps a graph reference per batch until the print; `loss.detach()` (or .item()) frees each graph after backward; the printed value is the same number"))
d(TC+"train_model","trains for `epochs` epochs, evaluating and saving embeddings each epoch",
 ("a",R,"the per-epoch evaluation and saving are the author's reported progress and the saved files are an observable output after every epoch (a crash leaves the latest files); removing them changes printed output and files"))
d(TC+"eval_model","scores every validation impression with one forward pass each and prints four metrics",
 ("a",A,"the forward pass runs once per impression on 10-100 rows; but batching changes float accumulation in some layers and the metric inputs per impression; metrics would stay close but not provably identical, so I accept only for the record and defer measurement"))
d(TC+"read_bert_embeddings","fills a news x 512 matrix from two embedding files and returns it as a FloatTensor",
 ("a",A,"np.zeros defaults to float64, so the matrix is twice the size and torch.FloatTensor converts it again; dtype=np.float32 gives the same float32 tensor (values are rounded to float32 on conversion either way)"))
d(TC+"read_bert_embeddings_from_file","copies embedding rows from a TSV into rows of a preallocated array",
 ("a",A,"`data_loader.news()` is a method call that returns the same dict, called twice per line; one local before the loop removes both calls"),
 ("b",R,"`[float(i) for i in s.split(',')]` is assigned into a numpy row; np.array(..., dtype=float32) would round differently before the float64 array stores it, so values could differ in the last bits"))
d(TC+"save_embeddings","writes user and news embeddings of the current model to two TSV files",
 ("a",A,"the forward passes run with autograd on, so a graph is built for the full user and news tables; `torch.no_grad()` leaves values unchanged and `.tolist()` output identical"))
d(TC+"write_embeddings","writes one TSV line per id with six-decimal formatted embedding values",
 ("a",A,"`embeddings[index].tolist()` indexes the tensor once per id; `embeddings.tolist()` once and list indexing gives identical numbers with less per-row tensor overhead"))
TM="news/src/python/train_mf.py::"
d(TM+"train_epoch","runs one MF training epoch and prints the summed loss",("a",A,"same retained-graph accumulation as train_cold_start.train_epoch: `total_loss += loss` holds every batch graph; detach before adding"))
d(TM+"main","sets the seed, loads data, trains the MF model and evaluates it",
 ("a",R,"train_model evaluates only when epoch % 10 == 9 on an unchanged model at the last epoch, but main's two eval_model calls also print the metrics the author reports at the end; dropping them removes printed output"))
d(TM+"eval_model","scores every validation impression with one forward pass each and prints four metrics",("a",R,"same as train_cold_start.eval_model: a batched forward pass is not guaranteed to reproduce the metrics exactly, and the unit's inputs need torch models built from data files"))
d(TM+"save_embeddings","writes user and news embeddings of the MF model",("a",A,"forward-free here: the embedding lookups run with autograd enabled, so wrapping in torch.no_grad() builds no graph; output identical"))
CB="news/src/python/create_bert_embeddings.py::"
d(CB+"create_embeddings","embeds every news title+abstract with a BERT model and writes the CLS vector per document",
 ("a",A,"model(**tokens) runs with autograd enabled, so every document builds a graph that is dropped; `torch.no_grad()` leaves outputs identical"),
 ("b",A,"`outputs[0].tolist()[0][0]` converts the whole seq_len x 512 tensor to nested lists to keep one row; `outputs[0][0, 0].tolist()` converts 512 numbers; same values"),
 ("c",R,"the two from_pretrained calls happen once per create_embeddings call and main calls it twice; hoisting would change the function's signature and caller, and the load is a one-off cost next to per-document inference"))
d(CB+"write_embedding","writes a tab then comma-separated four-decimal values of one embedding",("a",A,"512 values written with two f.write calls each, 1000 calls per document; one joined string is one call; the file object buffers, so the saving is the per-call Python overhead"))
CV="news/src/python/convert_to_vespa_format.py::"
d(CV+"convert_file","streams news rows into a JSON array as documents with random dates and click counts",("a",A,"json.dump writes through the pure-Python iterencode and many small writes; `output.write(json.dumps(doc))` uses the C encoder and writes the same text (same default separators)"))
d(CV+"generate_random_date","returns a random date in Nov 2019 as an int yyyymmdd",("a",R,"a lookup table indexed by a different random draw would consume the RNG differently and change the generated values for a given seed; randint's output must be kept"))
CE="news/src/python/convert_embeddings_to_vespa_format.py::"
d(CE+"convert_user_embeddings","rewrites user embeddings as Vespa put operations",("a",R,"the strings are re-rendered from float32; passing the original text through can differ where a six-decimal value is not exactly representable after float32 rounding, so output bytes could change"))
d(CE+"convert_news_embeddings","rewrites news embeddings as Vespa update operations",("a",R,"same: float32 round trip then %.6f is not guaranteed to reproduce the input text"))
d(CE+"read_embeddings","reads an embeddings TSV into a dict of float32 arrays",("a",R,"the dict is consumed once by a single writer and holding all rows is how the callers are written; streaming needs the callers changed and is outside this unit's contract"))
VC="news/src/python/vespa_client.py::"
d(VC+"query_news","posts a nearest-neighbour query to Vespa and returns the JSON",
 ("a",R,"a Session needs a module- or caller-level object shared across calls, which changes the signature or a module global; the unit needs a live Vespa to run"),
 ("b",R,"`select *` is part of the query text the server sees and callers read news_id and relevance only; changing the query changes the request, which is the unit's contract with Vespa"))
d(VC+"query_user_embedding","fetches one user's embedding vector from Vespa",("a",R,"same reason: connection reuse needs shared session state beyond the unit"))
LG="rag-blueprint/eval/train_lightgbm.py::"
d(LG+"perform_cross_validation","cross-validates a LightGBM ranker, writes model JSON, feature importances and metrics",
 ("a",A,"the model JSON string is scanned by one re.sub per feature, then parsed again; renaming the features in the dumped dict once is linear in the feature count instead of feature count times the JSON size"),
 ("b",A,"`models` is appended to per fold and never read afterwards (grep in the function), so all fold boosters stay alive to the end"),
 ("c",R,"valid_sets=[lgb_train, lgb_val] also drives the log_evaluation line printed every 100 rounds; dropping the train set changes the printed output"))
d("rag-blueprint/eval/train_logistic_regression.py::perform_cross_validation","cross-validates a logistic regression and writes coefficients and metrics",
 ("a",A,"X[feature].describe() sorts for quartiles that are never printed; the same four stats from one agg call"),
 ("b",A,"predict() and predict_proba() each compute the decision function; y_pred = (proba > 0.5) is identical for binary classes"))
FS="feed-split.py::"
d(FS+"what_language","chooses a code-fence language from a bs4 code element's text",("a",A,"`el.text` is a property that joins all descendant strings on every access, up to three times; one local gives the same string"))
d(FS+"split_text","splits a bs4 document into (id, header, text) sections via markdown",("a",A,"`text = text + '\\n' + line` makes a new string per line; the local is unaliased so CPython may resize in place, but joining a list of lines at flush gives the same text; `Decide which form fits` card: measure"))
d(FS+"xml_fixup","XML-escapes the body of every highlight-xml block in a document string",("a",A,"`text.replace(match, escaped)` rescans the whole document for each match; one re.sub with a function does a single pass (identical when blocks differ; when a block text recurs elsewhere the original also replaces those, which the repair must reproduce by using the same replace on distinct matches)"))
d(FS+"table_header_row","finds the thead first row for a table row",("a",R,"called only for rows that carry an id paragraph, not per row of the table, and the lookup walks one parent; hoisting would need changes in split_tables"))
d(FS+"main","converts a JSON feed of HTML docs to paragraph docs and writes paragraph_index.json",
 ("a",A,"json.dump chunked writes through the pure-Python encoder; json.dumps then write gives the same text"),
 ("b",R,"the eight passes are order-dependent string rewrites on small paragraphs; merging them changes results, so no repair that preserves output exists"),
 ("c",A,"re.sub with literal patterns inside the per-paragraph loop pays a cache probe each; precompiled module patterns remove it"))
FV="feed_to_vespa.py::"
d(FV+"update_endpoint","syncs a Vespa index with feed files by deleting stale documents then feeding",
 ("a",R,"setting docids_in_index to empty after the full removal would change which 'To Remove' lines and counts are printed; printed output is part of the contract"),
 ("b",A,"`docids_in_feed.union(...)` creates a new set of all ids so far per file; `update(...)` grows the one set in place; result and later uses identical"),
 ("c",R,"docids_in_index is needed whenever either flag is set; when both are false the function still prints the found count, which is output"))
d(FV+"vespa_remove","sends one HTTP DELETE per document id",("a",R,"each delete is a distinct request through a shared Session, and concurrency needs a thread pool and ordering decisions; needs a live Vespa, and no repair is established without a measurement"))
d(FV+"get_docs","loads a JSON file",("a",R,"the function is never called in feed_to_vespa.py (grep) and the repair is a with-block on a one-shot open; it does not change the work in a way a measurement would show"))
d(FV+"get_feed_docids","returns the set of document ids in a feed file for the doc type",("a",A,"`set([listcomp])` builds a throwaway list per branch; a set comprehension builds the set directly"))
SA="incremental-search/search-as-you-type/feed_to_vespa.py::"
d(SA+"update_endpoint","syncs a Vespa index with feed files by deleting stale documents then feeding",
 ("a",R,"same as the root script: the repeated delete is visible in printed output and counts"),
 ("b",A,"`union` copies the set every file; `update` in place"),
 ("c",R,"update_endpoint parses each feed file twice (ids, then vespa_feed's get_docs); reusing the parse needs vespa_feed's signature changed and is outside what one measurable edit here covers, and the unit needs curl and a server"))
d(SA+"vespa_post","posts one document through a forked curl",("a",A,"each document forks a curl process with a fresh connection; a requests.Session POST to the same URL removes the fork and reconnect, if requests is acceptable here (it is used in the sibling script)"))
d(SA+"vespa_delete","deletes one document through a forked curl",("a",A,"same fork-per-call cost as vespa_post"))
d("examples/in-context-learning/categorize_group.py::inference","queries Vespa for examples for one text and parses the grouped result",
 ("a",A,"twelve of thirteen request dicts, each embedding `text`, are built and dropped on every call; only query_request_bm25_no_group_10 is posted"),
 ("b",R,"a Session would be a module-level object; the unit as written is module-bound and needs Vespa and Ollama, no measurement possible"))
d("examples/in-context-learning/categorize_group.py::get_label","asks an LLM to label a text given examples and normalises the answer",("a",R,"the membership test sits behind a network call to an LLM that costs orders of magnitude more than a 77-element list scan"))
PP="examples/workshop-ecommerce/preprocess.py::"
d(PP+"process_users","aggregates Instacart train orders per user and writes users.jsonl",
 ("a",A,"iterrows builds a Series per purchase row, then four int() casts; `to_dict('records')` on the four columns gives the same ints once the columns are cast"),
 ("b",R,"in sample mode only `limit` users are written, but selecting them first changes the groupby ordering inputs and the printed totals use len(user_groups); not one local edit"),
 ("c",A,"read_csv with usecols for order_id,user_id,order_dow,order_hour_of_day and product_id avoids parsing unused columns; output identical"))
d(PP+"process_products","merges products with aisles and departments and writes products.jsonl",
 ("a",R,"the printed count uses len(df_merged) in full mode and the merge sits before the limit; head(limit) before the merge is valid, but rows lost by how='left' ordering are preserved, and the saving is on a dataset file this repo does not hold"),
 ("b",A,"iterrows builds a Series per row to read four fields; itertuples or zip over columns builds none"))
d(PP+"process_orders","aggregates order products per order and writes orders_*.jsonl per eval set",
 ("a",A,"`.agg({'product_id': lambda x: list(x)})` runs a lambda per group; `.agg(list)` on the column gives the same lists"),
 ("b",R,"orders.csv was also read by process_users, but the two are separate calls from main and sharing the frame changes both signatures"),
 ("c",A,".copy() of a filter result nothing later mutates (the merge below produces a new frame)"),
 ("d",A,"iterrows builds a Series per order row"))
CT2="text-search/python/collect_training_data.py::"
d(CT2+"build_dataset","queries Vespa per MS MARCO query and appends rank features to a CSV, tracking processed ids",
 ("a",A,"processed_queries is a list from load_processed_queries; `int(qid) not in processed_queries` scans it per query; built once per call and read only here, so a set of the same ints is a sole-use change"),
 ("b",R,"the append handle reopen per query is the author's resume point after a crash; one handle would lose ids on interruption"),
 ("c",R,"the processed-id write happens for every query on purpose (queries without the relevant hit must not be retried); it is not a redundant store"))
d(CT2+"get_features","POSTs one query to Vespa and returns hits",("a",R,"a Session is shared state beyond the unit and a server is needed"))
d(CT2+"load_processed_queries","reads processed query ids from a file into a list",("a",A,"open() without a with block leaks the handle if int() raises; a with block releases it (and `Looks like it, but is not` does not apply: the handle is not returned)"))
EM="text-search/python/extract-msmarco.py::"
d(EM+"load_msmarco_queries","loads all MS MARCO train queries, cleaned and lowercased, into a dict",("a",R,"the returned dict's key set is part of the function's result and `qrel` is passed as the set of wanted ids only by main; filtering would change the return value"))
d(EM+"extract_documents","copies each document's cleaned line to docs.tsv and records its offset",("a",A,"`out.tell()` on a text-mode file computes an opaque cookie per document and can force a flush; a running byte count gives the same offsets only if text offsets equal byte offsets, which holds for the utf-8 text this writes; kept as a finding with the offset semantics to check"))
d(EM+"getcontent","reads one document line by offset, cleans title and body with four regex passes, formats a TSV line",("a",A,"four re.sub calls with string patterns each pay a module cache probe; precompiled module patterns do the same substitutions"))
SQ="text-search/python/sample-queries-and-documents.py::"
d(SQ+"select_documents","adds random documents until the set reaches the target size",("a",A,"rejection sampling with random.choice slows as the set approaches the pool size; `random.sample` of the remaining ids would give a different draw sequence, so outputs differ for a seed, which the contract (a random sample) allows only if the RNG state is not part of it; I accept for the record with that doubt"))
d(SQ+"load_queries","loads queries and applies a punctuation-stripping regex to each",("a",R,"the query file was written by extract-msmarco with the same regex, but this script can be pointed at any queries.tsv; removing the cleaning changes its output for other inputs"))
d(SQ+"write_document_offsets","writes sampled docid/offset pairs in set order",("a",R,"sorting by offset changes the order of the output file, which convert-to-vespa-format reads in file order; the order of the written lines is part of the output"))
d("text-search/python/convert-to-vespa-format.py::main","reads sampled docs by offset and writes a Vespa JSON feed",("a",A,"json.dump per document uses the pure-Python encoder with many writes; json.dumps then write is the same text"))
EMB="text-video-search/src/python/embedding.py::"
d(EMB+"extract_images","decodes a video at 1 fps and returns the sampled frames",("a",A,"every frame is decoded into a list and sample_images keeps number_frames of them; reading the sampled indices needs the frame count first (reader.count_frames), which the card marks as a different decomposition; keep as a finding"))
d(EMB+"sample_images","samples equally spaced frames from a list",("a",A,"`np.array(images)[idx]` stacks every frame into one array before indexing; stacking only `[images[i] for i in idx]` copies number_to_sample frames; same array"))
d(EMB+"VideoFeedDataset.__getitem__","embeds the frames of one video and returns Vespa feed dicts",("a",A,"encode_image is called per frame with batch size 1; stacking preprocessed frames into one tensor and encoding once gives the same embeddings up to float accumulation; the model is CLIP in eval mode, so I accept with the numeric doubt noted"),("b",A,"`ntpath.basename(video_file_name)` and the split are recomputed per frame from a value that does not change in the loop"))
d("text-video-search/src/python/app.py::get_predefined_queries","downloads a list of example queries over HTTP",("a",A,"it is called on each Streamlit rerun and nothing caches the download; `st.cache_data` keeps one copy, the card's measure-first case since the host fetch is cached below"))
