import json, sys
sys.path.insert(0, "/tmp/ee")
from lib import src, edit
S = []
def sub(id, unit, changed, evidence=None, notes=""):
    S.append({"id": id, "unit": unit, "changed": changed, "sole_caller_evidence": evidence, "notes": notes})

CT = "incremental-search/search-suggestions/count_terms.py"
sub("count-terms-docfreq-one-pass", CT+"::process_docs", {CT+"::process_docs": edit(CT, "process_docs",
 ('''                terms[term]["count"] = terms[term]["count"] + count
            else:
                terms[term] = {"term": term, "count": count}

    # Find number of documents containing the term
    for term in terms.keys():
        terms[term]["docs"] = sum(
            [1 if term in doc else 0 for doc in doc_counts]
        )
''', '''                terms[term]["count"] = terms[term]["count"] + count
                terms[term]["docs"] += 1
            else:
                terms[term] = {"term": term, "count": count, "docs": 1}
'''))}, notes="Each per-document dict has unique keys, so counting +1 per (doc, term) in the existing pass equals the per-term scan over all docs. Key order of each term dict stays term, count, docs.")
sub("count-terms-drop-unused-total", CT+"::process_docs", {CT+"::process_docs": edit(CT, "process_docs",
 ('''        total_count = sum([count for count in counts.values()])
''', ''))}, notes="total_count was never read.")
sub("count-terms-merge-without-key-lists", CT+"::process_doc", {CT+"::process_doc": edit(CT, "process_doc",
 ('''        return {
            term: title_counts.get(term, 0) + content_counts.get(term, 0)
            for term in list(title_counts.keys()) + list(content_counts.keys())
        }''', '''        merged = dict(title_counts)
        for term, count in content_counts.items():
            merged[term] = merged.get(term, 0) + count
        return merged'''))}, notes="Same key order: title keys first, then content-only keys.")
sub("count-terms-common-flags-once", CT+"::count_terms", {CT+"::count_terms": edit(CT, "count_terms",
 ('''    counts = {}
''', '''    counts = {}
    is_common = [word in common_words for word in doc]
'''),
 ('''            if not any(
                map(lambda word: word in common_words, doc[i : i + win_len])
            ):''', '''            if not any(is_common[i : i + win_len]):'''))}, notes="Common-word membership is computed once per token instead of via a lambda per word per window.")
EV = "news/src/python/evaluate.py"
sub("news-predictions-hit-index", EV+"::predictions", {EV+"::predictions": '''def predictions(hits, news_ids):
    preds = []
    if not news_ids:
        return preds
    hit_by_id = {}
    for child in hits["root"]["children"]:
        hit_by_id.setdefault(child["fields"]["news_id"], child)
    for news_id in news_ids:
        hit = hit_by_id.get(news_id)
        relevance = hit["relevance"]
        preds.append(relevance)
    return preds
'''}, notes="setdefault keeps the first matching child, as find_hit does; a missing id gives None and the same TypeError. find_hit itself is unchanged.")
CV = "colbert-long/scripts/convert.py"
sub("colbert-control-chars-per-distinct", CV+"::remove_control_characters", {CV+"::remove_control_characters": '''def remove_control_characters(s):
    control = {ord(ch): None for ch in set(s) if unicodedata.category(ch)[0] == "C"}
    return s.translate(control) if control else s
'''}, notes="unicodedata.category is evaluated once per distinct character; str.translate deletes the control characters in C.")
FS = "feed-split.py"
sub("feed-split-split-text-join", FS+"::split_text", {FS+"::split_text": edit(FS, "split_text",
 ('''    header = ""
    text = ""
''', '''    header = ""
    parts = []
'''),
 ('''            if text:
                data.append((id, header, text))
                text = ""''', '''            if parts:
                data.append((id, header, "".join(parts)))
                parts = []'''),
 ('''            text = text + "\\n" + line''', '''            parts.append("\\n" + line)'''),
 ('''    data.append((id, header, text)) #Flush any last data''', '''    data.append((id, header, "".join(parts))) #Flush any last data'''))},
 notes="`text + \"\\n\" + line` copies the whole section per line because the first + is not followed by a store; the parts list is joined once per section.")
