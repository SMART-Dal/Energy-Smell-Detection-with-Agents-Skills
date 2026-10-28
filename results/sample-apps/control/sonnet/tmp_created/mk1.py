import json
U=[]
def u(unit, *s):
    U.append({"step":1,"unit":unit,"suspicions":[{"label":l,"lines":ln,"why":w} for l,ln,w in s]})

u("feed-split.py::split_text",
 ("a",[97],"`text = text + \"\\n\" + line` copies the whole accumulated section for every line; the section only needs to be joined when flushed at lines 91-93 and 99"),
 ("b",[83],"`markdownify(str(soup))` serialises the tree and markdownify re-parses it with html.parser"))
u("feed-split.py::xml_fixup",
 ("a",[38,39,40],"`text.replace(match, escaped_match)` scans the full text once per highlight block, O(matches x length)"),
 ("b",[36,37],"regex given as a string is looked up in re's cache on every call"))
u("feed-split.py::what_language",
 ("a",[20,24,26],"`el.text` runs BeautifulSoup get_text() up to three times per code block; the value does not change"))
u("feed-split.py::main",
 ("a",[164,165,166,167],"four re.sub calls with string patterns per paragraph, each going through re's pattern cache"))
u("incremental-search/search-suggestions/count_terms.py::process_docs",
 ("a",[100,101,102,103],"for each term in the vocabulary, scans every document's count dict to count documents containing it, so cost is vocabulary x documents; the count can be taken in the summing loop at lines 93-97"),
 ("b",[92],"`total_count` is computed per document and never read"),
 ("c",[85,86,87],"doc_counts list holds every per-document dict; only needed by the quadratic scan at 100-103"))
u("incremental-search/search-suggestions/count_terms.py::count_terms",
 ("a",[59,60,61,62],"each window builds a slice, a lambda and a map, then slices again to join; the common-word test could be done once per word with a prefix sum"))
u("incremental-search/search-suggestions/count_terms.py::process_doc",
 ("a",[76,77,78,79],"iterates list(title_counts.keys()) + list(content_counts.keys()), building a concatenated list and calling .get twice per term"))
u("incremental-search/search-suggestions/count_terms.py::write_json_file",
 ("a",[27],"`re.sub(r\" \", \"/\", term)` runs the regex engine per term where str.replace gives the same result"),
 ("b",[39],"json.dump with indent=2 uses the pure-Python encoder and many small writes"))
u("colbert-long/scripts/convert.py::remove_control_characters",
 ("a",[7],"calls unicodedata.category for every character of every chunk inside a Python generator; a memoised str.translate table calls it once per distinct code point"))
u("news/src/python/mind_data.py::MindData.sample_valid_data",
 ("a",[166,167,168,169,170],"category, subcategory and entity lists are built for every impression before the `sum(labels) > 0 and sum(labels) != len(labels)` filter that discards all-clicked and none-clicked impressions"),
 ("b",[161,162,163],"called every epoch with prob=1.0 and rebuilds identical tensors each time"))
u("news/src/python/mind_data.py::MindData.add_impressions",
 ("a",[189,190,191,198,199,200],"three separate `self.news_content[idx][...]` lookups per sampled row where one lookup would serve"))
u("news/src/python/mind_data.py::MindData.read_data",
 ("a",[93],"datetime.strptime parses a timestamp for every impression row; the value is stored but the training code never reads it"))
u("news/src/python/evaluate.py::predictions",
 ("a",[64,65],"calls find_hit per news id, each scanning all hits linearly, so O(n^2) per impression; a dict of relevance by news_id is built once"))
u("news/src/python/evaluate.py::find_hit",
 ("a",[56,57,58],"linear scan over hits per lookup"))
u("news/src/python/train_cold_start.py::write_embeddings",
 ("a",[160],"`embeddings[index].tolist()` creates a tensor view and a list per id; one `embeddings.tolist()` converts the matrix once"))
u("news/src/python/train_cold_start.py::save_embeddings",
 ("a",[151,152],"user and news embeddings are computed with autograd recording on although only written to file"))
