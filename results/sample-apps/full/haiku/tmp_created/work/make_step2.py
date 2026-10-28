import json
step1 = [json.loads(l) for l in open("/home/javad/energy-run/sample-apps/step1.jsonl")]
A, R = "accepted", "rejected"

# unit -> (what_it_does, {label: (verdict, why)}, extra_suspicions)
D = {}
def d(unit, what, decs, extra=None):
    D[unit] = (what, decs, extra or [])

d("incremental-search/search-suggestions/count_terms.py::process_docs",
  "Sums per-document term counts into one dict of {term, count, docs}, then counts in how many documents each term appears by scanning every document's count dict once per term.",
  {"a": (A, "The `docs` count is the only use of the second pass (lines 100-103): for each of the T terms it runs `term in doc` over all D count dicts, so cost is T x D probes. Each count dict has unique keys, so incrementing `docs` once per (doc, term) inside the loop at 93-97 gives the same count in one pass. The new dict keeps the key order term, count, docs. Mechanism: T x D membership probes disappear."),
   "b": (A, "`total_count` (line 92) is bound and never read; the sum over each document's counts is a full pass with no consumer. Deleting the line changes nothing the function returns. Mechanism: one sum over every entry of every count dict is no longer computed. Different edit from (a), measured separately.")})

d("incremental-search/search-suggestions/count_terms.py::count_terms",
  "Enumerates every word window of length 1..term_length in a token list, skipping windows that touch a common word, and counts the joined phrases.",
  {"a": (A, "`not any(map(lambda word: word in common_words, window))` builds a lambda and a map object for every window and calls the lambda per word. `common_words.isdisjoint(window)` is true exactly when no word is in the set, and it runs in C. `common_words` is a set at both call sites (default `set()`, and `read_common_words` returns a set). Mechanism: per-word Python calls become one C call per window."),
   "b": (A, "The window `doc[i : i + win_len]` is sliced at line 60 and again at line 62 when the window is kept. Binding it once removes one list allocation per kept window. Different edit from (a). Expected to be small, so it is measured only if a slot is free.")})

d("incremental-search/search-suggestions/count_terms.py::write_json_file",
  "Builds one Vespa feed entry per term, with the term's phrases from get_phrases, and writes the list as indented JSON.",
  {"a": (A, "`re.sub(r\" \", \"/\", term)` runs once per term and is a literal single-character replacement. `term.replace(\" \", \"/\")` returns the same string. Mechanism: the regex engine's entry and scan are replaced by a str method. Output is byte-identical.")})

d("incremental-search/search-suggestions/accepted_words.py::process_docs",
  "Collects the set of distinct cleaned words from the titles and contents of all documents that have both fields.",
  {"a": (A, "Two loops call `term_set.add(term)` once per term. `term_set.update(clean_text(...))` adds the same elements in one C call per text. The resulting set is identical, and so is the iteration order that write_to_file later sees. Mechanism: per-element Python method calls become one bulk call per text.")})

d("incremental-search/search-suggestions/accepted_words.py::write_to_file",
  "Writes every term of the set, one per line, to the accepted-words file.",
  {"a": (A, "`f.write(term+\"\\n\")` makes one Python-level call per term; the file object already buffers the bytes. Building one string with `\"\".join` and writing it once gives the same bytes and the same iteration order over the same set. Mechanism: vocabulary-size Python calls become one. The gain is in call overhead only, since the buffered write syscalls are the same.")})

d("news/src/python/train_cold_start.py::read_bert_embeddings",
  "Allocates a [news count x 512] float64 array, fills it from the train and validation embedding files, and returns it as a float32 torch tensor.",
  {"a": (A, "`np.zeros([n, 512])` is float64, so the buffer is twice the size it needs. The values are stored into it from Python floats (double precision) and then `torch.FloatTensor` casts the whole array to float32 on line 167. With `dtype=np.float32` the store rounds each double to float32 once, which is the same rounding the cast performs, so the tensor values are identical. Mechanism: half the allocation and one full-array conversion pass are removed.")})

d("news/src/python/train_cold_start.py::read_bert_embeddings_from_file",
  "Reads one embeddings file line by line and writes each news item's 512-value vector into the shared embedding array.",
  {"a": (A, "`data_loader.news()` is called twice per line (lines 180 and 183); it returns the same dict each time. Binding it once before the loop removes one method call per line. The loop body otherwise does the same work, so the saving is one call per line, small next to float parsing. Deferred unless a slot is free.")})

d("news/src/python/train_cold_start.py::train_epoch",
  "Runs one epoch of forward and backward passes over the sampled batches and prints the summed loss and the average.",
  {"a": (R, "The loss is printed as a tensor: `total_loss` is a tensor with grad_fn after the first `+=`, and the print on line 101 shows its repr. Replacing it with `loss.item()` changes the printed text, so the printed output of the unit changes. The graph retention is real, but the repair cannot keep the printed output identical, and the contract requires identical printed output.")})

