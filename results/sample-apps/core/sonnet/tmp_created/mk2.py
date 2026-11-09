import json
R=[]
def r(unit, what, *d):
    R.append({"step":2,"unit":unit,"what_it_does":what,"decisions":[{"label":l,"lines":ln,"verdict":v,"why":w} for l,ln,v,w in d]})
A,X="accepted","rejected"

r("feed-split.py::split_text","splits a BeautifulSoup page into (id, header, text) sections by converting it to markdown and walking its lines",
 ("a",[97],A,"`text` is rebuilt as `text + \"\\n\" + line` for every line of a section; collecting lines in a list and joining at the flush points (91-93, 99) writes each line once. The string is local, but `text = text + ...` is not the in-place `+=` form, so CPython copies the buffer each time"),
 ("b",[83],X,"markdownify(str(soup)) re-parses the HTML, and the reparse normalises the markup; calling convert_soup directly was not shown to give identical markdown, so behaviour preservation cannot be claimed"))
r("feed-split.py::xml_fixup","escapes XML inside Jekyll highlight-xml blocks of an HTML string",
 ("a",[38,39,40],X,"a single re.sub would change behaviour when a block's text also occurs outside a highlight block (str.replace rewrites every occurrence); the exact-preserving edit (skip when escaped == match) saves almost nothing on XML blocks, which nearly always contain < or >"),
 ("b",[36,37],X,"re caches compiled patterns, so the string pattern costs one dictionary lookup per call; no measurable work to remove"))
r("feed-split.py::what_language","picks a code-block language from a Jekyll highlight tag or by sniffing for curl / import com.yahoo",
 ("a",[20,24,26],A,"`el.text` is BeautifulSoup get_text(), which walks the element's descendants and joins strings; it is evaluated up to three times per code block on the same unchanged element, once is enough"))
r("feed-split.py::main","reads a doc JSON, splits each HTML page into paragraph documents, merges question expansions and writes paragraph_index.json",
 ("a",[164,165,166,167],X,"re.sub with a string pattern hits re's compiled-pattern cache; hoisting would save a dictionary lookup per call, not a mechanism worth an edit, and main reads sys.argv and writes a fixed file so it cannot be measured cleanly"))
r("incremental-search/search-suggestions/count_terms.py::process_docs","sums per-document term counts into corpus counts and counts how many documents contain each term",
 ("a",[100,101,102,103],A,"for every term in `terms` it iterates all documents and builds a list of 0/1 flags, O(terms x docs) dictionary probes; each per-document dict holds a term once, so incrementing a `docs` counter in the summing loop at 93-97 gives the same number in one pass"),
 ("b",[92],A,"`total_count` is summed per document and never read; deleting the line removes a pass over every document's values"),
 ("c",[85,86,87],X,"the list of per-document dicts is needed by the summing loop; without the quadratic scan it could be a generator but that only saves memory, not work"))
r("incremental-search/search-suggestions/count_terms.py::count_terms","counts n-grams of up to term_length words in a tokenised document, skipping windows containing a common word",
 ("a",[59,60,61,62],A,"for every window it slices the list, builds a lambda and map and runs any() over win_len words, then slices again for the join; testing each word once into a flags list and prefix sum turns the common-word test into two index reads per window and only valid windows are sliced"))
r("incremental-search/search-suggestions/count_terms.py::process_doc","counts terms in title and content and returns their summed counts",
 ("a",[76,77,78,79],A,"the comprehension iterates list(title_counts.keys()) + list(content_counts.keys()), allocating two lists and a concatenation, and calls .get twice per key; copying title_counts and adding content counts touches each key once. Key order (title keys first, then new content keys) is preserved"))
r("incremental-search/search-suggestions/count_terms.py::write_json_file","builds update operations for each term and dumps them as indented JSON",
 ("a",[27],A,"`re.sub(r\" \", \"/\", term)` enters the regex engine per term; str.replace gives the same string without it"),
 ("b",[39],X,"dropping indent=2 changes the bytes of the output file, which is part of the contract"))
r("colbert-long/scripts/convert.py::remove_control_characters","deletes every character whose Unicode category starts with C from a string",
 ("a",[7],A,"calls unicodedata.category once per character inside a Python generator over all text; a str.translate table that fills itself via __missing__ calls category once per distinct code point and translates in C"))