sub("feed-split-what-language-text-once", FS+"::what_language", {FS+"::what_language": edit(FS, "what_language",
 ('''    z = re.match(r"{%\\s*highlight\\s*(\\w+)\\s%}", el.text)''', '''    text = el.text
    z = re.match(r"{%\\s*highlight\\s*(\\w+)\\s%}", text)'''),
 ('''    if el.text.find("curl") > 0:''', '''    if text.find("curl") > 0:'''),
 ('''    if el.text.find("import com.yahoo") > 0:''', '''    if text.find("import com.yahoo") > 0:'''))})
CP = "visual-retrieval-colpali/src/backend/colpali.py"
sub("colpali-simmap-hoist-seq-length", CP+"::SimMapGenerator._prepare_similarity_map_tensor", {CP+"::SimMapGenerator._prepare_similarity_map_tensor": edit(CP, "SimMapGenerator._prepare_similarity_map_tensor",
 ('''        for idx, vespa_sim_map in enumerate(vespa_sim_maps):''', '''        image_seq_length = None
        for idx, vespa_sim_map in enumerate(vespa_sim_maps):'''),
 ('''                if hasattr(self.processor, "image_seq_length"):
                    image_seq_length = self.processor.image_seq_length
                else:
                    image_seq_length = 1024
''', '''                if image_seq_length is None:
                    if hasattr(self.processor, "image_seq_length"):
                        image_seq_length = self.processor.image_seq_length
                    else:
                        image_seq_length = 1024
'''))}, notes="The processor attribute is resolved at the first cell instead of every cell; still not touched when there are no cells.")
sub("colpali-simmap-single-scatter", CP+"::SimMapGenerator._prepare_similarity_map_tensor", {CP+"::SimMapGenerator._prepare_similarity_map_tensor": edit(CP, "SimMapGenerator._prepare_similarity_map_tensor",
 ('''        for idx, vespa_sim_map in enumerate(vespa_sim_maps):''', '''        map_idx, token_idx, patch_idx, values = [], [], [], []
        for idx, vespa_sim_map in enumerate(vespa_sim_maps):'''),
 ('''                vespa_sim_map_tensor[
                    idx,
                    query_token,
                    patch // self.n_patch,
                    patch % self.n_patch,
                ] = value
''', '''                map_idx.append(idx)
                token_idx.append(query_token)
                patch_idx.append(patch)
                values.append(value)
        if values:
            patches = torch.tensor(patch_idx)
            vespa_sim_map_tensor[
                torch.tensor(map_idx),
                torch.tensor(token_idx),
                patches // self.n_patch,
                patches % self.n_patch,
            ] = torch.tensor(values, dtype=vespa_sim_map_tensor.dtype)
'''))}, notes="One advanced-index assignment replaces a tensor __setitem__ per cell. Values are cast to the tensor's float32 as the per-cell assignment does.")
sub("colpali-gen-simmaps-no-copy", CP+"::SimMapGenerator.gen_similarity_maps", {CP+"::SimMapGenerator.gen_similarity_maps": edit(CP, "SimMapGenerator.gen_similarity_maps",
 ('''        processed_images, original_images, original_sizes = [], [], []''', '''        original_images, original_sizes = [], []'''),
 ('''            original_images.append(img_pil.copy())
            original_sizes.append(img_pil.size)
            processed_images.append(img_pil)''', '''            original_images.append(img_pil)
            original_sizes.append(img_pil.size)'''))}, notes="processed_images was never read and the copied image is only passed to _blend_image, which does not read it.")
sub("colpali-gen-simmaps-size-only", CP+"::SimMapGenerator.gen_similarity_maps", {CP+"::SimMapGenerator.gen_similarity_maps": edit(CP, "SimMapGenerator.gen_similarity_maps",
 ('''        processed_images, original_images, original_sizes = [], [], []
        for img in images:
            img_pil = self._load_image(img)
            original_images.append(img_pil.copy())
            original_sizes.append(img_pil.size)
            processed_images.append(img_pil)''', '''        original_sizes = []
        for img in images:
            try:
                if isinstance(img, Path):
                    img_pil = Image.open(img)
                elif isinstance(img, str):
                    img_pil = Image.open(BytesIO(base64.b64decode(img)))
                else:
                    img_pil = None
            except Exception as e:
                raise ValueError(f"Failed to load image: {e}")
            original_sizes.append(img_pil.size)
        original_images = [None] * len(original_sizes)'''))}, notes="_blend_image never reads its img argument; only the size is needed, which Image.open reads from the header without decoding pixels or converting to RGB. Same ValueError on unreadable input, same AttributeError for unsupported types.")