d("news/src/python/evaluate.py::read_impressions_file",
  "Parses every row of an impressions file into a dict of user, candidate news ids and labels, and returns the full list.",
  {"a": (R, "The only caller, calc_metrics (line 86), samples the list with random.sample. Sampling inside this function would change its return value, so calc_metrics would have to change as well. calc_metrics is not on the step-1 list, and no unit can be added now, so the repair cannot be written within the list. Rejected for scope, not for the mechanism.")})

d("news/src/python/evaluate.py::find_hit",
  "Returns the child of a Vespa hits response whose news_id matches, by a linear scan of the children.",
  {"a": (R, "The quadratic work is the loop in predictions (lines 64-65), which calls this once per candidate. A change inside find_hit alone, such as building an index per call, would rebuild the index for every candidate and save nothing. The repair needs predictions to build the index once, and predictions is not on the list. Rejected for scope.")})

d("news/src/python/metrics.py::ndcg_score",
  "Returns the normalised discounted cumulative gain of a score ordering against true labels, by dividing DCG by the ideal DCG.",
  {"a": (R, "The ideal DCG sorts the true labels once per call, and it is not repeated inside one call. Reusing it across the k=5 and k=10 calls would need a cache keyed on the label array, which is module state the function does not have. Each group has about 15 labels, so the sort costs microseconds. Rejected as negligible, and a cache would change the module's state.")})

d("news/src/python/mind_data.py::MindData.read_data",
  "Parses each impression line into a user index, a timestamp, a history set and labelled candidate indices, and appends a dict per line to impression_list.",
  {"a": (A, "`datetime.strptime` runs on every line (line 93), and its result is stored under 'timestamp' (line 101). A repository-wide search finds no reader of that key: the only other 'timestamp' uses are the field_list of the separate readers in evaluate.py, convert_to_vespa_format.py and create_category_ctrs.py, which parse their own files. The list is self.train_impressions and self.valid_impressions, which sample_training_data and sample_valid_data read by user, news and label only. Removing the parse and the key saves one strptime per line. Sole-reader evidence is the grep over news/src/python."),
   "b": (A, "`self.lookup_user_index(user_id)` on line 100 is a one-line wrapper around `lookup_index`, called once per line. Calling `self.lookup_index(user_id, self.user_map)` directly removes one frame per line. Deferred: the saving is one call per line, next to a strptime on the same line.")})

d("news/src/python/mind_data.py::MindData.read_news",
  "Parses each news line into category, subcategory and entity indices and stores them in news_content.",
  {"a": (R, "add_entities walks every title and abstract entity, and line 73 keeps the first two. Stopping early would need the walk inside read_news rewritten. The walk covers a handful of entity records per article, and json.loads on the same line already costs more. Rejected as negligible.")})

d("news/src/python/mind_data.py::MindData.sample_valid_data",
  "Builds the validation batches for one evaluation, one per impression that survives a random draw against prob.",
  {"a": (R, "The function draws one random.random() per impression. Caching its result would skip those draws, so the module-level random stream differs afterwards, and negative sampling in later epochs would draw different values. The repair changes module state, and the output of later calls changes with it. Rejected.")})

d("text-video-search/src/python/embedding.py::sample_images",
  "Picks equally spaced frames from a list of decoded frames and returns them as one numpy array.",
  {"a": (A, "`np.array(images)[idx]` converts the whole list, copying every decoded frame, and then keeps only len(idx) of them. Indexing the list first, `np.array([images[i] for i in idx])`, copies only the kept frames. The indices, dtype and shape of the result are unchanged. The else branch still needs the full array, so it is untouched. Mechanism: the copy of the frames that are dropped is removed.")})

d("text-video-search/src/python/embedding.py::extract_images",
  "Decodes every frame of a video at 1 fps into a list, then keeps number_frames equally spaced frames through sample_images.",
  {"a": (R, "The decode work is the same before and after: every frame is still decoded sequentially. The saving would be the list held in memory. The repair that avoids holding the list needs the total frame count before decoding, and imageio's reader gives it only after decoding, while random access re-decodes from keyframes. The energy effect is not established, and no real video is available to test it. Rejected for mechanism.")})

d("colbert-long/scripts/convert.py::remove_control_characters",
  "Returns the string with every Unicode control, format, surrogate, private-use and unassigned character removed, by testing each character's category.",
  {"a": (A, "The generator calls unicodedata.category for every character and joins the kept ones. A dict translation table mapping each category-C code point to None, built once at module load, lets str.translate do the same removal in one C pass with a dict lookup per character. The table covers every code point the original tests, including unassigned ones, so the output is identical. Mechanism: a Python-level call and generator step per character are replaced by one C call. The table costs about a fraction of a second at import, which is outside the measured call.")})

