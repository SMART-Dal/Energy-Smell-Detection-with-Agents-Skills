import ast, json, textwrap, sys
ROOT="/home/javad/energy-run/sample-apps/"
def src(unit):
    p,q=unit.split("::")
    text=open(ROOT+p).read(); lines=text.split("\n"); t=ast.parse(text)
    def find(body,parts):
        for n in body:
            if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)) and n.name==parts[0]:
                return n if len(parts)==1 else find(n.body,parts[1:])
    n=find(t.body,q.split("."))
    start=min([n.lineno]+[d.lineno for d in n.decorator_list])
    return "\n".join(lines[start-1:n.end_lineno])
SUBS=[]
def sub(id,rc,unit,edits,notes,evidence=None,extra=None):
    s=src(unit)
    for old,new in edits:
        assert s.count(old)==1,(id,old[:50],s.count(old))
        s=s.replace(old,new)
    s=textwrap.dedent(s)
    changed={unit:s}
    if extra: changed.update(extra)
    SUBS.append({"id":id,"root_cause":rc,"unit":unit,"changed":changed,"sole_caller_evidence":evidence,"notes":notes})
N="news/src/python/"
sub("C3S4-predictions-index","C3.S4",N+"evaluate.py::predictions",[(
'''    preds = []
    for news_id in news_ids:
        hit = find_hit(hits, news_id)
''','''    preds = []
    by_id = None
    for news_id in news_ids:
        if by_id is None:
            by_id = {}
            for child in hits["root"]["children"]:
                by_id.setdefault(child["fields"]["news_id"], child)
        hit = by_id.get(news_id)
''')],"C3.S4. Dict of first child per news_id replaces the per-id scan in find_hit; build is lazy so empty news_ids never touches hits; missing id still ends in TypeError on None.")
T="incremental-search/search-suggestions/count_terms.py::"
sub("C3S4-process_docs-docs-count","C3.S4",T+"process_docs",[(
'''                terms[term]["count"] = terms[term]["count"] + count
            else:
                terms[term] = {"term": term, "count": count}

    # Find number of documents containing the term
    for term in terms.keys():
        terms[term]["docs"] = sum(
            [1 if term in doc else 0 for doc in doc_counts]
        )
''','''                terms[term]["count"] = terms[term]["count"] + count
                terms[term]["docs"] = terms[term]["docs"] + 1
            else:
                terms[term] = {"term": term, "count": count, "docs": 1}
''')],"C3.S4. Document frequency counted in the first pass (a doc dict holds a term once) instead of probing every doc dict for every term. Key order term,count,docs unchanged.")
sub("C3S2-count_terms-common-once","C3.S2",T+"count_terms",[(
'''    counts = {}
''','''    counts = {}
    is_common = [word in common_words for word in doc]
'''),('''            if not any(
                map(lambda word: word in common_words, doc[i : i + win_len])
            ):''','''            if not any(is_common[i : i + win_len]):''')],"C3.S2. Membership of each token in common_words computed once per call instead of once per window it appears in.")
sub("C1S5-sample_valid_data-filter-first","C1.S5",N+"mind_data.py::MindData.sample_valid_data",[(
'''                category_indices = [ self.news_content[index]["category_index"] for index in news_indices ]
                subcategory_indices = [ self.news_content[index]["subcategory_index"] for index in news_indices ]
                entity_indices = [ self.news_content[index]["entity_index"] for index in news_indices ]
                user_index = [ impression["user_index"] ] * len(labels)
                if sum(labels) > 0 and sum(labels) != len(labels):
                    data.append([''','''                clicks = sum(labels)
                if clicks > 0 and clicks != len(labels):
                    category_indices = [ self.news_content[index]["category_index"] for index in news_indices ]
                    subcategory_indices = [ self.news_content[index]["subcategory_index"] for index in news_indices ]
                    entity_indices = [ self.news_content[index]["entity_index"] for index in news_indices ]
                    user_index = [ impression["user_index"] ] * len(labels)
                    data.append([''')],"C1.S5 (suspicion a); suspicion b (sum twice) is the same edit. Lists are built only for impressions that pass the filter; random draw order unchanged.")
sub("C10S1-remove_control_characters-translate","C10.S1","colbert-long/scripts/convert.py::remove_control_characters",[(
'''    return "".join(ch for ch in s if unicodedata.category(ch)[0]!="C")''','''    drop = {ord(ch): None for ch in set(s) if unicodedata.category(ch)[0] == "C"}
    return s.translate(drop) if drop else s''')],"C10.S1. unicodedata.category is called once per distinct character, and the removal runs in C through str.translate.")