sub("colpali-blend-colormap-bytes", CP+"::SimMapGenerator._blend_image", {CP+"::SimMapGenerator._blend_image": edit(CP, "SimMapGenerator._blend_image",
 ('''        heatmap = self.colormap(sim_map_normalized)
        heatmap_img = Image.fromarray((heatmap * 255).astype(np.uint8)).convert("RGBA")''', '''        heatmap_img = Image.fromarray(self.colormap(sim_map_normalized, bytes=True))'''))}, notes="matplotlib's bytes=True applies (lut*255).astype(uint8) to the lookup table, the same per-element operation as before, so the RGBA image is identical; convert('RGBA') on an RGBA image was a copy.")
sub("colpali-filter-token-compiled", CP+"::SimMapGenerator.should_filter_token", {CP+"::SimMapGenerator.should_filter_token": edit(CP, "SimMapGenerator.should_filter_token",
 ('''        pattern = re.compile(
            r"^<.*$|^\\s+$|^(?!.*\\d)(?!▁)[^\\w\\s]+$|^_.*$|^Question$|^▁$"
        )
        return bool(pattern.match(token))''', '''        global _SHOULD_FILTER_TOKEN_PATTERN
        try:
            pattern = _SHOULD_FILTER_TOKEN_PATTERN
        except NameError:
            pattern = _SHOULD_FILTER_TOKEN_PATTERN = re.compile(
                r"^<.*$|^\\s+$|^(?!.*\\d)(?!▁)[^\\w\\s]+$|^_.*$|^Question$|^▁$"
            )
        return bool(pattern.match(token))'''))}, notes="The compiled pattern is kept in a module-level value only this method reads, skipping re.compile's cache lookup per call.")
VA = "visual-retrieval-colpali/src/backend/vespa_app.py"
sub("vespa-app-packbits-bool", VA+"::VespaQueryClient.float_to_binary_embedding", {VA+"::VespaQueryClient.float_to_binary_embedding": edit(VA, "VespaQueryClient.float_to_binary_embedding",
 ('''                np.packbits(np.where(np.array(vector) > 0, 1, 0))''', '''                np.packbits(np.array(vector) > 0)'''))}, notes="packbits accepts the boolean mask; the int64 0/1 array from np.where is not needed. Same bits.")
sub("vespa-app-format-q-embs-tolist-once", VA+"::VespaQueryClient.format_q_embs", {VA+"::VespaQueryClient.format_q_embs": edit(VA, "VespaQueryClient.format_q_embs",
 ('''        return {idx: emb.tolist() for idx, emb in enumerate(q_embs)}''', '''        return dict(enumerate(q_embs.tolist()))'''))}, notes="One tolist of the whole tensor instead of a row tensor and tolist per row.")
PF = "visual-retrieval-colpali/prepare_feed_deploy.py"
sub("prepare-feed-packbits-bool", PF+"::float_to_binary_embedding", {PF+"::float_to_binary_embedding": edit(PF, "float_to_binary_embedding",
 ('''            np.packbits(np.where(np.array(v) > 0, 1, 0)).astype(np.int8).tolist()''', '''            np.packbits(np.array(v) > 0).astype(np.int8).tolist()'''))})
TV = "text-video-search/src/python/embedding.py"
sub("video-sample-images-select-first", TV+"::sample_images", {TV+"::sample_images": edit(TV, "sample_images",
 ('''        return np.array(images)[idx]''', '''        return np.array([images[i] for i in idx])'''))}, notes="Only the sampled frames are stacked, instead of stacking every frame and fancy-indexing a second copy.")