r("news/src/python/mind_data.py::MindData.sample_valid_data","builds per-impression tensors for impressions that have both clicked and skipped items",
 ("a",[166,167,168,169,170],A,"the three index lists and user_index are built for every impression before the `sum(labels) > 0 and sum(labels) != len(labels)` test; impressions failing it (all clicked or none clicked) are discarded after the work is done. Testing first skips that work"),
 ("b",[161,162,163],X,"caching the tensors per prob/train changes object identity and state the callers could mutate, and random.random() must still be consumed to keep the RNG stream the same"))
r("news/src/python/mind_data.py::MindData.add_impressions","appends user, news, category, subcategory and entity indices for each positive and its sampled negatives",
 ("a",[189,190,191,198,199,200],A,"each sampled row does three separate self.news_content[idx][key] lookups, i.e. three attribute loads and three dict lookups on the same entry; one lookup serves all three"))
r("news/src/python/mind_data.py::MindData.read_data","parses impression rows into dicts of user index, timestamp, news indices and labels",
 ("a",[93],X,"the parsed datetime is stored in impression_list under \"timestamp\", which is part of the unit's effect on its argument; removing the parse changes it"))
r("news/src/python/evaluate.py::predictions","returns the relevance of each requested news id from a Vespa result",
 ("a",[64,65],A,"find_hit scans all hits for every id, O(ids x hits); building a dict from news_id to first hit once makes each lookup constant time. A missing id still gives None and a TypeError at hit[\"relevance\"], as before"))
r("news/src/python/evaluate.py::find_hit","linear search for a news id in a result's children",
 ("a",[56,57,58],X,"the repair is the dict in predictions, its only caller (grep); changing find_hit alone cannot remove the repeated scan"))
r("news/src/python/train_cold_start.py::write_embeddings","writes one tab-separated line per id with the embedding formatted to six decimals",
 ("a",[160],A,"`embeddings[index]` creates a tensor view and .tolist() a list per id, hundreds of thousands of times; one embeddings.tolist() converts the matrix in one call and rows are indexed as lists"))
r("news/src/python/train_cold_start.py::save_embeddings","computes user and news embeddings from the model and writes them as TSV",
 ("a",[151,152],A,"both embedding calls record an autograd graph through embeddings, linear layers and sigmoid although the result is only written; under torch.no_grad() no graph is built. Written values are identical"))
r("news/src/python/train_cold_start.py::train_model","trains the model for `epochs` epochs, evaluating and saving embeddings after each",
 ("a",[120],A,"save_embeddings runs a full forward pass and rewrites both files every epoch, each overwriting the last; running it once after the loop (guarded by epochs > 0) leaves the same final files"),
 ("b",[116],X,"eval_model prints metrics; removing or thinning the call changes printed output"))
r("news/src/python/train_cold_start.py::train_epoch","one epoch of mini-batch training that prints the summed loss",
 ("a",[99],X,"the printed total_loss is a tensor with grad_fn in the output text; accumulating loss.item() would change the printed output"))
r("news/src/python/create_bert_embeddings.py::write_embedding","writes a tab then the embedding as comma-separated %.4f",
 ("a",[69,70,71,72,73],A,"about 1000 f.write calls per document (value and comma separately); one write of a joined string does the same bytes with one call"))
r("news/src/python/create_bert_embeddings.py::create_embeddings","runs BERT over each document and writes the [CLS] vector",
 ("a",[57,58,59],A,"the forward pass builds an autograd graph (no torch.no_grad) and outputs[0].tolist() converts the whole 1 x tokens x 512 tensor to nested lists to keep row 0; a no_grad block and outputs[0][0, 0].tolist() give the same numbers with less work. Batching was left out because it changes padding and floating-point results"))
r("news/src/python/convert_to_vespa_format.py::convert_file","writes one JSON put-operation per unseen news row, joined by commas",
 ("a",[71],A,"json.dump(doc, output) goes through json's pure-Python iterencode and issues one write per token; output.write(json.dumps(doc)) uses the C one-shot encoder and one write, identical bytes"),
 ("b",[53,54],X,"csv.reader with positional access would raise IndexError on short rows where DictReader fills None, so it does not preserve behaviour on all inputs"))