sub("C1S8-extract_documents-tell","C1.S8","text-search/python/extract-msmarco.py::extract_documents",[(
'''        for docid in docoffset.keys():
            offset.write("{0}\\t{1}\\n".format(docid, out.tell()))
            out.write(getcontent(docid, f, docoffset))''','''        position = 0
        for docid in docoffset.keys():
            offset.write("{0}\\t{1}\\n".format(docid, position))
            content = getcontent(docid, f, docoffset)
            out.write(content)
            position += len(content.encode("utf8"))''')],"C1.S8. out.tell() on a text file flushes per document; the byte position is tracked from the encoded length (utf-8, no newline translation on Linux).")
sub("C10S4-split_text-join","C10.S4","feed-split.py::split_text",[(
'''    text = ""
    id = ""''','''    parts = []
    id = ""'''),('''            if text:
                data.append((id, header, text))
                text = ""''','''            if parts:
                data.append((id, header, "\\n" + "\\n".join(parts)))
                parts = []'''),('''            text = text + "\\n" + line''','''            parts.append(line)'''),('''    data.append((id, header, text)) #Flush any last data''','''    data.append((id, header, "\\n" + "\\n".join(parts) if parts else "")) #Flush any last data''')],"C10.S4. Section text collected as parts and joined once; the joined value is identical (leading newline, one newline per line).")
sub("C1S4-what_language-text-once","C1.S4","feed-split.py::what_language",[(
'''    z = re.match(r"{%\\s*highlight\\s*(\\w+)\\s%}", el.text)''','''    text = el.text
    z = re.match(r"{%\\s*highlight\\s*(\\w+)\\s%}", text)'''),('''    if el.text.find("curl") > 0:''','''    if text.find("curl") > 0:'''),('''    if el.text.find("import com.yahoo") > 0:''','''    if text.find("import com.yahoo") > 0:''')],"C1.S4. el.text, a subtree walk in bs4, read once.")
sub("C1S4-ndcg_score-discounts-once","C1.S4",N+"metrics.py::ndcg_score",[(
'''    best = dcg_score(y_true, y_true, k)
    actual = dcg_score(y_true, y_score, k)
    return actual / best''','''    k = min(np.shape(y_true)[-1], k)
    order = np.argsort(y_true)[::-1]
    best_true = np.take(y_true, order[:k])
    discounts = np.log2(np.arange(len(best_true)) + 2)
    best = np.sum((2 ** best_true - 1) / discounts)
    order = np.argsort(y_score)[::-1]
    actual_true = np.take(y_true, order[:k])
    actual = np.sum((2 ** actual_true - 1) / discounts)
    return actual / best''')],"C1.S4. Both dcg_score calls (same k) built the same discount vector; computed once. dcg_score is called only from ndcg_score (grep metrics.py, train_*.py).",
 "grep -rn dcg_score over the repo: only news/src/python/metrics.py:28-29 call it; dcg_score itself is left unchanged.")
sub("C8S3-add_impressions-content-once","C8.S3",N+"mind_data.py::MindData.add_impressions",[(
'''            category_indices.append(self.news_content[pos_news_index]["category_index"])
            subcategory_indices.append(self.news_content[pos_news_index]["subcategory_index"])
            entity_indices.append(self.news_content[pos_news_index]["entity_index"])''','''            pos_content = self.news_content[pos_news_index]
            category_indices.append(pos_content["category_index"])
            subcategory_indices.append(pos_content["subcategory_index"])
            entity_indices.append(pos_content["entity_index"])'''),('''                category_indices.append(self.news_content[neg_news_index]["category_index"])
                subcategory_indices.append(self.news_content[neg_news_index]["subcategory_index"])
                entity_indices.append(self.news_content[neg_news_index]["entity_index"])''','''                neg_content = self.news_content[neg_news_index]
                category_indices.append(neg_content["category_index"])
                subcategory_indices.append(neg_content["subcategory_index"])
                entity_indices.append(neg_content["entity_index"])''')],"C8.S3. news_content[idx] resolved once per item instead of three times.")