CB = "news/src/python/create_bert_embeddings.py"
sub("bert-write-embedding-one-write", CB+"::write_embedding", {CB+"::write_embedding": '''def write_embedding(f, embedding):
    f.write("\\t" + ",".join(["%.4f" % num for num in embedding]))
'''}, notes="Same bytes in one write call instead of two per float.")
TC = "news/src/python/train_cold_start.py"
sub("cold-start-write-embeddings-tolist-once", TC+"::write_embeddings", {TC+"::write_embeddings": edit(TC, "write_embeddings",
 ('''        for id, index in id_to_index_map.items():
            f.write("{}\\t{}\\n".format(id, ",".join(["%.6f" % i for i in embeddings[index].tolist()])))''', '''        rows = embeddings.tolist()
        for id, index in id_to_index_map.items():
            f.write("{}\\t{}\\n".format(id, ",".join(["%.6f" % i for i in rows[index]])))'''))}, notes="The whole tensor is converted once after the file is opened; per-id rows come from the Python list, so no tensor indexing (and no autograd node on grad tensors) per id.")
CE = "news/src/python/convert_embeddings_to_vespa_format.py"
sub("news-read-embeddings-fromstring", CE+"::read_embeddings", {CE+"::read_embeddings": edit(CE, "read_embeddings",
 ('''            embeddings[id] = np.array(vector.split(","), dtype=np.float32)''', '''            embeddings[id] = np.fromstring(vector, dtype=np.float32, sep=",")'''))}, notes="Parses the comma-separated text in C instead of building a list of strings. Equivalence of float32 rounding is left to the check.")
sub("news-convert-user-embeddings-tolist", CE+"::convert_user_embeddings", {CE+"::convert_user_embeddings": edit(CE, "convert_user_embeddings",
 ('''            embedding_str = ",".join(["%.6f" % v for v in embedding])''', '''            embedding_str = ",".join(["%.6f" % v for v in embedding.tolist()])'''))}, notes="float32 to Python float is exact, and %-formatting a numpy float32 converts it to the same float.")
MD = "news/src/python/mind_data.py"
sub("mind-valid-filter-first", MD+"::MindData.sample_valid_data", {MD+"::MindData.sample_valid_data": edit(MD, "MindData.sample_valid_data",
 ('''                category_indices = [ self.news_content[index]["category_index"] for index in news_indices ]
                subcategory_indices = [ self.news_content[index]["subcategory_index"] for index in news_indices ]
                entity_indices = [ self.news_content[index]["entity_index"] for index in news_indices ]
                user_index = [ impression["user_index"] ] * len(labels)
                if sum(labels) > 0 and sum(labels) != len(labels):
''', '''                if sum(labels) > 0 and sum(labels) != len(labels):
                    category_indices = [ self.news_content[index]["category_index"] for index in news_indices ]
                    subcategory_indices = [ self.news_content[index]["subcategory_index"] for index in news_indices ]
                    entity_indices = [ self.news_content[index]["entity_index"] for index in news_indices ]
                    user_index = [ impression["user_index"] ] * len(labels)
'''))}, notes="random.random() is still drawn for every impression, so the RNG stream is unchanged.")
sub("mind-valid-sum-once", MD+"::MindData.sample_valid_data", {MD+"::MindData.sample_valid_data": edit(MD, "MindData.sample_valid_data",
 ('''                if sum(labels) > 0 and sum(labels) != len(labels):''', '''                num_clicked = sum(labels)
                if num_clicked > 0 and num_clicked != len(labels):'''))})
PP = "examples/workshop-ecommerce/preprocess.py"
sub("preprocess-users-no-iterrows", PP+"::process_users", {PP+"::process_users": edit(PP, "process_users",
 ('''            for _, purchase in user_purchases_df.iterrows():
                purchase_struct = {
                    "order_dow": int(purchase["order_dow"]),
                    "order_hour_of_day": int(purchase["order_hour_of_day"]),
                    "order_id": int(purchase["order_id"]),
                    "product_id": int(purchase["product_id"]),
                }''', '''            for order_dow, order_hour_of_day, order_id, product_id in zip(
                user_purchases_df["order_dow"].tolist(),
                user_purchases_df["order_hour_of_day"].tolist(),
                user_purchases_df["order_id"].tolist(),
                user_purchases_df["product_id"].tolist(),
            ):
                purchase_struct = {
                    "order_dow": int(order_dow),
                    "order_hour_of_day": int(order_hour_of_day),
                    "order_id": int(order_id),
                    "product_id": int(product_id),
                }'''))}, notes="Column lists give the same values int() sees through iterrows (NaN still raises ValueError).")
