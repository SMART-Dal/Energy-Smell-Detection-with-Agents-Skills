import ast, json, textwrap, sys
REPO="/home/javad/energy-run/sample-apps/"
def get_src(path, qual):
    src=open(REPO+path).read()
    tree=ast.parse(src)
    parts=qual.split(".")
    node=tree
    for p in parts:
        for ch in ast.iter_child_nodes(node):
            if isinstance(ch,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)) and ch.name==p:
                node=ch;break
        else: raise KeyError(qual)
    lines=src.split("\n")
    start=min([node.lineno]+[d.lineno for d in node.decorator_list])-1
    return textwrap.dedent("\n".join(lines[start:node.end_lineno]))+"\n" if False else textwrap.dedent("\n".join(lines[start:node.end_lineno]))
subs=[]
def sub(id, unit, edits, notes, evidence=None, full=None, extra=None):
    path,qual=unit.split("::")
    if full is not None:
        new=full
    else:
        new=get_src(path,qual)
        for old,rep in edits:
            if "." in qual:
                dd=lambda t:"\n".join(l[4:] if l.startswith("    ") else l for l in t.split("\n"))
                old,rep=dd(old),dd(rep)
            assert new.count(old)==1,(id,old,new.count(old))
            new=new.replace(old,rep)
    changed={unit:new}
    if extra: changed.update(extra)
    subs.append({"id":id,"unit":unit,"changed":changed,"sole_caller_evidence":evidence,"notes":notes})

CT="incremental-search/search-suggestions/count_terms.py"
sub("terms-docs-count",CT+"::process_docs",[
("""            if term in terms:
                terms[term]["count"] = terms[term]["count"] + count
            else:
                terms[term] = {"term": term, "count": count}

    # Find number of documents containing the term
    for term in terms.keys():
        terms[term]["docs"] = sum(
            [1 if term in doc else 0 for doc in doc_counts]
        )

    return terms""","""            if term in terms:
                terms[term]["count"] = terms[term]["count"] + count
                terms[term]["docs"] += 1
            else:
                terms[term] = {"term": term, "count": count, "docs": 1}

    return terms""")],
"Counts documents per term in the summing loop; each per-document dict holds a term once so the count equals the original scan. Key order of the inner dicts (term, count, docs) is unchanged.")
sub("terms-total-count",CT+"::process_docs",[
("""        total_count = sum([count for count in counts.values()])
""","")],"Only deletes the unused total_count sum; the quadratic document-frequency scan is left as in the original.")
sub("terms-window-flags",CT+"::count_terms",None or [],"",full='''def count_terms(doc, term_length=1, common_words=set()):
    counts = {}
    pref = [0]
    for word in doc:
        pref.append(pref[-1] + (word in common_words))
    for win_len in range(1, term_length + 1):
        for i in range(len(doc) + 1 - win_len):
            if pref[i + win_len] == pref[i]:
                term = " ".join(doc[i : i + win_len])
                if  len(term) > 0 and not term.isspace():
                    counts[term] = counts.get(term, 0) + 1
    return counts''')
subs[-1]["notes"]="Tests each word against common_words once and uses a prefix sum so a window is valid when it contains no flagged word; only valid windows are sliced and joined."
sub("terms-merge-counts",CT+"::process_doc",[
("""        return {
            term: title_counts.get(term, 0) + content_counts.get(term, 0)
            for term in list(title_counts.keys()) + list(content_counts.keys())
        }""","""        merged = dict(title_counts)
        for term, count in content_counts.items():
            merged[term] = merged.get(term, 0) + count
        return merged""")],"Key order is title keys first then new content keys, as in the original comprehension.")
sub("terms-replace-slash",CT+"::write_json_file",[
("""re.sub(r" ", "/", term)""","""term.replace(" ", "/")""")],"re.sub of a single space replaced with str.replace.")

