import json
U=[]
def u(unit,*s):
    sus=[]
    for i,(rc,lines,why) in enumerate(s):
        sus.append({"label":"abcdefgh"[i],"root_cause":rc,"lines":lines,"why":why})
    U.append({"step":1,"unit":unit,"suspicions":sus})
CT="incremental-search/search-suggestions/count_terms.py::"
u(CT+"process_docs",("C3.S4",[100,101,102,103],"for every distinct term, a list comprehension scans every document dict to test membership: terms x docs; the document frequency could be incremented in the first loop where each doc's keys are already walked"),("C1.S1",[92],"`total_count` is computed per document and never read"))
u(CT+"count_terms",("C10.S1",[59,60,61],"per window, `any(map(lambda ...))` runs a Python lambda per word and builds a slice; `not common_words.isdisjoint(window)` does the same test in C"),("C1.S4",[60,62],"`doc[i:i+win_len]` is sliced twice per window"))
u(CT+"process_doc",("C6.S1",[78],"`list(title_counts.keys()) + list(content_counts.keys())` builds two key lists and a concatenation, and terms in both dicts are summed twice"))
u(CT+"read_common_words",("C6.S3",[45,46,47],"`f.readlines()` materialises every line before a single pass"))
u(CT+"write_json_file",("C10.S2",[27],"`re.sub(r\" \", \"/\", term)` uses the regex engine for a one-character replace"))
AW="incremental-search/search-suggestions/accepted_words.py::"
u(AW+"read_common_words",("C6.S3",[14,15,16,17,18,19,20],"readlines then iterate once"))
u(AW+"process_docs",("C10.S1",[29,30,31,32],"per-term `term_set.add` loop where `update` would do"))
u(AW+"write_to_file",("C9.S1",[41,42],"one write per term with a concatenated string"))
MD="news/src/python/mind_data.py::MindData."
u(MD+"sample_valid_data",("C4.S2",[166,167,168,169,170],"three comprehensions and a user_index list are built before the filter `sum(labels) > 0 and sum(labels) != len(labels)` rejects the impression"),("C1.S4",[170],"`sum(labels)` computed twice"),("C8.S1",[159,160,161,162],"with prob=1.0 the output is deterministic yet rebuilt for the same data each epoch by callers"))
u(MD+"add_impressions",("C1.S4",[189,190,191,198,199,200],"`self.news_content[idx]` is looked up three times per row; one local would serve"))
u(MD+"read_data",("C1.S1",[93,101],"strptime result stored under 'timestamp' which nothing reads (grep in news/src/python)"))
u(MD+"read_news",("C3.S5",[60,61,65,66],"both entity JSON fields are parsed although only the first 2 ids are kept"))
u(MD+"sample_training_data",("C8.S1",[144,145,146],"find_clicked split is recomputed per impression per epoch"))
NE="news/src/python/evaluate.py::"
u(NE+"predictions",("C3.S4",[64,65],"`find_hit` scans the hit list linearly per news id; a dict of news_id->relevance built once per response makes it linear"))
u(NE+"calc_impression",("C8.S4",[73],"user embedding refetched for each impression though users repeat"))
u(NE+"calc_metrics",("C11.S5",[87,88,89,90],"impressions are independent but each does two blocking HTTP calls in sequence"),("C3.S6",[84,85,86],"whole file is parsed then 1000 sampled"))
TC="news/src/python/train_cold_start.py::"
u(TC+"train_epoch",("C6.S4",[99],"`total_loss += loss` keeps every batch's autograd graph alive until the epoch ends"))
u(TC+"train_model",("C1.S5",[116,117,120],"full train-set eval and rewrite of both embedding files every epoch, only the last is used"))
u(TC+"eval_model",("C10.S3",[123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143],"one forward pass per impression on tiny tensors"))
u(TC+"read_bert_embeddings",("C5.S3",[164],"np.zeros float64 then copied into FloatTensor"))
u(TC+"read_bert_embeddings_from_file",("C8.S3",[180,183],"`data_loader.news()` called twice per line"),("C10.S3",[181,182,183,184],"per-element float() in comprehension"))
u(TC+"save_embeddings",("C6.S1",[146,147,148,149,150,151,152,153,154],"forward passes without no_grad; torch.LongTensor(range(n))"))
u(TC+"write_embeddings",("C10.S3",[157,158,159,160],"embeddings[index].tolist() per row"))
TM="news/src/python/train_mf.py::"
u(TM+"train_epoch",("C6.S4",[63],"`total_loss += loss` retains autograd graphs"))
u(TM+"main",("C1.S4",[145,146],"train_model already evaluated at the final epoch; main re-evaluates the unchanged model"))
u(TM+"eval_model",("C10.S3",[84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103],"per-impression forward pass"))
u(TM+"save_embeddings",("C6.S1",[106,107,108,109,110,111,112],"forward without no_grad"))
CB="news/src/python/create_bert_embeddings.py::"
u(CB+"create_embeddings",("C6.S1",[58],"BERT forward with autograd enabled and no batching"),("C5.S4",[59],"`outputs[0].tolist()[0][0]` converts whole hidden-state tensor to nested lists to keep the CLS vector"),("C8.S2",[47,48],"tokenizer and model loaded in the function, called twice from main"))
u(CB+"write_embedding",("C9.S1",[68,69,70,71,72,73],"about 1000 f.write calls per embedding"))
CV="news/src/python/convert_to_vespa_format.py::"
u(CV+"convert_file",("C10.S2",[71],"json.dump per document uses pure-Python iterencode and many small writes"))
u(CV+"generate_random_date",("C8.S1",[74,75,76],"fromtimestamp/strftime per document for about 13 distinct dates"))
CE="news/src/python/convert_embeddings_to_vespa_format.py::"
u(CE+"convert_user_embeddings",("C5.S4",[39],"parses %.6f text into float32 then reformats with %.6f"))
u(CE+"convert_news_embeddings",("C5.S4",[53],"parses %.6f text into float32 then reformats with %.6f"))
u(CE+"read_embeddings",("C6.S3",[19,28],"all embeddings materialised into a dict before streaming out"))
VC="news/src/python/vespa_client.py::"
u(VC+"query_news",("C3.S3",[52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67],"bare requests.post per call without a Session, mTLS handshake each time"),("C9.S2",[61],"`select * from sources news` returns every field, caller reads two"))
u(VC+"query_user_embedding",("C3.S3",[45,46,47,48,49],"bare requests.get per call"))
LG="rag-blueprint/eval/train_lightgbm.py::"
u(LG+"perform_cross_validation",("C3.S4",[265,266,267,268,269,270,271,272],"one full-string re.sub over the dumped model JSON per feature, then json.loads"),("C6.S4",[136,194],"`models` list of fold boosters appended and never read"),("C1.S5",[188],"valid_sets includes the training split, scored every round only for a log line"))
u("rag-blueprint/eval/train_logistic_regression.py::perform_cross_validation",("C10.S3",[478,479,480,481,482],"`describe()` per feature computes quartiles that are not printed"),("C1.S4",[514,515],"predict and predict_proba each compute the decision function"))
FS="feed-split.py::"
u(FS+"what_language",("C1.S4",[20,24,26],"bs4 `el.text` re-joins all descendant strings on each access, up to three times"))
u(FS+"split_text",("C10.S4",[97],"`text = text + \"\\n\" + line` per line, quadratic in paragraph length"))
u(FS+"xml_fixup",("C3.S4",[38,39,40],"text.replace(match, ...) rescans the whole document per match"))
u(FS+"table_header_row",("C3.S2",[123],"same thead looked up for every row of one table"))
u(FS+"main",("C10.S2",[199],"json.dump uses the pure-Python encoder with many small writes"),("C10.S1",[164,166,167,169,170,171,172,173,174],"about eight regex/replace passes per paragraph"))
FV="feed_to_vespa.py::"
u(FV+"update_endpoint",("C1.S5",[156,158,172],"after deleting every id in the index the difference set is computed from the stale set and deleted again"),("C6.S2",[166],"`docids_in_feed.union(...)` copies the set per file"),("C1.S6",[153],"index is paged in full even when neither remove nor feed is set"))
u(FV+"vespa_remove",("C9.S1",[64,65,66,67,68],"one HTTP DELETE per document, sequential"))
u(FV+"get_docs",("C6.S6",[95,96,97],"open without close; function unused"))
u(FV+"get_feed_docids",("C6.S3",[123,124,125,126,127],"set([listcomp])"))
SA="incremental-search/search-as-you-type/feed_to_vespa.py::"
u(SA+"update_endpoint",("C1.S5",[141,155,160],"delete of all index ids then difference of stale set deleted again"),("C6.S2",[149],"union copies set per file"),("C8.S2",[147,148,149,165,166,167],"each feed file json.load-ed twice"))
u(SA+"vespa_post",("C9.S1",[48,49,50,51,52,53,54,55,56,57,58],"one forked curl process per document"))
u(SA+"vespa_delete",("C9.S1",[37,38,39,40,41,42,43,44,45],"one forked curl process per delete"))
CG="examples/in-context-learning/categorize_group.py::"
u(CG+"inference",("C1.S1",[128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,194,195,196,197,198,199,200,201,202,203,204,205,206,207,208,209],"twelve of thirteen request dicts are built per call and never used (only query_request_bm25_no_group_10 is posted)"),("C3.S3",[211],"bare requests.post per row without a Session"))
u(CG+"get_label",("C5.S1",[66,68],"`result not in label_names` is a linear scan of a 77-element list per call"))
PP="examples/workshop-ecommerce/preprocess.py::"
u(PP+"process_users",("C3.S1",[202,203,204,205,206,207,208,209],"iterrows builds a Series per purchase row"),("C3.S6",[175,178,181,188],"sample mode (limit rows) still reads, merges and groups all users"),("C9.S2",[175,178],"read_csv loads all columns, five used"))
u(PP+"process_products",("C3.S6",[139,144,152],"sample mode merges the full product table and writes `limit` rows"),("C3.S1",[152],"iterrows builds a Series per row"))
u(PP+"process_orders",("C10.S2",[260],"lambda x: list(x) per group where agg(list) works"),("C8.S4",[234,247],"orders.csv and order_products files re-read after process_users"),("C6.S2",[238],"`.copy()` of a never-mutated filter"),("C3.S1",[290],"iterrows"))
CT2="text-search/python/collect_training_data.py::"
u(CT2+"build_dataset",("C5.S1",[71,75],"`int(qid) not in processed_queries` linear scan of a list per query"),("C9.S1",[92,93,94,95,96,97,98,99],"reopens the processed-queries file and the CSV per query; builds a DataFrame to append a few rows"),("C1.S2",[98,99],"the append is outside the `if`, so already-processed ids are re-appended"))
u(CT2+"get_features",("C3.S3",[38],"bare requests.post without Session"))
u(CT2+"load_processed_queries",("C6.S6",[62,63,64],"open without with; readlines"))
EM="text-search/python/extract-msmarco.py::"
u(EM+"load_msmarco_queries",("C3.S6",[20,26],"parameter qrel is unused; every query is regex-cleaned though only qrel ids are read later"))
u(EM+"extract_documents",("C9.S1",[85],"out.tell() on a text-mode file per document"))
u(EM+"getcontent",("C8.S2",[68,69,70,71],"four string-pattern re.sub per document"))
SQ="text-search/python/sample-queries-and-documents.py::"
u(SQ+"select_documents",("C7.S1",[60,61,62],"rejection sampling with random.choice until the set reaches the target, `min(...)` recomputed per iteration"))
u(SQ+"load_queries",("C1.S3",[29],"re-applies the cleaning extract-msmarco already did, to all queries"))
u(SQ+"write_document_offsets",("C12.S2",[78,79],"offsets written in set order, so later seeks are random"))
u("text-search/python/convert-to-vespa-format.py::main",("C10.S2",[62],"json.dump per document uses the pure-Python encoder"))
EMB="text-video-search/src/python/embedding.py::"
u(EMB+"extract_images",("C6.S3",[48,49,50,51,52],"decodes every frame into a list; sample_images keeps only number_frames"))
u(EMB+"sample_images",("C6.S2",[33,34],"`np.array(images)[idx]` stacks all frames before indexing"))
u(EMB+"VideoFeedDataset.__getitem__",("C10.S3",[96,97,98,99],"one encode_image call per frame instead of one batch"),("C3.S2",[100,103],"basename and split recomputed per frame"))
u("text-video-search/src/python/app.py::get_predefined_queries",("C8.S4",[33,34,35,36],"HTTP GET on every Streamlit rerun, uncached"))
TS="test/test.py::"
u(TS+"exec_file",("C10.S1",[80,81,82,83,84],"loop rebuilding the joined path per component where os.makedirs does it"))
u(TS+"process_liquid",("C8.S2",[175,176,177,178,179],"one string-pattern re.sub per site variable over every block"))
u(TS+"parse_file",("C10.S4",[211,212,213,214,215,216],"`content +=` in a loop and str(type(line)) test"))
u(TS+"parse_page",("C3.S1",[263,264,265,266,267,268,269,270,271,272,273,274,275,276,277,278,279,280],"find_all with a Python lambda per tag; independent ifs"))
u(TS+"run_url",("C10.S4",[306,307,308,309,310,311,312,313],"allpages += bytes in a loop; sequential fetches"))
u("test/pseudo_terminal.py::Log.write",("C4.S1",[29,30,31,32,33],"regex match runs on every chunk even when not verbose"))
CO="visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator."
u(CO+"gen_similarity_maps",("C1.S1",[83,86,88],"processed_images is appended to and never read; original_images holds a full copy of each image that is never mutated"))
u(CO+"_prepare_similarity_map_tensor",("C3.S2",[147,148,149,150],"hasattr/image_seq_length resolved per cell"),("C10.S3",[143,144,145,146,154,155,156,157,158,159],"scalar tensor assignment per cell"))
u(CO+"_blend_image",("C3.S2",[177,178,179,180],"resolution depends only on the image size, recomputed per token"))
u(CO+"should_filter_token",("C8.S2",[253,254,255],"re.compile on every call, per token per image"))
VA="visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient."
u(VA+"float_to_binary_embedding",("C10.S3",[155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178],"per-vector np.array/np.where/packbits/tolist"))
u(VA+"get_suggestions",("C6.S3",[364],"set([listcomp])"))
u(VA+"get_result_from_query",("C1.S4",[239,240],"ranking.split('_') computed three times"))
u(VA+"format_query_results",("C1.S5",[100,101,102,103,104],"values built only for a debug log"))
VM="visual-retrieval-colpali/src/main.py::"
u(VM+"message_generator",("C10.S4",[395,396,397,398,399,400,401,402,403,404],"replace_newline_with_br rescans the whole accumulated text per chunk"),("C3.S3",[364,365,366,367,368,369,370,371,372,373,374,375,376,377,378,379,380,381,382],"reopens every ready image every 0.2 s poll"))
u(VM+"get_and_store_sim_maps",("C5.S4",[288,289,290],"PNG base64-encoded then immediately decoded to write"),("C3.S6",[273,274,275,276,277,278],"builds a full list per poll so all() cannot short-circuit"))
u(VM+"full_image",("C5.S4",[335,336,337,338,339,340,341],"file read and base64-encoded per request"))
u(VM+"fetch_results",("C11.S4",[205,206,207],"ColPali forward pass runs synchronously inside an async function"))
u(VM+"poll_vespa_keepalive",("C1.S8",[251,252,253,254,255],"a Vespa query every 5 s forever, new session each time"))
PF="visual-retrieval-colpali/prepare_feed_deploy.py::"
u(PF+"download_pdf",("C3.S5",[266,267,268],"invalid filename does `continue` without incrementing attempt, repeating the GET forever"))
u(PF+"float_to_binary_embedding",("C10.S3",[584,585,586,587,588,589,590,591,592],"per-vector numpy ops for ~1030 vectors per page"))
u(PF+"generate_embeddings",("C10.S3",[534,535,536,537,538,539,540,541,542,543,544,545,546,547,548,549,550,551,552,553,554,555,556,557,558,559,560,561,562,563,564,565,566,567,568,569],"batch_size parameter not passed to DataLoader, one image per forward"))
u(PF+"get_pdf_images",("C6.S3",[319,320,321,322,323,324,325,326,327,328,329],"convert_from_path rasterises every page into memory at once"))
u("visual-retrieval-colpali/refeed_from_hf.py::process_item_for_vespa",("C5.S4",[36,37],"image decoded to PIL then re-encoded to JPEG and base64"),("C3.S6",[41,42,43,44,45],"scans every key of every item for embedding.N keys"))
u("visual-retrieval-colpali/src/frontend/app.py::SimMapButtonPoll",("C9.S1",[495,496,497,498,499,500,501,502,503,504],"each pending token button polls every 0.5 s"))
EC="examples/ecommerce-user-preferences/webapp/app.py::"
u(EC+"get_wikipedia_image",("C9.S3",[133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163],"one imageinfo request per candidate image"),("C8.S4",[167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,194,195,196],"second loop re-requests imageinfo already fetched by the first"),("C8.S1",[103,127,208],"failed lookups are not cached"))
u(EC+"get_car_image",("C1.S4",[563,573],"cache checked and stored again though get_wikipedia_image does both"))
u(EC+"load_system_prompt",("C8.S2",[46,47,48,49],"static file read on each chat request"))
u(EC+"chat",("C11.S5",[500,501,502],"two independent Vespa queries run in sequence"))
u(EC+"query_vespa",("C3.S3",[216,217,218,219,220,221,222,223,224,225,226,227,228,229,230,231,232,233,234,235,236,237,238,239,240,241,242,243,244,245,246,247,248,249,250,251,252,253,254,255,256,257,258,259,260,261,262,263,264,265,266,267,268,269,270,271,272,273,274,275,276,277,278,279,280,281,282,283,284,285,286,287,288,289,290,291,292,293,294,295,296,297,298,299,300,301,302,303,304,305,306,307,308],"bare requests.post with mTLS cert per call"))
GC="examples/google-cloud/cloud-functions/python/main.py::"
u(GC+"get_blobs",("C8.S2",[87,88,89,90],"storage.Client() built per request"))
u(GC+"getlogs",("C11.S5",[60,61,62,63,64,65,66,67,68,69,70],"blobs downloaded and decompressed one after another"),("C7.S4",[66,67,68,69,70],"json.loads per line before a cheap uri filter"))
u(GC+"listfiles",("C9.S2",[37,38,39,40,41,42,43,44,45,46,47,48,49],"lists every object then filters by substring in Python"))
EP="examples/embedder-auto-training-evaluation/training-evaluation/"
u(EP+"positives-negatives.py::search",("C4.S7",[22,23,24,25,44,45],"Vespa query runs before the empty positives/negatives early return"))
u(EP+"evaluate.py::search",("C3.S2",[35],"str(query_id) recomputed per hit"),("C11.S5",[10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25],"sequential blocking POST per query"))
u(EP+"train.py::TrainDataset.__getitem__",("C3.S7",[23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41],"pop(0) then append rotates lists on each sample"))
u(EP+"train.py::TrainDataset.__init__",("C6.S3",[11,12,13,14,17,18,19,20],"readlines before one pass"),("C6.S4",[14],"keeps whole document dict, only text read"))
VS="examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/"
for f in ["subgraph_GenerateKeywords","subgraph_EvaluateCategory","subgraph_EvaluateFilters","EvaluateResults"]:
    u(VS+"langgraph_modules/subgraph.py::"+f,("C8.S2",[15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52],"schema, parser, prompt, ChatOpenAI client and chain rebuilt on every call; only invoke needs to run"))