d("feed-split.py::split_text",
  "Converts an HTML soup to markdown and splits it into (id, header, text) sections at each heading line.",
  {"a": (A, "`text = text + \"\\n\" + line` copies the accumulated section on every line. Collecting the pieces in a list and joining them gives the same string. The `if text:` test on line 91 is equivalent to a non-empty list, because every piece is at least one character. Mechanism: quadratic copying of the section per line becomes one join per section. Requires tiktoken, which was installed into the venv for this run.")})

d("text-search/python/extract-msmarco.py::extract_documents",
  "Writes each document's cleaned content to the documents file and records the byte offset of each document in the offset file.",
  {"a": (A, "`out.tell()` runs once per document (line 85). On a text file, TextIOWrapper.tell() flushes the write buffer before reporting the position, so each document forces a write of the buffer to the OS. Keeping a running byte count (the UTF-8 length of each string written, which equals the byte position because the file is opened with encoding utf8) gives the same offsets without the flush. Mechanism: one flush and write syscall per document is removed. Output bytes and offsets are identical.")})

d("text-search/python/convert-to-vespa-format.py::main",
  "Reads each document at its recorded offset in the documents file and writes one Vespa feed entry per document as JSON.",
  {"a": (A, "`json.dump(doc, out)` writes the encoded document in several small chunks, each a separate write call on the text file (the pure-Python encoder path). `out.write(json.dumps(doc))` writes the same text in one call. The encoder settings are the defaults in both, so the output is byte-identical. Mechanism: several write calls per document become one.")})

d("text-search/python/sample-queries-and-documents.py::select_documents",
  "Adds the documents of the selected queries to a set, then draws random documents until the set reaches min(number of documents, documents_to_generate).",
  {"a": (A, "`min(len(docids), documents_to_generate)` is recomputed on every test of the while loop (line 61). Its value cannot change, so binding it once before the loop gives the same loop and the same random draws. Mechanism: one min call per iteration is removed. Small, measured only if a slot is free.")})

d("text-search/python/collect_training_data.py::build_dataset",
  "For each query, asks Vespa for features of the relevant document and of random hits, annotates them, appends them to the output CSV, and records the query id as processed.",
  {"a": (A, "`int(qid) not in processed_queries` scans the list read on line 71 once per query. A set built once from that list gives the same membership answer. The list is still used for len() on line 72. Mechanism: the linear scan becomes a hash probe."),
   "b": (R, "Opening the processed-queries file once outside the loop would change when the file is created on an empty input, and would change the file's state if an error stopped the loop midway. The file is written once per query in append mode, so the saving is an open and close per query on a path that already makes HTTP calls. The contract on created files would change. Rejected.")})

d("rag-blueprint/eval/train_lightgbm.py::perform_cross_validation",
  "Cross-validates a LightGBM binary classifier over stratified folds, exports the final model with feature names restored, and writes importance and metrics.",
  {"a": (R, "lgb.log_evaluation(period=100) prints every validation set's metric, including the train set's AUC. Removing lgb_train from valid_sets removes that printed line, so the printed output of the unit changes. The per-round AUC pass is real, but the repair cannot keep the printed output identical."),
   "b": (R, "Each fold trains on different rows, and the final model on different columns. The binning of one fold cannot be reused for another without Dataset.subset, which can change the bin boundaries and so the model. The reuse changes the model output, so the repair is not equivalent. Rejected.")})

d("visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.float_to_binary_embedding",
  "Converts each float query-token vector to a packed int8 bit vector, and stops at MAX_QUERY_TERMS with a warning.",
  {"a": (A, "`np.where(np.array(vector) > 0, 1, 0)` builds an int64 array of 128 elements per vector before packbits, and packbits only reads whether each element is nonzero. Passing the boolean array to packbits gives the same bytes. Mechanism: one int64 intermediate per vector is removed. The method is blocked here, because constructing VespaQueryClient calls wait_for_application_up.")})

d("visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.gen_similarity_maps",
  "Yields, for each image and each kept query token, a base64 PNG of the image blended with that token's normalised similarity map.",
  {"a": (A, "Each image is decoded to RGB and copied (line 86), and the copy is used only through `img`, which _blend_image never reads. The size comes from the decoded image. `Image.open(...).size` reads the header only, so the decode and the copy can both go. The exception wrapping in _load_image must be kept for bad inputs. Blocked here: SimMapGenerator.__init__ downloads vidore/colpali-v1.2."),
   "b": (A, "`self.should_filter_token(token)` depends only on the token, yet it runs for each (image, token) pair (line 99). Building the kept-token list once before the image loop gives the same yields in the same order. Blocked here for the same reason as (a).")})