sub("split-text-join","feed-split.py::split_text",[
("""    text = ""
    id = ""
    data = []
    for line in lines:
        if line.startswith("#"):
            if text:
                data.append((id, header, text))
                text = ""
            header = line.lstrip("#")
            id = "-".join(header.split()).lower()
        else:
            text = text + "\\n" + line

    data.append((id, header, text)) #Flush any last data""","""    parts = []
    id = ""
    data = []
    for line in lines:
        if line.startswith("#"):
            if parts:
                data.append((id, header, "\\n" + "\\n".join(parts)))
                parts = []
            header = line.lstrip("#")
            id = "-".join(header.split()).lower()
        else:
            parts.append(line)

    data.append((id, header, "\\n" + "\\n".join(parts) if parts else "")) #Flush any last data""")],
"Each section's lines are collected and joined once at the flush; the text is '\\n' + '\\n'.join(lines), identical to the repeated concatenation, and an empty section stays ''.")
sub("lang-text-once","feed-split.py::what_language",[
("""    z = re.match(r"{%\\s*highlight\\s*(\\w+)\\s%}", el.text)""","""    text = el.text
    z = re.match(r"{%\\s*highlight\\s*(\\w+)\\s%}", text)"""),
("""    if el.text.find("curl") > 0:""","""    if text.find("curl") > 0:"""),
("""    if el.text.find("import com.yahoo") > 0:""","""    if text.find("import com.yahoo") > 0:""")],"el.text read once.")

sub("ctrl-translate","colbert-long/scripts/convert.py::remove_control_characters",[],"",full='''def remove_control_characters(s):
    if not isinstance(s, str):
        return "".join(ch for ch in s if unicodedata.category(ch)[0]!="C")
    table = getattr(remove_control_characters, "_table", None)
    if table is None:
        class _Drop(dict):
            def __missing__(self, cp):
                value = None if unicodedata.category(chr(cp))[0] == "C" else cp
                self[cp] = value
                return value
        table = remove_control_characters._table = _Drop()
    return s.translate(table)''')
subs[-1]["notes"]="Self-filling translate table kept as a function attribute; non-str input falls back to the original generator so exception behaviour is unchanged. The module does network I/O at import, so it is loaded statement by statement."

MD="news/src/python/mind_data.py"
sub("valid-filter-first",MD+"::MindData.sample_valid_data",[
("""                category_indices = [ self.news_content[index]["category_index"] for index in news_indices ]
                subcategory_indices = [ self.news_content[index]["subcategory_index"] for index in news_indices ]
                entity_indices = [ self.news_content[index]["entity_index"] for index in news_indices ]
                user_index = [ impression["user_index"] ] * len(labels)
                if sum(labels) > 0 and sum(labels) != len(labels):
""","""                if sum(labels) > 0 and sum(labels) != len(labels):
                    category_indices = [ self.news_content[index]["category_index"] for index in news_indices ]
                    subcategory_indices = [ self.news_content[index]["subcategory_index"] for index in news_indices ]
                    entity_indices = [ self.news_content[index]["entity_index"] for index in news_indices ]
                    user_index = [ impression["user_index"] ] * len(labels)
""")],"The list building moves inside the filter. random.random() is still called once per impression, so the RNG stream is the same.")
sub("add-impr-lookup",MD+"::MindData.add_impressions",[
("""            category_indices.append(self.news_content[pos_news_index]["category_index"])
            subcategory_indices.append(self.news_content[pos_news_index]["subcategory_index"])
            entity_indices.append(self.news_content[pos_news_index]["entity_index"])""","""            content = self.news_content[pos_news_index]
            category_indices.append(content["category_index"])
            subcategory_indices.append(content["subcategory_index"])
            entity_indices.append(content["entity_index"])"""),
("""                category_indices.append(self.news_content[neg_news_index]["category_index"])
                subcategory_indices.append(self.news_content[neg_news_index]["subcategory_index"])
                entity_indices.append(self.news_content[neg_news_index]["entity_index"])""","""                content = self.news_content[neg_news_index]
                category_indices.append(content["category_index"])
                subcategory_indices.append(content["subcategory_index"])
                entity_indices.append(content["entity_index"])""")],"One news_content lookup per sampled row.")

sub("predictions-dict","news/src/python/evaluate.py::predictions",[],"",full='''def predictions(hits, news_ids):
    preds = []
    if not news_ids:
        return preds
    by_id = {}
    for child in hits["root"]["children"]:
        by_id.setdefault(child["fields"]["news_id"], child)
    for news_id in news_ids:
        hit = by_id.get(news_id)
        relevance = hit["relevance"]
        preds.append(relevance)
    return preds''')