sub("C10S2-float_to_binary-bool","C10.S2","visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.float_to_binary_embedding",[(
'''np.packbits(np.where(np.array(vector) > 0, 1, 0))''','''np.packbits(np.array(vector) > 0)''')],"C10.S2. packbits takes the bool array directly; no int64 intermediate.")
sub("C3S2-prepare_sim_map-seq-length","C3.S2","visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator._prepare_similarity_map_tensor",[(
'''        for idx, vespa_sim_map in enumerate(vespa_sim_maps):''','''        if hasattr(self.processor, "image_seq_length"):
            image_seq_length = self.processor.image_seq_length
        else:
            image_seq_length = 1024
        for idx, vespa_sim_map in enumerate(vespa_sim_maps):'''),('''                if hasattr(self.processor, "image_seq_length"):
                    image_seq_length = self.processor.image_seq_length
                else:
                    image_seq_length = 1024

''','''
''')],"C3.S2. The processor attribute lookup and fallback were repeated for every cell.")
sub("C6S2-sample_images-index-first","C6.S2","text-video-search/src/python/embedding.py::sample_images",[(
'''        return np.array(images)[idx]''','''        if len(idx) == 0:
            return np.array(images)[idx]
        return np.array([images[i] for i in idx])''')],"C6.S2. Only the sampled frames are stacked; empty sample keeps the original path so the empty shape is unchanged.")
P="examples/workshop-ecommerce/preprocess.py::process_users"
sub("C3S6-process_users-limit-first","C3.S6",P,[(
'''    user_groups = df_order_products_with_metadata.groupby("user_id")''','''    if not full:
        keep_users = sorted(df_order_products_with_metadata["user_id"].dropna().unique())[:max(limit, 1)]
        df_order_products_with_metadata = df_order_products_with_metadata[
            df_order_products_with_metadata["user_id"].isin(keep_users)
        ]
    user_groups = df_order_products_with_metadata.groupby("user_id")''')],"C3.S6. When not full only the first `limit` users in sorted id order are written, so the groupby sees only their rows; the final count is min(limit, groups) as before.")
sub("C8S2-should_filter_token-compiled-default","C8.S2","visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.should_filter_token",[(
'''    def should_filter_token(token: str) -> bool:''','''    def should_filter_token(token: str, _pattern=re.compile(r"^<.*$|^\\s+$|^(?!.*\\d)(?!▁)[^\\w\\s]+$|^_.*$|^Question$|^▁$")) -> bool:'''),('''        pattern = re.compile(
            r"^<.*$|^\\s+$|^(?!.*\\d)(?!▁)[^\\w\\s]+$|^_.*$|^Question$|^▁$"
        )
        return bool(pattern.match(token))''','''        return bool(_pattern.match(token))''')],"C8.S2. Pattern compiled once at definition as a default argument; callers pass one argument.")
C="news/src/python/create_category_ctrs.py::"
sub("C10S2-category_ctrs-read_impressions-reader","C10.S2",C+"read_impressions_file",[(
'''        field_list = ["id", "user_id", "timestamp", "history", "impressions"]
        reader = csv.DictReader(f, delimiter="\\t", fieldnames=field_list)
        for line in reader:
            for impression in line["impressions"].split(" "):''','''        reader = csv.reader(f, delimiter="\\t")
        for line in reader:
            if not line:
                continue
            for impression in line[4].split(" "):''')],"C10.S2. csv.reader and an index replace the 5-key dict DictReader builds per row (blank rows skipped by both).")
sub("C2S1-lookup_news_index-inline","C2.S1",N+"mind_data.py::MindData.lookup_news_index",[(
'''        return self.lookup_index(news_id, self.news_map)''','''        map = self.news_map
        if news_id not in map:
            map[news_id] = len(map)
        return map[news_id]'''.replace("\n        ","\n        "))],"C2.S1. lookup_index's body inlined in the forwarder; lookup_index is unchanged and still used by the other lookup_* methods.")
sub("C10S3-train_cold_start-write_embeddings-tolist-once","C10.S3",N+"train_cold_start.py::write_embeddings",[(
'''        for id, index in id_to_index_map.items():
            f.write("{}\\t{}\\n".format(id, ",".join(["%.6f" % i for i in embeddings[index].tolist()])))''','''        rows = embeddings.tolist()
        for id, index in id_to_index_map.items():
            f.write("{}\\t{}\\n".format(id, ",".join(["%.6f" % i for i in rows[index]])))''')],"C10.S3. One tolist() of the whole matrix instead of one tensor index and tolist() per id.")