sub("preprocess-users-usecols", PP+"::process_users", {PP+"::process_users": edit(PP, "process_users",
 ('''    df_order = pd.read_csv("dataset/orders.csv")''', '''    df_order = pd.read_csv(
        "dataset/orders.csv",
        usecols=["order_id", "user_id", "order_dow", "order_hour_of_day"],
    )'''))}, notes="Only these four columns are used; pandas infers each column's dtype independently.")
sub("preprocess-orders-no-iterrows", PP+"::process_orders", {PP+"::process_orders": edit(PP, "process_orders",
 ('''            for i, (_, order) in enumerate(df_orders_vespa.iterrows()):
                doc = {
                    "put": f"id:orders:order::{order['order_id']}",
                    "fields": {
                        "order_id": int(order["order_id"]),
                        "user_id": int(order["user_id"]),
                        "order_dow": int(order["order_dow"]),
                        "order_hour_of_day": int(order["order_hour_of_day"]),
                        "days_since_prior_order": (
                            float(order["days_since_prior_order"])
                            if pd.notna(order["days_since_prior_order"])
                            else None
                        ),
                        "product_ids": order["product_ids"],
                    },
                }''', '''            columns = [
                df_orders_vespa[column].tolist()
                for column in [
                    "order_id",
                    "user_id",
                    "order_dow",
                    "order_hour_of_day",
                    "days_since_prior_order",
                    "product_ids",
                ]
            ]
            for i, (
                order_id,
                user_id,
                order_dow,
                order_hour_of_day,
                days_since_prior_order,
                product_ids,
            ) in enumerate(zip(*columns)):
                doc = {
                    "put": f"id:orders:order::{order_id}",
                    "fields": {
                        "order_id": int(order_id),
                        "user_id": int(user_id),
                        "order_dow": int(order_dow),
                        "order_hour_of_day": int(order_hour_of_day),
                        "days_since_prior_order": (
                            float(days_since_prior_order)
                            if pd.notna(days_since_prior_order)
                            else None
                        ),
                        "product_ids": product_ids,
                    },
                }'''))}, notes="iterrows on this mixed-dtype frame yields object rows holding Python scalars; tolist yields the same scalars.")
sub("preprocess-orders-no-copy", PP+"::process_orders", {PP+"::process_orders": edit(PP, "process_orders",
 ('''df_order[df_order["eval_set"] == eval_set].copy()''', '''df_order[df_order["eval_set"] == eval_set]'''))}, notes="The filtered frame is only merged, never mutated.")
CS = "use-case-shopping/create_suggestions.py"
sub("suggestions-filter-one-regex", CS+"::filter", {CS+"::filter": edit(CS, "filter",
 ('''def filter(text):
''', '''def filter(text):
    global _FILTERS_PATTERN
'''),
 ('''    for f in filters:
        if f in text:
            return True
    return False''', '''    try:
        pattern = _FILTERS_PATTERN
    except NameError:
        pattern = _FILTERS_PATTERN = re.compile("|".join(map(re.escape, filters)))
    return pattern.search(text) is not None'''))}, notes="One compiled alternation of the escaped filter tokens, kept in a module-level value only this function reads.")
sub("suggestions-filter-content-startswith-tuple", CS+"::filter_content", {CS+"::filter_content": '''def filter_content(text):
    return text.startswith(tuple(invalid_starts))
'''})
AW = "incremental-search/search-suggestions/accepted_words.py"
sub("accepted-words-set-update", AW+"::process_docs", {AW+"::process_docs": edit(AW, "process_docs",
 ('''            for term in clean_text(doc['fields']['title']):
                term_set.add(term)
            for term in clean_text(doc['fields']['content']):
                term_set.add(term)''', '''            term_set.update(clean_text(doc['fields']['title']))
            term_set.update(clean_text(doc['fields']['content']))'''))})