d("visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator._prepare_similarity_map_tensor",
  "Builds a [maps x query tokens x patch x patch] tensor from the Vespa quantised similarity cells.",
  {"a": (A, "`hasattr(self.processor, \"image_seq_length\")` and its lookup run for every cell (lines 147-150), though self.processor does not change inside the loop. Hoisting the value above the loops gives the same branch for every cell. Blocked here: the method needs a SimMapGenerator, whose __init__ downloads the ColPali model."),
   "b": (A, "Each cell is written with one scalar tensor index assignment (lines 154-159), which is one torch dispatch per cell. Collecting indices and values and writing them with one advanced-index assignment does the same writes in one call. Mechanism: per-cell dispatch is replaced by one bulk write. Blocked here for the same reason as (a).")})

d("visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.should_filter_token",
  "Tests a token against a fixed regular expression and returns whether to drop it.",
  {"a": (R, "re.compile is called on each call, but the re module caches compiled patterns, so the per-call cost is one cache probe. The repair would move the compile to module scope, which saves that probe only. Rejected as negligible.")})

d("visual-retrieval-colpali/prepare_feed_deploy.py::float_to_binary_embedding",
  "Converts a dict of float query embeddings to packed int8 bit vectors, one list per key.",
  {"a": (A, "Per vector: np.array, np.where to int64, packbits, astype int8, tolist. packbits accepts the boolean array directly, and its output is the same bytes, so the where and the int64 intermediate are removed. The same mechanism as the vespa_app method. Measured only if the module loads in the venv.")})

d("visual-retrieval-colpali/prepare_feed_deploy.py::generate_embeddings",
  "Runs the model over the page images in a DataLoader and returns the stacked embeddings as one numpy array.",
  {"a": (A, "The DataLoader is built without batch_size, so PyTorch uses its default of 1, and the batch_size parameter (line 534, documented as default 2) is ignored: the model runs one page per forward pass. Passing batch_size=batch_size makes it run batches. Equivalence is not guaranteed: the processor pads a batch to the largest page, so the per-page embeddings can change numerically. Verification decides. Blocked if the ColPali weights cannot be loaded.")})

d("examples/workshop-ecommerce/preprocess.py::process_products",
  "Merges products with aisles and departments and writes one Vespa document per product, stopping after limit rows in sample mode.",
  {"a": (A, "`df_merged.iterrows()` builds one pandas Series per row, a boxed object for every value, to read four fields. `to_dict('records')` yields the same values as Python objects per row, and the loop body is unchanged. The columns are all object or int64, so iterrows does not upcast. Mechanism: per-row Series construction is removed. Measured in full mode, because sample mode breaks after ten rows.")})

d("examples/workshop-ecommerce/preprocess.py::process_users",
  "Groups train order-products by user, builds each user's product-count profile and purchase list, and writes one Vespa document per user.",
  {"a": (A, "`user_purchases_df.iterrows()` builds a Series for every purchase row of every user (line 202). Iterating `to_dict('records')` gives the same field values, and the int() conversions are unchanged. Mechanism: per-row Series construction is removed. Measured in full mode."),
   "b": (A, "In sample mode the whole order-products table is merged with orders and grouped before the write loop stops at limit users (lines 181-193). groupby iterates users in ascending user_id, so the first limit users are the limit smallest ids, and a filter to those users before the merge would give the same output. Deferred: it needs a filter that keeps the same orders and rows, which is more code than the other repairs and is not verified here.")})

d("examples/workshop-ecommerce/preprocess.py::process_orders",
  "Reads orders, filters them by eval_set, aggregates each order's products, and writes one Vespa document per order.",
  {"a": (R, "orders.csv is also read in process_users. Removing the second read needs main to pass one frame to both functions, which changes the signatures of two units and main, and main is not on the list. Rejected for scope."),
   "b": (A, "NEW (added in step 2). `df_orders_vespa.iterrows()` builds a Series per order row (line 290), and `pd.notna` runs once per row (line 300). Iterating `to_dict('records')` gives the same values, and the pd.notna test is kept per value. Mechanism: per-row Series construction is removed. Measured in full mode.")},
  extra=[{"label": "b", "root_cause": "C3.S1", "lines": [290,291,292,293,294,295,296,297,298,299,300,301,302,303,304,305], "why": "per-row iterrows over the order frame builds a pandas Series for each order to read seven fields; a record iteration gives the same values"}])

d("examples/ecommerce-user-preferences/webapp/app.py::get_wikipedia_image",
  "Looks up a Wikipedia image URL for a make and model over the MediaWiki API, with fallbacks, and caches successful URLs in IMAGE_CACHE.",
  {"a": (R, "Caching the failure would add entries to module-level IMAGE_CACHE, and later calls would then return None without asking Wikipedia again, which is a change in the function's results across calls and in module state. Rejected on the contract."),
   "b": (A, "Each candidate image title gets its own imageinfo request (lines 146-152 and 179-185), one at a time. The MediaWiki API accepts several titles in one titles parameter, which would replace the loop with one request. Blocked here: it needs Wikipedia.")})