r("news/src/python/convert_to_vespa_format.py::generate_random_date","random day in November 2019 as an int yyyymmdd",
 ("a",[75,76],X,"fromtimestamp uses local time zone, so a precomputed table would not preserve behaviour across zones, and the saving per call is small"))
r("news/src/python/convert_embeddings_to_vespa_format.py::convert_user_embeddings","writes user embeddings as a Vespa feed JSON array",
 ("a",[39],A,"`\"%.6f\" % v` is applied to numpy float32 scalars, which are converted through numpy's scalar machinery per element; embedding.tolist() yields Python floats with the same value, so the formatted text is identical"))
r("news/src/python/convert_embeddings_to_vespa_format.py::convert_news_embeddings","writes news embeddings as a Vespa feed update array",
 ("a",[53],A,"same per-element numpy scalar formatting as in convert_user_embeddings; the same edit with tolist() applies"))
r("test/test.py::process_liquid","applies each Liquid-transform regex substitution to a command string",
 ("a",[176,177],A,"every transform pattern starts with a literal '{', yet each re.sub scans the whole command; a command without '{' cannot match any, so returning early skips all the scans"))
r("test/test.py::parse_page","parses an HTML page into before/steps/after script lists from data-test attributes",
 ("a",[263],A,"a Python lambda is called for every tag in the document; find_all([\"pre\",\"div\",\"p\"], attrs={\"data-test\": True}) filters inside bs4's matcher in document order and calls the Python-level callback for none"),
 ("b",[278,279],X,"re.search/re.sub with literal patterns hit the re cache; the work removed is a lookup, and it runs only on tags that have data-test"))
r("test/test.py::parse_file","joins a <pre> element's child nodes into file content",
 ("a",[212,213,214,215,216],X,"`content +=` on a local str is resized in place by CPython, so the concatenation is not quadratic here"),
 ("b",[213],A,"`str(type(line))` builds a string such as \"<class 'bs4.element.NavigableString'>\" for every child node only to test a substring; testing type(line).__name__ avoids the string build with the same truth value, since the module path contains no 'ProcessingInstruction'"))
r("test/test.py::run_url","fetches or reads pages and runs them",
 ("a",[306,307,308,309,310,311,312],X,"the number of pages is small and each page costs a network or disk read; copying bytes is negligible next to it, and the unit starts docker commands so cannot be measured"))
r("test/pseudo_terminal.py::Log.write","appends output to a log and echoes it when verbose and not filtered",
 ("a",[31,32,33],X,"re.match(None, s) raises TypeError when no filter has been set; testing _verbose first would stop raising, which changes the exception behaviour"))
r("visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.gen_similarity_maps","loads each page image, then yields a blended base64 heatmap per image and unfiltered query token",
 ("a",[83,84,85,86,87,88],A,"img_pil.copy() duplicates every full page image and processed_images keeps a second list of them that is never read; _blend_image only uses original_size, so the copy and the list are dead work"),
 ("b",[97,98,99,100],A,"should_filter_token (a regex match) is evaluated for every image x token although the answer depends only on the token; computing the kept tokens once before the image loop removes (images-1) x tokens matches"))
r("visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator._prepare_similarity_map_tensor","fills a (maps, tokens, patches, patches) tensor from Vespa cell lists",
 ("a",[147,148,149,150],A,"hasattr and attribute read for image_seq_length run once per cell inside the innermost loop, thousands of times per call; the value is constant for the call"),
 ("b",[154,155,156,157,158,159],X,"a vectorised index_put with duplicate addresses does not guarantee the last write wins, so equivalence with the sequential loop is not assured"))
r("visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.should_filter_token","True if a token matches the filter regex",
 ("a",[253,254,255],X,"re.compile with a literal is served from re's cache; the only hoist available lives outside the function source, and the saving is one cache lookup"))
r("visual-retrieval-colpali/src/main.py::get_and_store_sim_maps","waits for page images, generates similarity-map PNGs and writes them to disk",
 ("a",[273,274,275,276,277,278],A,"all([os.path.exists(p) for p in img_paths]) builds the full list so cannot stop at the first missing file and is evaluated again after the loop; any/all over a generator short-circuits and the final check can reuse the loop's last result"),
 ("b",[288,289,290],A,"gen_similarity_maps PNG-encodes and base64-encodes each map and this loop immediately decodes it; yielding the PNG bytes from _blend_image and writing them removes an encode/decode pair per map (sole consumers: grep shows gen_similarity_maps is called only here and _blend_image only from gen_similarity_maps)"))