u(VS+"vespa_module/update_vespa.py::fetch_documents",("C3.S3",[27],"new syncio session per call, called every 3 s"))
u(VS+"utils/helpers.py::get_latest_ai_or_human_message",("C3.S2",[3,4,5,6,7,8],"messagetype string comparisons re-evaluated per message"))
u("examples/book-search/frontend/app.py::feed_catalog",("C9.S1",[18,19,20,21,22,23,24,25],"feed_data_point per JSONL line"))
GD="examples/mcp-server-app/script/generate_data.py::"
u(GD+"generate_job",("C10.S2",[73],"random.choice(list(skills.keys())) builds a list"))
u(GD+"generate_candidate",("C10.S2",[104],"random.choice(list(skills.keys())) builds a list"))
u(GD+"save_vespa_feed",("C6.S3",[118,119,120,121,122,123,124,125,126,127,128,129,130],"full list of dicts then joined into one string"))
u("examples/model-exporting/export_hf_model_from_hf.py::export_model",("C1.S5",[43,45,46,47,48,49],"save_pretrained writes every tokenizer file, then all but one are deleted"))
u("examples/model-exporting/export_model_from_hf.py::export_model",("C1.S5",[42,44,45,46,47,48],"save_pretrained then delete all but vocab.txt"))
u("billion-scale-vector-search/app/src/main/python/recall.py::knn_result_read",("C6.S6",[44,45,46,47,48,49,50],"open without close; header read via separate np.fromfile"))
u("colbert-long/scripts/convert.py::remove_control_characters",("C10.S1",[6,7],"per-character unicodedata.category in a generator for each chunk"))
u("colbert-long/scripts/evaluate.py::search",("C3.S2",[42],"str(query_id) recomputed per hit"))
u("use-case-shopping/create_suggestions.py::filter",("C10.S1",[57,58,59,60,61,62,63,64,65],"per-substring Python loop"),("C1.S3",[58,59,60],"unreachable startswith('/') branch"))
u("use-case-shopping/create_suggestions.py::filter_content",("C10.S1",[67,68,69,70,71],"loop over invalid_starts instead of startswith(tuple)"))
u("use-case-shopping/convert_meta.py::main",("C6.S3",[54,55,56,57,58,59,60,61,62,63,64,65,66,67],"readlines, whole list, one indented json.dumps"))
u("use-case-shopping/convert_reviews.py::main",("C6.S3",[46,47,48,49,50,51,52,53,54,55,56,57,58],"readlines, whole list, one indented json.dumps"))
u("multilingual-search/ext/evaluate.py::search",("C3.S5",[12,13],"iterrows builds a Series per row to keep only the last query"))
u("reverse-image-search/script/feed.py::run",("C3.S3",[127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192],"feed_iterable builds a pool and connections per 32-document batch, blocking the next batch"),("C5.S4",[144,145,146,147,148,149,150,151,152,153],"JPEG written to disk, read back and decoded again"))
u("reverse-image-search/script/search.py::_search",("C5.S4",[89,90],"astype copies of already-typed arrays before tolist"))
u("commerce-product-ranking/scripts/evaluate.py::main",("C9.S2",[52,53,54,55],"read_parquet loads all columns/rows, three successive copies"),("C3.S6",[58,59,60,61,62,63,64,65,66,67,68,69,70,98],"recall string built for all queries, then restricted to qrels"),("C10.S1",[91,92,93,94,95],"groupby.apply with lambda per query"))
u("msmarco-ranking/python/evaluate_passage_run.py::eval_query",("C3.S2",[90,91,92,93,94],"args.trec_format tested per hit"))
u("msmarco-ranking/python/evaluate_passage_run.py::format_query",("C2.S1",[49,50],"one-line wrapper over str.format"))
u("billion-scale-image-search/app/src/main/python/create-joined-feed.py::nan_handler",("C10.S2",[20,21,22,23,24],"np.isnan on a scalar"))
u("hypencoder/encode_query.py::main",("C5.S4",[70,71,72],"numpy round trip to get floats"))
with open("step1.jsonl","w") as f:
    for r in U: f.write(json.dumps(r)+"\n")
print(len(U))