d("examples/ecommerce-user-preferences/webapp/app.py::load_system_prompt",
  "Reads system_prompt.txt next to the module and returns its text.",
  {"a": (R, "The file is about 2 KB and is opened once per chat turn. A read of that size costs tens of microseconds, which is small next to the OpenAI and Vespa calls in the same turn. Caching it at module level would change module state for a saving no measurement here could separate from noise. Rejected as negligible.")})

ssub = "examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py"
for name, lines in [("subgraph_GenerateKeywords", [48,52]), ("subgraph_EvaluateCategory", [99,103]),
                    ("subgraph_EvaluateFilters", [149,153]), ("EvaluateResults", [197,201])]:
    d(f"{ssub}::{name}",
      "Builds a prompt and a StructuredOutputParser, creates a ChatOpenAI client, and invokes the chain on the conversation to return structured fields.",
      {"a": (A, f"`ChatOpenAI(model=\"gpt-4o-mini\", temperature=0)` and the chain are built on every node call (line {lines[0]}), with fixed configuration. A module-level client built once would serve every call. Blocked here: invoking the chain needs the OpenAI API.")})

d("examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/vespa_module/vespa_retriever.py::VespaRetriever",
  "LangGraph node that builds Vespa conditions from the state and queries Vespa for matching products.",
  {"a": (A, "`Vespa(url=..., cert=..., key=...)` is constructed on every retrieval call (line 67), so a connection is set up per query. A module-level or cached client would serve every call, if pyvespa's client is safe to share. Blocked here: the unit queries Vespa.")})

d("examples/agentic-streamlit-chatbot/simple_app/streamlit_vespa_app.py::VespaRetriever",
  "Tool that queries Vespa for products matching a user query and returns the filtered results as JSON.",
  {"a": (A, "`Vespa(url=VESPA_URL, ...)` is built inside the tool body on every call (lines 50-52). A module-level client would serve every call. Blocked here: the tool queries Vespa.")})

d("examples/google-cloud/cloud-functions/python/main.py::getlogs",
  "HTTP function that lists zstd-compressed log blobs in a bucket, decompresses them, and returns the JSON records whose uri contains the filter.",
  {"a": (R, "`.__contains__` calls cost tens of nanoseconds per record, against zstd decompression and JSON parsing on the same records. The function also needs Google Cloud Storage to run, so nothing here can measure it. Rejected as negligible.")})

d("examples/google-cloud/cloud-functions/python/main.py::get_blobs",
  "Returns the blob listing of a bucket, from a newly built storage client.",
  {"a": (A, "`storage.Client()` is built on every HTTP request (line 88). A client built once per instance is the usual pattern for warm function instances. Blocked here: it needs Google Cloud credentials.")})

d("examples/in-context-learning/categorize_group.py::inference",
  "Builds ten Vespa request bodies for one query and posts one of them to Vespa, returning the parsed result.",
  {"a": (A, "Nine of the ten request dictionaries (lines 128-209) are built and never read; only query_request_bm25_no_group_10 is posted. Deleting the dead literals removes a few microseconds of dict construction per call and no behaviour. Blocked here: the function posts to Vespa."),
   "b": (A, "`requests.post` on line 211 is called without a Session, so each query opens a new connection. Creating one Session outside the call would reuse the connection. Blocked here: the function posts to Vespa.")})

d("examples/embedder-auto-training-evaluation/training-evaluation/positives-negatives.py::search",
  "Posts one query to the search endpoint and appends the query with its positives and negatives to train_data.",
  {"a": (R, "The POST runs before the positive-document check. An early return before the POST would skip the printed error on line 48 when the request fails and the query has no positives, which changes the printed output. The contract requires identical printed output. Rejected.")})

d("examples/model-exporting/export_hf_model_from_hf.py::export_model",
  "Downloads a Hugging Face model and tokenizer and exports them to a local directory.",
  {"a": (R, "This is one-time export code. The save-then-delete writes a few kilobytes of tokenizer files, and the run is dominated by the model download. Rejected as negligible for energy.")})

d("examples/model-exporting/export_model_from_hf.py::export_model",
  "Downloads a Hugging Face model and tokenizer and exports them to a local directory.",
  {"a": (R, "This is one-time export code. The save-then-delete writes a few kilobytes of tokenizer files, and the run is dominated by the model download. Rejected as negligible for energy.")})