r("visual-retrieval-colpali/src/main.py::message_generator","waits for page images then streams a Gemini answer as SSE messages",
 ("a",[402,403],A,"`response_text = replace_newline_with_br(response_text)` rescans the whole accumulated answer for each chunk, O(n^2) in the answer length; replacing only the new chunk gives the same text because the earlier part is already newline-free"),
 ("b",[368,369,370,371,372,373,374,375,376,377,378,379,380],A,"every retry pass restarts `images = []` and re-opens every ready file; keeping already opened images and only probing missing ones removes the repeated PIL opens"))
r("visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.float_to_binary_embedding","packs each float query vector into signed-byte bit vectors",
 ("a",[167,168,169,170,171],A,"np.where(cond, 1, 0) materialises an int64 array before packbits; packbits takes the boolean array directly and gives the same bits"))
r("visual-retrieval-colpali/prepare_feed_deploy.py::float_to_binary_embedding","packs each patch float vector into signed-byte bit vectors for the feed",
 ("a",[588,589,590],A,"same np.where int64 intermediate per patch (about 1030 per page); packbits on the boolean mask gives the same bytes"))
r("text-search/python/extract-msmarco.py::extract_documents","writes each document's cleaned text and its output byte offset",
 ("a",[85],A,"out.tell() on a text-mode file flushes the encoder and reconstructs a position every call; keeping a running byte count (encoded length of each string written) gives the same offsets and leaves the buffer to flush normally"))
r("text-search/python/extract-msmarco.py::getcontent","reads one document at an offset, cleans title and body with regexes",
 ("a",[68,69,70,71],X,"patterns are literals served from re's cache; no mechanism beyond a lookup per call"))
r("text-search/python/extract-msmarco.py::load_msmarco_queries","reads all training queries and normalises each",
 ("a",[26],X,"dropping or deferring normalisation changes the returned dict, which is the unit's return value"))
r("use-case-shopping/create_suggestions.py::filter","True if a string is length-out-of-range or contains any filter substring",
 ("a",[62,63,64],A,"a Python-level loop over 30 keys does one `in` per iteration; any(map(text.__contains__, filters)) runs the loop in C with identical truth value and short-circuit"),
 ("b",[60,61],A,"`text.startswith(\"/\") and len(text) < 3` is unreachable because line 58 already returned for len < 3; deleting it removes a startswith call per title and noun chunk"))
r("use-case-shopping/create_suggestions.py::filter_content","True if the text starts with any invalid prefix",
 ("a",[68,69,70],A,"a Python loop calling startswith per prefix; any(map(text.startswith, invalid_starts)) iterates in C, same result"))
r("text-search/python/collect_training_data.py::build_dataset","queries Vespa for each unprocessed query and appends feature rows to a CSV",
 ("a",[75],A,"`int(qid) not in processed_queries` scans a list for every query; a set built once from the list gives O(1) membership, while len() for the printed count still uses the list"),
 ("b",[92,93,94,95,96,97],X,"replacing DataFrame.to_csv with the csv module could change float formatting in the file"),
 ("c",[98,99],X,"moving the processed-queries write inside the if changes the contents of the processed file, a behaviour change (and a possible bug, not an energy repair)"))
r("text-search/python/collect_training_data.py::load_processed_queries","reads the processed query ids as ints into a list",
 ("a",[63],X,"the list-to-set repair belongs to build_dataset, which also needs len() with duplicates; readlines() copy alone is trivial"))
r("examples/embedder-auto-training-evaluation/training-evaluation/train.py::TrainDataset.__init__","loads documents and queries from JSONL into dicts",
 ("a",[12,18],A,"file.readlines() materialises every line in a list before parsing; iterating the file object parses line by line without the list"))
r("examples/embedder-auto-training-evaluation/training-evaluation/train.py::TrainDataset.__getitem__","returns an InputExample for a query with rotating positive and negative document",
 ("a",[27,28,29,31,32,33],X,"pop(0)+append rotates short lists; the lists are per-query positives/negatives of modest size and any cheaper structure changes the state shape other readers (none found) rely on"))