u("news/src/python/train_cold_start.py::train_model",
 ("a",[120],"save_embeddings does a full forward pass and rewrites both TSV files every epoch; each overwrites the previous, so only the last epoch's files survive"),
 ("b",[116],"eval_model on the whole training set every epoch"))
u("news/src/python/train_cold_start.py::train_epoch",
 ("a",[99],"`total_loss += loss` keeps every batch's autograd graph reachable until the epoch ends"))
u("news/src/python/create_bert_embeddings.py::write_embedding",
 ("a",[69,70,71,72,73],"one f.write call per number plus one per comma, about 1000 calls per document"))
u("news/src/python/create_bert_embeddings.py::create_embeddings",
 ("a",[57,58,59],"BERT is run one document at a time with autograd on, and the full hidden-state tensor is turned into nested lists to keep one row"))
u("news/src/python/convert_to_vespa_format.py::convert_file",
 ("a",[71],"json.dump(doc, output) goes through iterencode and many small writes; json.dumps takes the C one-shot encoder"),
 ("b",[53,54],"csv.DictReader builds a dict per row"))
u("news/src/python/convert_to_vespa_format.py::generate_random_date",
 ("a",[75,76],"fromtimestamp then strftime per document where a 13-entry table of dates would do"))
u("news/src/python/convert_embeddings_to_vespa_format.py::convert_user_embeddings",
 ("a",[39],"`\"%.6f\" % v` over numpy float32 scalars; formatting numpy scalars is slower than Python floats from embedding.tolist()"))
u("news/src/python/convert_embeddings_to_vespa_format.py::convert_news_embeddings",
 ("a",[53],"same per-element numpy scalar formatting as convert_user_embeddings"))
u("test/test.py::process_liquid",
 ("a",[176,177],"runs one re.sub per site variable plus two macro patterns on every command, though every pattern begins with '{' and most commands contain none"))
u("test/test.py::parse_page",
 ("a",[263],"a Python lambda is called for every tag in the soup to test name and attribute; find_all with a name list and attrs filter does it in the parser"),
 ("b",[278,279],"re.search and re.sub for a fixed prefix"))
u("test/test.py::parse_file",
 ("a",[212,213,214,215,216],"`content +=` string concatenation per child node and `str(type(line))` substring test"))
u("test/test.py::run_url",
 ("a",[306,307,308,309,310,311,312],"`allpages +=` on bytes copies the accumulated pages for every page"))
u("test/pseudo_terminal.py::Log.write",
 ("a",[31,32,33],"re.match runs on every output chunk even when not verbose; test self._verbose first"))
u("visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.gen_similarity_maps",
 ("a",[83,84,85,86,87,88],"processed_images is filled and never read, and img_pil.copy() duplicates every page although _blend_image only uses the size"),
 ("b",[97,98,99,100],"should_filter_token is evaluated for every image x token; the filtered token list is the same for all images"))
u("visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator._prepare_similarity_map_tensor",
 ("a",[147,148,149,150],"hasattr(self.processor, 'image_seq_length') evaluated for every cell inside the innermost loop"),
 ("b",[154,155,156,157,158,159],"one scalar torch index write per cell, about patches x tokens x images writes"))
u("visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.should_filter_token",
 ("a",[253,254,255],"re.compile executed on every call, called for every token x image"))
u("visual-retrieval-colpali/src/main.py::get_and_store_sim_maps",
 ("a",[273,274,275,276,277,278],"builds a list of os.path.exists results with all([...]) so it cannot short-circuit, polls with sleep(0.2) and repeats the check at line 278"),
 ("b",[289,290],"sim maps are PNG-encoded and base64-encoded by gen_similarity_maps, then immediately base64-decoded here"))
u("visual-retrieval-colpali/src/main.py::message_generator",
 ("a",[402,403],"`response_text = replace_newline_with_br(response_text)` rescans the whole accumulated text on every chunk"),
 ("b",[368,369,370,371,372,373,374,375,376,377,378,379,380],"on each retry pass, images already opened are opened again"))
u("visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.float_to_binary_embedding",
 ("a",[167,168,169,170,171],"np.where(np.array(vector) > 0, 1, 0) builds an int array before packbits; packbits accepts the boolean array directly"))