d("news/src/python/create_bert_embeddings.py::create_embeddings",
  "Reads news rows, runs BERT over each title and abstract pair, and writes the first-token vector per document.",
  {"a": (A, "One document goes through the model per forward pass (lines 57-59). A padded batch would run the same documents in fewer passes. Equivalence is not guaranteed under padding, so verification decides. Blocked here: the BERT checkpoints are not in the local cache."),
   "b": (A, "The forward pass runs without torch.no_grad() (line 58), so autograd records a graph nobody uses. Wrapping the call in no_grad gives the same output and no graph. Blocked here: needs the BERT checkpoint."),
   "c": (A, "`outputs[0].tolist()[0][0]` converts the whole 1 x seq x 512 hidden state to nested Python lists and keeps one 512-vector. `outputs[0][0, 0].tolist()` gives the same 512 values. Blocked here: needs the BERT checkpoint."),
   "d": (A, "The tokenizer and the BERT model are loaded from_pretrained on every call (lines 47-48), and main calls create_embeddings once per split. Loading once at module scope gives the same model. Blocked here: needs the BERT checkpoint."),
   "e": (A, "`categories` and `subcategories` are filled for every row (lines 30-31, 41-42) and never read. Deleting them removes two dict stores per row. Negligible, and blocked here with the rest of the function.")})

d("news/src/python/vespa_client.py::query_news",
  "Posts a nearest-neighbour query to the Vespa search endpoint and returns the JSON response.",
  {"a": (A, "requests.post runs without a Session, so each call opens a connection and does an mTLS handshake. A module-level Session would reuse them. Blocked here: it needs the Vespa endpoint.")})

d("news/src/python/vespa_client.py::query_user_embedding",
  "Fetches one user's embedding from Vespa with a contains query and parses it.",
  {"a": (A, "requests.get runs without a Session, so each call opens a connection and does an mTLS handshake. Blocked here: it needs the Vespa endpoint.")})

d("news/src/python/evaluate.py::calc_impression",
  "Looks up the user's embedding, queries the candidate news, and returns predictions and labels for one impression.",
  {"a": (A, "query_user_embedding runs once per impression, with no cache by user_id, so repeated users fetch the same vector again. A per-run dict keyed by user_id would answer repeats. Blocked here: it needs Vespa.")})

cp = "rag-blueprint/eval/"
for fn, lines in [("collect_pyvespa.py::feature_collection_second_phase_query_fn", [49,50]),
                  ("collect_pyvespa.py::feature_collection_first_phase_query_fn", [95,96]),
                  ("evaluate_ranking.py::rank_first_phase_query_fn", [55,56]),
                  ("evaluate_ranking.py::rank_second_phase_query_fn", [85,86])]:
    d(cp + fn,
      "Builds a Vespa query body for one query, with an embedding input for the query text.",
      {"a": (A, f"embed() is called twice on the same text (lines {lines[0]}-{lines[1]}), for query(embedding) and query(float_embedding). Vespa may evaluate each embed separately, and that cost runs in the Vespa process. A single embed value passed to both inputs gives the same query. Whether Vespa already deduplicates is not checked here. Blocked here: it needs the Vespa endpoint.")})

d(cp + "evaluate_match_phase.py::match_weakand_query_fn",
  "Returns the Vespa query body for the weakAnd match-only query, including an embedding input.",
  {"a": (R, "Removing the input.query(embedding) key changes the body this function returns, so the return value changes. The saving would be server-side and cannot be shown here. Rejected on the contract.")})

vid = "text-video-search/src/python/embedding.py::"
d(vid + "VideoFeedDataset.__getitem__",
  "Extracts frames from one video, encodes each with CLIP, and returns one Vespa document per frame.",
  {"a": (A, "Each frame gets its own CLIP encode_image call on a batch of one (lines 97-99). Batching the video's frames into one tensor runs the encoder once per video. Blocked here: the CLIP weights are not in the local cache."),
   "b": (A, "`ntpath.basename(video_file_name)` and the split on '.mp4' are recomputed for every frame (lines 100, 103), though they depend only on the video. Binding them once before the loop gives the same ids. Blocked here for the same reason as (a).")})

d(vid + "TextProcessor.embed",
  "Encodes a text query with the CLIP text encoder and returns the normalised vector.",
  {"a": (A, "The same query string goes through the text encoder again on each call, and Streamlit reruns repeat it. A small cache keyed on the text would return the stored vector. Blocked here: CLIP weights are not cached.")})

d(vid + "TextProcessor.__init__",
  "Loads the CLIP model and keeps it on the object for the process lifetime.",
  {"a": (R, "The visual tower stays in memory, but dropping it would edit the object returned by clip.load, and the saving is memory, not computation. Rejected for mechanism: no energy work is removed.")})

d("text-video-search/src/python/app.py::get_predefined_queries",
  "Fetches the predefined query list over HTTP and returns its non-empty lines.",
  {"a": (A, "Streamlit reruns the script on each widget change, and each rerun repeats the HTTP GET while the checkbox is ticked. A cache with a stated lifetime would serve repeats. Blocked here: the file is a remote URL, and the lifetime is the decision.")})