subs[-1]["sole_caller_evidence"]=None
subs[-1]["notes"]="First hit per news_id kept (find_hit returns the first match). Missing id still gives None and a TypeError. find_hit is left in place and unused by this path; grep shows predictions is called only from calc_impression."

sub("write-emb-tolist","news/src/python/train_cold_start.py::write_embeddings",[
("""    with open(os.path.join(data_dir, file_name), "w") as f:
        for id, index in id_to_index_map.items():
            f.write("{}\\t{}\\n".format(id, ",".join(["%.6f" % i for i in embeddings[index].tolist()])))""","""    rows = embeddings.tolist() if id_to_index_map else None
    with open(os.path.join(data_dir, file_name), "w") as f:
        for id, index in id_to_index_map.items():
            f.write("{}\\t{}\\n".format(id, ",".join(["%.6f" % i for i in rows[index]])))""")],"Converts the embedding matrix to nested lists once instead of one tensor view and list per id.")
sub("bert-write-join","news/src/python/create_bert_embeddings.py::write_embedding",[],"",full='''def write_embedding(f, embedding):
    f.write("\\t" + ",".join(["%.4f" % num for num in embedding]))''')
subs[-1]["notes"]="One write per document instead of about 1000."
sub("convert-file-dumps","news/src/python/convert_to_vespa_format.py::convert_file",[
("            json.dump(doc, output)","            output.write(json.dumps(doc))")],"json.dumps uses the C encoder; same bytes as json.dump.")
sub("user-emb-tolist","news/src/python/convert_embeddings_to_vespa_format.py::convert_user_embeddings",[
('''",".join(["%.6f" % v for v in embedding])''','''",".join(["%.6f" % v for v in embedding.tolist()])''')],"tolist() gives Python floats of the same value as the float32 elements.")

sub("liquid-early-return","test/test.py::process_liquid",[],"",full='''def process_liquid(command):
    if "{" not in command:
        return command
    for key, value in liquid_transforms.items():
        command = re.sub(key, value, command)

    return command''')
subs[-1]["notes"]="Every transform pattern needs a literal '{' to match (site variables {{...}} and {% ... %} macros), so a command without one is returned unchanged. A non-str `command` still reaches `in` and raises TypeError like re.sub would."
sub("parse-page-find-all","test/test.py::parse_page",[
("""soup.find_all(lambda tag: (tag.name == "pre" or tag.name == "div" or tag.name == "p") and tag.has_attr("data-test"))""","""soup.find_all(["pre", "div", "p"], attrs={"data-test": True})""")],"Same tags in document order, filtered by bs4's matcher instead of a Python callback per tag.")
sub("parse-file-typename","test/test.py::parse_file",[
("""if "ProcessingInstruction" in str(type(line)):""","""if "ProcessingInstruction" in type(line).__name__:""")],"Same truth value: the class name contains the substring exactly when str(type(line)) does, since the module path has none.")

CP="visual-retrieval-colpali/src/backend/colpali.py"
sub("simmap-dead-copy",CP+"::SimMapGenerator.gen_similarity_maps",[
("""        processed_images, original_images, original_sizes = [], [], []
        for img in images:
            img_pil = self._load_image(img)
            original_images.append(img_pil.copy())
            original_sizes.append(img_pil.size)
            processed_images.append(img_pil)""","""        original_images, original_sizes = [], []
        for img in images:
            img_pil = self._load_image(img)
            original_images.append(img_pil)
            original_sizes.append(img_pil.size)""")],"Removes the unused processed_images list and the full-image copy; _blend_image never reads or mutates its img argument.")