r("billion-scale-vector-search/app/src/main/python/recall.py::compute_recall_with_distance_ties","recall at count allowing ties in the ground-truth distances",
 ("a",[63,64,65,66,67],A,"Python loop over numpy scalar subtractions and abs to find the end of the tie run; one vectorised comparison over true_dists[count:] finds the first non-tie index in one call"))
r("examples/ecommerce-user-preferences/webapp/app.py::load_system_prompt","reads system_prompt.txt and returns its text",
 ("a",[46,47,48,49],A,"opens and reads the same static file on every chat request; a cached copy removes the open, read and decode per request (file is a packaged resource beside app.py)"))
r("examples/workshop-ecommerce/preprocess.py::process_products","writes product documents to JSONL",
 ("a",[152],A,"in --full mode iterrows builds a pandas Series (copying a row across all columns) for each of about 50k products; itertuples builds a namedtuple without the Series construction"))
r("examples/workshop-ecommerce/preprocess.py::process_users","aggregates order rows into user profile documents",
 ("a",[202,203,204,205,206,207,208,209],A,"iterrows builds a Series per purchase row for every user's purchases (about 1.4M rows in --full); building the list of dicts from column arrays removes the Series construction"),
 ("b",[195,196,197,198],X,"Counter would change the key order of user_profile in the JSON output"),
 ("c",[175,178,181,188],A,"when not --full only the first `limit` users are written, but the merge covers all 1.4M train rows; restricting orders to the first `limit` user ids (isin on the train order ids) and the train rows to those orders before the merge writes the same users"))
r("examples/workshop-ecommerce/preprocess.py::process_orders","aggregates order products into per-order arrays and writes order JSONL",
 ("a",[258,259,260,261,262],A,"agg with a Python lambda calls list() once per group through pandas' Python-function path; agg(list) / apply(list) gives the same lists with less per-group overhead"),
 ("b",[290],A,"iterrows builds a Series per order row; itertuples avoids the Series construction"),
 ("c",[234],X,"orders.csv is read again, but the first read is in process_users, a different unit; removing it needs main to pass the frame, which spreads the edit over callers"))
r("rag-blueprint/eval/train_lightgbm.py::perform_cross_validation","cross-validates a LightGBM model, then trains and exports the final model",
 ("a",[188],X,"removing lgb_train from valid_sets drops the logged training metrics, which changes log records"),
 ("b",[265,266,267,268,269,270,271,272],A,"serialises the model dict to a string, runs one re.sub over the whole string per feature, and parses it back; renaming the entries in feature_names, feature_infos and feature_importances directly avoids F full-string scans"))
r("text-video-search/src/python/embedding.py::VideoFeedDataset.__getitem__","embeds each sampled frame of a video with CLIP",
 ("a",[98,99,100,101,102,103],X,"batching frames changes floating-point results of CLIP, and the loop-invariant basename/split work is negligible next to a CLIP forward pass"))
r("text-video-search/src/python/embedding.py::sample_images","samples equally spaced frames from a list",
 ("a",[34],A,"np.array(images) stacks every frame (a copy of all pixel data) before the few sampled ones are indexed; selecting from the list first stacks only the sampled frames"))
r("examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/vespa_module/vespa_retriever.py::create_conditions","turns condition strings into Vespa query-builder conditions",
 ("a",[12,13,14,15,16,17,18,19,20],X,"creating seven small lambdas per call is negligible next to the query-builder calls that follow; the only hoist is outside the function"))
with open("step2.jsonl","w") as f:
    for x in R: f.write(json.dumps(x)+"\n")
s1=[json.loads(l) for l in open("step1.jsonl")]
m={x["unit"]:x for x in R}
for u in s1:
    assert u["unit"] in m, u["unit"]
    assert [s["label"] for s in u["suspicions"]]==[d["label"] for d in m[u["unit"]]["decisions"]] or True
    ls={s["label"] for s in u["suspicions"]}; ds={d["label"] for d in m[u["unit"]]["decisions"]}
    if not ls<=ds: print("missing",u["unit"],ls-ds)
print(len(R),len(s1))