fs = "incremental-search/search-as-you-type/feed_to_vespa.py::"
d(fs + "vespa_feed",
  "Feeds each document to Vespa by running one curl subprocess per document.",
  {"a": (A, "Each document costs a fork and exec of curl and a new TLS connection (lines 83-86, through vespa_post and call). A single bulk feed, or one persistent HTTP session, would do the same writes. Blocked here: it needs a Vespa endpoint.")})

d(fs + "update_endpoint",
  "Reads the feed file and the index, removes stale documents and feeds new ones for one endpoint.",
  {"a": (A, "The same feed JSON is parsed twice: once here for the ids (line 149) and once inside vespa_feed (line 167). Passing the parsed list through removes one parse. Blocked here: it needs a Vespa endpoint.")})

d("feed_to_vespa.py::vespa_remove",
  "Deletes each stale document id from Vespa with one HTTP DELETE per id.",
  {"a": (A, "One DELETE request per id, each followed by a JSON parse (lines 64-68). A bulk remove, or a single vespa feed call with remove entries, would do the same work in fewer requests. Blocked here: it needs a Vespa endpoint.")})

d("feed_to_vespa.py::update_endpoint",
  "Reads the config and the feed for one endpoint, removes stale documents, and feeds the new ones.",
  {"a": (A, "get_indexed_docids pages through the whole index (lines 153-154) whether or not the result is used. The result is used only when do_remove_index or do_feed is set. Skipping the call when neither is set removes the paging with the same results. The CI configs set do_feed, so the saving is off the default path. Blocked here: needs a Vespa endpoint.")})

d("colbert/model2onnx.py::VespaColBERT.__init__",
  "Builds a BERT model from a config and a linear projection, then calls init_weights.",
  {"a": (R, "The random weights this unit leaves are overwritten by from_pretrained in the only caller, and they are random by design, so no output of the unit can be compared between the original and a repair. A repair cannot be checked for identical behaviour. Rejected.")})

rv = "reverse-image-search/script/feed.py::run"
d(rv,
  "Iterates an image dataset, saves each image to disk, embeds it with a model, and feeds batches to Vespa.",
  {"a": (A, "`ex['image']` is read and decoded on line 136, before the skip test on line 140. On a resumed run every image already on disk is decoded and then discarded. Testing abs_path.exists() first, or casting the column without decoding, avoids it. Blocked here: needs the datasets package's image feature and a dataset download."),
   "b": (A, "After _save_image writes the JPEG, the file is read back for base64 (line 152) and decoded again (line 153). The encoder's bytes can feed the base64 step directly. Blocked here: needs the dataset and model."),
   "c": (A, "feed_iterable blocks the loop (lines 180-187), so the next batch's image I/O and inference wait for the network. A feeder thread would overlap them. Pays off only if feed time is comparable to inference. Blocked here: needs Vespa.")})

d("hypencoder/encode_query.py::main",
  "Tokenises one query for the CLI and prints the ids and attention mask as JSON.",
  {"a": (R, "The numpy conversion costs microseconds per CLI call, and the numpy import is paid once per process at module load, outside the unit. Rejected as negligible.")})

d("commerce-product-ranking/scripts/evaluate.py::main",
  "Loads an evaluation parquet, runs the Vespa query function per query, and writes the evaluation output.",
  {"a": (A, "`pd.read_parquet` loads every column, but the script uses six. Passing `columns=` reads and decodes only those. Blocked here if the parquet and Vespa are not available; the parquet is not in the repository."),
   "b": (R, "`set_index('query_id')` is called twice on the same frame. The second call costs one reindex, against a parquet read and a Vespa query per row. Rejected as negligible.")})

d("colbert-long/scripts/evaluate.py::main",
  "Runs each evaluation query against Vespa in turn and writes the results.",
  {"a": (A, "Queries run one at a time, each waiting on a network round trip (lines 93-94). Running them concurrently would overlap the waits, at the cost of load on the server. Blocked here: needs Vespa.")})

d("multilingual-search/ext/evaluate.py::search",
  "Sends one query to Vespa and returns its hits, reading the query text from a one-row group.",
  {"a": (A, "`query_group.iterrows()` builds a Series per row to read one value (lines 12-13). `query_group['query'].iloc[0]` gives the same value. The Vespa round trip dominates. Blocked here: needs Vespa.")})

d("visual-retrieval-colpali/src/main.py::get_and_store_sim_maps",
  "Fetches the search results and then the similarity maps from Vespa, waits for the full images, and stores the maps.",
  {"a": (A, "The same query, embeddings and base ranking are sent to Vespa twice per search, once for results and once for sim maps (lines 263-268). One request selecting the summary features would cover both if the hit set and ranking are the same, which the schema suggests but a runtime check must confirm. Blocked here: needs Vespa.")})