LR = "rag-blueprint/eval/train_logistic_regression.py"
sub("logreg-stats-without-describe", LR+"::perform_cross_validation", {LR+"::perform_cross_validation": edit(LR, "perform_cross_validation",
 ('''        stats = X[feature].describe()
        print(
            f"{feature:<35} | {stats['mean']:<10.4f} | {stats['std']:<10.4f} | {stats['min']:<10.4f} | {stats['max']:<10.4f}"
        )''', '''        column = X[feature]
        print(
            f"{feature:<35} | {column.mean():<10.4f} | {column.std():<10.4f} | {column.min():<10.4f} | {column.max():<10.4f}"
        )'''))}, notes="describe() computes these with the same Series methods plus count and three quantiles that were not printed.")
sub("logreg-predict-from-proba", LR+"::perform_cross_validation", {LR+"::perform_cross_validation": edit(LR, "perform_cross_validation",
 ('''        y_pred = model.predict(X_test_scaled)
        y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]''', '''        y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
        y_pred = model.classes_[(y_pred_proba > 0.5).astype(int)]'''))}, notes="Binary LogisticRegression.predict is classes_[decision > 0]; proba > 0.5 is the same test on the same decision values.")
CF = "news/src/python/convert_to_vespa_format.py"
sub("news-convert-file-dumps", CF+"::convert_file", {CF+"::convert_file": edit(CF, "convert_file",
 ('''            json.dump(doc, output)''', '''            output.write(json.dumps(doc))'''))}, notes="json.dump with default arguments uses the pure-Python iterencode; json.dumps uses the C encoder and gives the same string.")
SW = "visual-retrieval-colpali/src/backend/stopwords.py"
sub("stopwords-tokenizer-only", SW+"::filter", {SW+"::filter": edit(SW, "filter",
 ('''    doc = nlp(text)''', '''    doc = nlp.tokenizer(text)'''))}, notes="The pipeline is spacy.blank('en') with no components, so nlp(text) is the tokenizer plus wrapper overhead.")
EM = "rag-blueprint/eval/evaluate_match_phase.py"
sub("match-semantic-yql-once", EM+"::match_semantic_query_fn", {EM+"::match_semantic_query_fn": '''def match_semantic_query_fn(query_text: str, top_k: int) -> dict:
    global _MATCH_SEMANTIC_YQL
    try:
        yql = _MATCH_SEMANTIC_YQL
    except NameError:
        yql = _MATCH_SEMANTIC_YQL = str(
            qb.select("*")
            .from_(SCHEMA_NAME)
            .where(
                qb.nearestNeighbor(
                    field="title_embedding",
                    query_vector="embedding",
                    annotations={"targetHits": 100},
                )
                | qb.nearestNeighbor(
                    field="chunk_embeddings",
                    query_vector="embedding",
                    annotations={"targetHits": 100},
                )
            )
        )
    return {
        "yql": yql,
        "query": query_text,
        "ranking": "match-only",
        "input.query(embedding)": f"embed({query_text})",
        "presentation.summary": "no-chunks",
    }
'''}, notes="The YQL does not depend on the arguments; it is built once and kept in a module-level value only this function reads.")
VR = "examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/vespa_module/vespa_retriever.py"
sub("create-conditions-operators-once", VR+"::create_conditions", {VR+"::create_conditions": edit(VR, "create_conditions",
 ('''    # Define supported operators
    operators = {''', '''    # Define supported operators
    global _CONDITION_OPERATORS
    try:
        operators = _CONDITION_OPERATORS
    except NameError:
        operators = _CONDITION_OPERATORS = {'''),
 ('''        ">": lambda f, v: f > v,
        "<": lambda f, v: f < v,
        "=": lambda f, v: f == v,
        "!=": lambda f, v: f != v,
        ">=": lambda f, v: f >= v,
        "<=": lambda f, v: f <= v,
        "contains": lambda f, v: f.contains(v),  # Special case for text search
    }''', '''            ">": lambda f, v: f > v,
            "<": lambda f, v: f < v,
            "=": lambda f, v: f == v,
            "!=": lambda f, v: f != v,
            ">=": lambda f, v: f >= v,
            "<=": lambda f, v: f <= v,
            "contains": lambda f, v: f.contains(v),  # Special case for text search
        }'''))}, notes="The operator table is built once and kept in a module-level value only this function reads.")

with open("/home/javad/energy-run/sample-apps/submissions.jsonl", "w") as f:
    for s in S: f.write(json.dumps(s, ensure_ascii=False) + "\n")
print(len(S))