u("visual-retrieval-colpali/prepare_feed_deploy.py::float_to_binary_embedding",
 ("a",[588,589,590],"same np.where intermediate, per patch, about 1030 patches per page"))
u("text-search/python/extract-msmarco.py::extract_documents",
 ("a",[85],"`out.tell()` on a text-mode file forces a flush and position reconstruction for every one of about 3.2M documents"))
u("text-search/python/extract-msmarco.py::getcontent",
 ("a",[68,69,70,71],"four re.sub calls with string patterns per document"))
u("text-search/python/extract-msmarco.py::load_msmarco_queries",
 ("a",[26],"regex-normalises every training query although only queries with qrels are written later; the `qrel` parameter is unused"))
u("use-case-shopping/create_suggestions.py::filter",
 ("a",[62,63,64],"tests about 30 substrings one at a time in a Python loop per title and per noun chunk"),
 ("b",[60,61],"dead branch, line 58 already returns for len < 3"))
u("use-case-shopping/create_suggestions.py::filter_content",
 ("a",[68,69,70],"loop over a dict of prefixes; str.startswith accepts a tuple"))
u("text-search/python/collect_training_data.py::build_dataset",
 ("a",[75],"`int(qid) not in processed_queries` is a list membership test per query"),
 ("b",[92,93,94,95,96,97],"builds a DataFrame and reopens the CSV in append mode for each query"),
 ("c",[98,99],"the processed-queries file is reopened and appended to for every query, including ones already processed"))
u("text-search/python/collect_training_data.py::load_processed_queries",
 ("a",[63],"returns a list that is only used for membership tests"))
u("examples/embedder-auto-training-evaluation/training-evaluation/train.py::TrainDataset.__init__",
 ("a",[12,18],"file.readlines() copies the whole file into a list before parsing line by line"))
u("examples/embedder-auto-training-evaluation/training-evaluation/train.py::TrainDataset.__getitem__",
 ("a",[27,28,29,31,32,33],"pop(0) then append rotates a list in O(n) per access"))
u("billion-scale-vector-search/app/src/main/python/recall.py::compute_recall_with_distance_ties",
 ("a",[63,64,65,66,67],"Python loop over numpy scalars to find the end of a tie; a vectorised comparison finds it in one call"))
u("examples/ecommerce-user-preferences/webapp/app.py::load_system_prompt",
 ("a",[46,47,48,49],"re-reads system_prompt.txt from disk on every chat request"))
u("examples/workshop-ecommerce/preprocess.py::process_products",
 ("a",[152],"iterrows builds a Series per row for the whole products table even when only `limit` rows are written"))
u("examples/workshop-ecommerce/preprocess.py::process_users",
 ("a",[202,203,204,205,206,207,208,209],"iterrows builds a Series per purchase row"),
 ("b",[195,196,197,198],"value_counts per user"),
 ("c",[175,178,181,188],"reads and merges the whole order tables although only the first `limit` users are written when not --full"))
u("examples/workshop-ecommerce/preprocess.py::process_orders",
 ("a",[258,259,260,261,262],"aggregates with a Python lambda per group"),
 ("b",[290],"iterrows builds a Series per row"),
 ("c",[234],"orders.csv read again; process_users already read it"))
u("rag-blueprint/eval/train_lightgbm.py::perform_cross_validation",
 ("a",[188],"valid_sets includes lgb_train so the metric is computed on the training fold each boosting round; early stopping ignores it"),
 ("b",[265,266,267,268,269,270,271,272],"model dumped to a JSON string, one re.sub per feature over the whole string, then parsed back"))
u("text-video-search/src/python/embedding.py::VideoFeedDataset.__getitem__",
 ("a",[98,99,100,101,102,103],"each frame is sent to CLIP as a batch of one; ntpath.basename and split are loop-invariant"))
u("text-video-search/src/python/embedding.py::sample_images",
 ("a",[34],"np.array(images) stacks every frame into one array before indexing the sampled ones"))
u("examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/vespa_module/vespa_retriever.py::create_conditions",
 ("a",[12,13,14,15,16,17,18,19,20],"dict of lambdas rebuilt on every call"))
with open("step1.jsonl","w") as f:
    for r in U: f.write(json.dumps(r)+"\n")
print(len(U))