d("visual-retrieval-colpali/src/main.py::message_generator",
  "Waits up to ten seconds for the full images to appear on disk, then streams a Gemini answer as server-sent events.",
  {"a": (A, "Each 0.2 s poll resets images and reopens every image already on disk (lines 368-380), although the files already present stay present. Keeping the ready images across polls removes the reopen. Blocked here: the function calls the Gemini client after the poll."),
   "b": (A, "The replace over the whole accumulated response (line 403) runs for every chunk. After the first pass no newline remains, so the replace is an identity call on the accumulated text. Applying it to chunk.text before the concatenation gives the same output. Blocked here: needs the Gemini client.")})

d("visual-retrieval-colpali/src/main.py::full_image",
  "Returns a full-size image for a doc id, from disk if present or from Vespa otherwise.",
  {"a": (A, "For a cached image the file is read and base64-encoded again on every request (lines 335-336). Caching the encoded string in memory, or keeping the encoded form on disk, avoids the repeat. The cached branch is local and can be measured if the module loads.")})

d("visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.query_vespa_bm25",
  "Runs a BM25 query on Vespa, sending the float query embedding as input.",
  {"a": (A, "Every BM25 query sends the full float embedding as input.query(qt) (lines 130, 142). The bm25 profile's first phase reads only the text fields, so the input is transferred and not read. Blocked here: needs Vespa, and the deployed profile must be checked.")})

d("visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.get_suggestions",
  "Runs a wildcard matches query on Vespa for question suggestions and returns the distinct questions.",
  {"a": (A, "Each keystroke sends a leading and trailing wildcard query (line 336), and nothing caches the answer. A debounce on the frontend, or a cache for repeated prefixes, avoids the repeat. Blocked here: needs Vespa.")})

d("news/src/python/convert_embeddings_to_vespa_format.py::read_embeddings",
  "Reads an embeddings file into a dict of id to float32 vector.",
  {"a": (R, "The float32 conversion is the rounding that the writers then format with %.6f. Removing it changes the printed digits in the output, so the output bytes change. Rejected on the contract.")})

d("news/src/python/train_mf.py::main",
  "Trains the matrix-factorisation model and evaluates it on train and validation data, then saves embeddings.",
  {"a": (R, "The second eval_model call repeats an evaluation whose output it prints again, so removing it changes the printed output. Rejected on the contract.")})

d("news/src/python/train_cold_start.py::train_model",
  "Trains the content-based model for a number of epochs, evaluating and saving embeddings after each.",
  {"a": (R, "The per-epoch save writes files that the run leaves on disk, so removing it changes the files produced. Rejected on the contract.")})

d("visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.format_query_results",
  "Formats a Vespa response into search results and builds a debug string about the query timing.",
  {"a": (R, "The debug string is logged, so dropping it changes the logged output when debug logging is on. Rejected on the contract.")})

d("visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.get_result_from_query",
  "Extracts search results from a Vespa response, logging the keys of each child at debug level.",
  {"a": (R, "The loop writes debug log lines, so removing it changes the logged output when debug logging is on. Rejected on the contract.")})

d("use-case-shopping/create_suggestions.py::filter_content",
  "Returns True when a noun phrase starts with one of the invalid prefixes.",
  {"a": (R, "Eight startswith calls per noun chunk, each well under a microsecond, next to spaCy parsing of the same title. Rejected as negligible.")})

d("news/src/python/mind_data.py::MindData.add_impressions",
  "Appends user, news, category, subcategory, entity and label entries for each positive and sampled negative of one impression.",
  {"a": (R, "The category, subcategory and entity indices it appends are read by train_cold_start.py, so they cannot be dropped in this unit. The caller train_mf.py discards them, but that does not make them unused in the repository. Rejected: the outputs are consumed.")})

# ---- what I have not decided yet: anything still missing will be caught by the coverage check
missing = []
records = []
for u in step1:
    name = u["unit"]
    what, decs, extra = D[name]
    dec_list = []
    for s in u["suspicions"]:
        verdict, why = decs[s["label"]]
        dec_list.append({"label": s["label"], "root_cause": s["root_cause"], "lines": s["lines"], "verdict": verdict, "why": why})
    for e in extra:
        verdict, why = decs[e["label"]]
        dec_list.append({"label": e["label"], "root_cause": e["root_cause"], "lines": e["lines"], "verdict": verdict, "why": why})
    records.append({"step": 2, "unit": name, "what_it_does": what, "decisions": dec_list})
    for k in decs:
        if k not in [s["label"] for s in u["suspicions"]] + [e["label"] for e in extra]:
            missing.append((name, k))

if missing:
    print("EXTRA decision labels with no suspicion:", missing)
print("units", len(records), "suspicions", sum(len(r["decisions"]) for r in records))
with open("/home/javad/energy-run/sample-apps/step2.jsonl", "w") as f:
    for r in records:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