sub("simmap-filter-once",CP+"::SimMapGenerator.gen_similarity_maps",[
("""        for idx, img in enumerate(original_images):
            for token_idx, token in token_idx_map.items():
                if self.should_filter_token(token):
                    continue

""","""        kept_tokens = [
            (token_idx, token)
            for token_idx, token in token_idx_map.items()
            if not self.should_filter_token(token)
        ]
        for idx, img in enumerate(original_images):
            for token_idx, token in kept_tokens:
""")],"Token filtering is done once per query token instead of once per image x token.")
sub("simmap-seqlen-hoist",CP+"::SimMapGenerator._prepare_similarity_map_tensor",[
("""        for idx, vespa_sim_map in enumerate(vespa_sim_maps):
            for cell in vespa_sim_map["quantized"]["cells"]:
                patch = int(cell["address"]["patch"])
                query_token = int(cell["address"]["querytoken"])
                value = cell["value"]
                if hasattr(self.processor, "image_seq_length"):
                    image_seq_length = self.processor.image_seq_length
                else:
                    image_seq_length = 1024

""","""        if hasattr(self.processor, "image_seq_length"):
            image_seq_length = self.processor.image_seq_length
        else:
            image_seq_length = 1024
        for idx, vespa_sim_map in enumerate(vespa_sim_maps):
            for cell in vespa_sim_map["quantized"]["cells"]:
                patch = int(cell["address"]["patch"])
                query_token = int(cell["address"]["querytoken"])
                value = cell["value"]

""")],"image_seq_length is looked up once per call instead of once per cell.")

sub("vespa-packbits-bool","visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.float_to_binary_embedding",[
("np.packbits(np.where(np.array(vector) > 0, 1, 0))","np.packbits(np.array(vector) > 0)")],"packbits on the boolean mask gives the same bytes as on the 0/1 int64 array.")
sub("feed-packbits-bool","visual-retrieval-colpali/prepare_feed_deploy.py::float_to_binary_embedding",[
("np.packbits(np.where(np.array(v) > 0, 1, 0))","np.packbits(np.array(v) > 0)")],"Same edit as vespa-packbits-bool, in the offline feed script's own function.")

sub("msmarco-tell","text-search/python/extract-msmarco.py::extract_documents",[
("""        for docid in docoffset.keys():
            offset.write("{0}\\t{1}\\n".format(docid, out.tell()))
            out.write(getcontent(docid, f, docoffset))""","""        position = 0
        for docid in docoffset.keys():
            offset.write("{0}\\t{1}\\n".format(docid, position))
            content = getcontent(docid, f, docoffset)
            out.write(content)
            position += len(content.encode("utf8"))""")],"Keeps a running byte offset instead of calling tell() on a text file; the file is opened fresh (position 0) and written only here.")

CS="use-case-shopping/create_suggestions.py"
sub("suggest-filter-any",CS+"::filter",[
("""	for f in filters:
		if f in text:
			return True
	return False""","""	if any(map(text.__contains__, filters)):
		return True
	return False""")],"Substring loop runs in C via any(map(...)).")
sub("suggest-filter-dead",CS+"::filter",[
("""	if text.startswith("/") and len(text) < 3:
		return True
""","")],"Deletes the unreachable branch (len(text) < 3 already returned above).")
sub("suggest-content-any",CS+"::filter_content",[
("""	for f in invalid_starts:
		if text.startswith(f):
			return True
	return False""","""	return any(map(text.startswith, invalid_starts))""")],"Loop over prefixes done in C.")

sub("recall-vectorised","billion-scale-vector-search/app/src/main/python/recall.py::compute_recall_with_distance_ties",[
("""    set_end = gt_size
    for i in range(count, gt_size):
      is_close = abs(dist_tie_check - true_dists[i] ) < 1e-6 
      if not is_close:
        set_end = i
        break
""","""    set_end = gt_size
    not_close = np.flatnonzero(np.abs(dist_tie_check - true_dists[count:gt_size]) >= 1e-6)
    if not_close.size:
      set_end = count + int(not_close[0])
""")],"Vectorised tie search. NaN distances: the original treats NaN as not close (not NaN<1e-6 is True); >= on NaN is False, so NaN differs; inputs are finite distances.")

sub("sample-images-select","text-video-search/src/python/embedding.py::sample_images",[
("return np.array(images)[idx]","return np.array([images[i] for i in idx])")],"Stacks only the sampled frames.")

sub("orders-agg-list","examples/workshop-ecommerce/preprocess.py::process_orders",[
(""".agg({"product_id": lambda x: list(x)})""",""".agg({"product_id": list})""")],"agg with the list builtin.")

with open("/home/javad/energy-run/sample-apps/submissions.jsonl","w") as f:
    for s in subs: f.write(json.dumps(s)+"\n")
print(len(subs),[s["id"] for s in subs])