sub("C3S5-read_news-lazy-abstract","C3.S5",N+"mind_data.py::MindData.read_news",[(
'''                abstract_entities = json.loads(news_data[7]) if len(news_data) > 7 else []

                entities_to_keep = 2
                entity_ids = []
                self.add_entities(entity_ids, title_entities)
                self.add_entities(entity_ids, abstract_entities)''','''
                entities_to_keep = 2
                entity_ids = []
                self.add_entities(entity_ids, title_entities)
                if len(entity_ids) < entities_to_keep:
                    abstract_entities = json.loads(news_data[7]) if len(news_data) > 7 else []
                    self.add_entities(entity_ids, abstract_entities)''')],"C3.S5. The abstract entity JSON is parsed only when the title entities gave fewer than the two ids that are kept.")
# lower-priority ones
sub("C1S1-process_docs-total_count","C1.S1",T+"process_docs",[(
'''        total_count = sum([count for count in counts.values()])
''','')],"C1.S1. total_count was computed per document and never read.")
sub("C10S3-accepted_words-process_docs-update","C10.S3","incremental-search/search-suggestions/accepted_words.py::process_docs",[(
'''            for term in clean_text(doc['fields']['title']):
                term_set.add(term)
            for term in clean_text(doc['fields']['content']):
                term_set.add(term)''','''            term_set.update(clean_text(doc['fields']['title']))
            term_set.update(clean_text(doc['fields']['content']))''')],"C10.S3. set.update takes the whole list in one call.")
sub("C3S2-select_documents-bound","C3.S2","text-search/python/sample-queries-and-documents.py::select_documents",[(
'''    while len(selected_doc_ids) < min(len(docids), documents_to_generate):''','''    target = min(len(docids), documents_to_generate)
    while len(selected_doc_ids) < target:''')],"C3.S2. Constant bound computed once.")
sub("C10S2-evaluate-read_impressions-reader","C10.S2",N+"evaluate.py::read_impressions_file",[(
'''        field_list = ["id", "user_id", "timestamp", "history", "impressions"]
        reader = csv.DictReader(f, delimiter="\\t", fieldnames=field_list)
        for line in reader:
            user_id = line["user_id"]''','''        reader = csv.reader(f, delimiter="\\t")
        for line in reader:
            if not line:
                continue
            user_id = line[1]'''),('''line["impressions"].split(" ")''','''line[4].split(" ")''')],"C10.S2. csv.reader with indexes replaces DictReader's per-row dict.")
sub("C8S3-read_bert_embeddings_from_file-news-once","C8.S3",N+"train_cold_start.py::read_bert_embeddings_from_file",[(
'''    with io.open(embeddings_file, "r", encoding="utf-8") as f:''','''    news_map = data_loader.news()
    with io.open(embeddings_file, "r", encoding="utf-8") as f:'''),('''            if news_id not in data_loader.news():''','''            if news_id not in news_map:'''),('''            news_index = data_loader.news()[news_id]''','''            news_index = news_map[news_id]''')],"C8.S3. data_loader.news() returns self.news_map (mind_data.py); fetched once.")
sub("C10S2-write_json_file-replace","C10.S2",T+"write_json_file",[(
'''re.sub(r" ", "/", term)''','''term.replace(" ", "/")''')],"C10.S2. A literal substitution through the regex engine becomes str.replace.")
G="visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.gen_similarity_maps"
sub("C6S2-gen_similarity_maps-no-copy","C6.S2",G,[(
'''        processed_images, original_images, original_sizes = [], [], []
        for img in images:
            img_pil = self._load_image(img)
            original_images.append(img_pil.copy())
            original_sizes.append(img_pil.size)
            processed_images.append(img_pil)''','''        original_images, original_sizes = [], []
        for img in images:
            img_pil = self._load_image(img)
            original_images.append(img_pil)
            original_sizes.append(img_pil.size)''')],"C6.S2 (suspicion c). Drops the pixel copy and the second list nobody reads.")
sub("C3S2-gen_similarity_maps-filter-once","C3.S2",G,[(
'''        for idx, img in enumerate(original_images):
            for token_idx, token in token_idx_map.items():
                if self.should_filter_token(token):
                    continue
''','''        kept_tokens = [
            (token_idx, token)
            for token_idx, token in token_idx_map.items()
            if not self.should_filter_token(token)
        ]
        for idx, img in enumerate(original_images):
            for token_idx, token in kept_tokens:
''')],"C3.S2 (suspicion b). Token filter evaluated once per token instead of once per image per token.")
open("/home/javad/energy-run/sample-apps/submissions.jsonl","w").write("\n".join(json.dumps({**s,"agent_measurement":None} if False else s,ensure_ascii=False) for s in SUBS)+"\n")
print(len(SUBS))
