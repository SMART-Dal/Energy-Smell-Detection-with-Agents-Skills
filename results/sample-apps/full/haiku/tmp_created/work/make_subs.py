import ast, json, textwrap
ROOT = "/home/javad/energy-run/sample-apps/"
cache = {}
def source_of(path, qual):
    if path not in cache:
        text = open(ROOT + path, encoding="utf-8").read()
        cache[path] = (text.splitlines(keepends=True), ast.parse(text))
    lines, tree = cache[path]
    names = qual.split(".")
    def find(node, names):
        for c in ast.iter_child_nodes(node):
            if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef)) and c.name == names[0]:
                if len(names) == 1:
                    return c
                r = find(c, names[1:])
                if r: return r
            elif isinstance(c, ast.ClassDef) and c.name == names[0] and len(names) > 1:
                r = find(c, names[1:])
                if r: return r
            else:
                r = find(c, names)
                if r: return r
        return None
    node = find(tree, names)
    assert node is not None, (path, qual)
    start = (node.decorator_list[0].lineno if node.decorator_list else node.lineno)
    return "".join(lines[start-1:node.end_lineno])

def build(path, qual, edits):
    src = source_of(path, qual)
    for old, new in edits:
        n = src.count(old)
        assert n == 1, (qual, n, old[:80])
        src = src.replace(old, new)
    indent = len(src) - len(src.lstrip(" "))
    if indent:
        src = textwrap.dedent(src)
    return src

S = []
def sub(id_, rc, path, qual, edits, notes, sole=None):
    unit = f"{path}::{qual}"
    S.append({"id": id_, "root_cause": rc, "unit": unit,
              "changed": {unit: build(path, qual, edits)},
              "sole_caller_evidence": sole, "notes": notes})

P = "incremental-search/search-suggestions/count_terms.py"
sub("C3S4-process-docs-docs-in-loop", "C3.S4", P, "process_docs", [(
"""    # Sum counts
    for counts in doc_counts:
        total_count = sum([count for count in counts.values()])
        for (term, count) in counts.items():
            if term in terms:
                terms[term]["count"] = terms[term]["count"] + count
            else:
                terms[term] = {"term": term, "count": count}

    # Find number of documents containing the term
    for term in terms.keys():
        terms[term]["docs"] = sum(
            [1 if term in doc else 0 for doc in doc_counts]
        )
""",
"""    # Sum counts
    for counts in doc_counts:
        total_count = sum([count for count in counts.values()])
        for (term, count) in counts.items():
            if term in terms:
                terms[term]["count"] = terms[term]["count"] + count
                terms[term]["docs"] = terms[term]["docs"] + 1
            else:
                terms[term] = {"term": term, "count": count, "docs": 1}
""")],
"Counts documents in the same pass that sums counts; the per-term scan over all documents is removed. Output dict has the same keys in the same order.")

sub("C1S1-process-docs-dead-total", "C1.S1", P, "process_docs", [(
"""        total_count = sum([count for count in counts.values()])
""", "")],
"Deletes the unread total_count sum. Different edit from C3S4-process-docs-docs-in-loop, measured on the original.")

sub("C10S1-count-terms-isdisjoint", "C10.S1", P, "count_terms", [(
"""            if not any(
                map(lambda word: word in common_words, doc[i : i + win_len])
            ):
""",
"""            if common_words.isdisjoint(doc[i : i + win_len]):
""")],
"isdisjoint answers 'no word of the window is in common_words' in one C call; the lambda and map per window are removed. common_words is a set at every call site.")

sub("C1S4-count-terms-window-once", "C1.S4", P, "count_terms", [(
"""            if not any(
                map(lambda word: word in common_words, doc[i : i + win_len])
            ):
                term = " ".join(doc[i : i + win_len])
""",
"""            window = doc[i : i + win_len]
            if not any(map(lambda word: word in common_words, window)):
                term = " ".join(window)
""")],
"Binds the window slice once. Different edit from C10S1-count-terms-isdisjoint, measured on the original.")

sub("C10S2-write-json-replace", "C10.S2", P, "write_json_file", [(
"""            "update": f'id:term:term::{re.sub(r" ", "/", term)}',
""",
"""            "update": f'id:term:term::{term.replace(" ", "/")}',
""")],
"term.replace gives the same string as re.sub on a single literal space.")

A = "incremental-search/search-suggestions/accepted_words.py"
sub("C10S3-accepted-process-update", "C10.S3", A, "process_docs", [(
"""            for term in clean_text(doc['fields']['title']):
                term_set.add(term)
            for term in clean_text(doc['fields']['content']):
                term_set.add(term)
""",
"""            term_set.update(clean_text(doc['fields']['title']))
            term_set.update(clean_text(doc['fields']['content']))
""")],
"set.update over a list adds the same elements in the same order as the add loops.")

sub("C10S3-accepted-write-join", "C10.S3", A, "write_to_file", [(
"""        for term in term_set:
            f.write(term+"\\n")
""",
"""        f.write("".join(term + "\\n" for term in term_set))
""")],
"One write of the joined text instead of one write call per term; the bytes written are the same.")

sub("C5S3-bert-float32-buffer", "C5.S3", "news/src/python/train_cold_start.py", "read_bert_embeddings", [(
"""    embeddings = np.zeros([len(data_loader.news()), 512])
""",
"""    embeddings = np.zeros([len(data_loader.news()), 512], dtype=np.float32)
""")],
"Float32 buffer: each stored double is rounded once to float32, which is the rounding torch.FloatTensor applied to the float64 buffer, so the tensor is identical.")

sub("C1S5-read-data-no-timestamp", "C1.S5", "news/src/python/mind_data.py", "MindData.read_data", [(
"""                time = datetime.datetime.strptime(impression_data[2], "%m/%d/%Y %I:%M:%S %p")
""", ""),
("""                    "timestamp": time,
""", "")],
"Removes the strptime and the 'timestamp' key. Expected to change the entries of impression_list, which the contract counts as an argument effect; measurement decides.",
sole="grep for 'timestamp' under news/src/python: the only occurrences in mind_data.py are the removed lines; the other hits are field_list names in evaluate.py, convert_to_vespa_format.py, create_category_ctrs.py, which parse their own files. MindData.train_impressions and valid_impressions are read by sample_training_data and sample_valid_data for user, news, category, subcategory, entity and label only.")

sub("C6S2-sample-images-copy-kept", "C6.S2", "text-video-search/src/python/embedding.py", "sample_images", [(
"""        return np.array(images)[idx]
""",
"""        return np.array([images[i] for i in idx])
""")],
"Copies only the sampled frames; the else branch still builds the full array.")

sub("C10S1-remove-control-fast-path", "C10.S1", "colbert-long/scripts/convert.py", "remove_control_characters", [(
"""def remove_control_characters(s):
    return "".join(ch for ch in s if unicodedata.category(ch)[0]!="C")
""",
"""def remove_control_characters(s):
    if s.isprintable():
        return s
    return "".join(ch for ch in s if unicodedata.category(ch)[0]!="C")
""")],
"A printable string has no category-C character (every C category is non-printable), so it is returned as is. Strings with newlines or other control characters take the original path.")

sub("C10S4-split-text-parts-list", "C10.S4", "feed-split.py", "split_text", [(
"""    data = []
    for line in lines:
        if line.startswith("#"):
            if text:
                data.append((id, header, text))
                text = ""
            header = line.lstrip("#")
            id = "-".join(header.split()).lower()
        else:
            text = text + "\\n" + line

    data.append((id, header, text)) #Flush any last data
""",
"""    data = []
    parts = []
    for line in lines:
        if line.startswith("#"):
            if parts:
                data.append((id, header, "".join(parts)))
                parts = []
            header = line.lstrip("#")
            id = "-".join(header.split()).lower()
        else:
            parts.append("\\n" + line)

    data.append((id, header, "".join(parts))) #Flush any last data
""")],
"parts is non-empty exactly when text was non-empty, since every appended piece starts with a newline.")

sub("C9S1-extract-docs-running-offset", "C9.S1", "text-search/python/extract-msmarco.py", "extract_documents", [(
"""        for docid in docoffset.keys():
            offset.write("{0}\\t{1}\\n".format(docid, out.tell()))
            out.write(getcontent(docid, f, docoffset))
""",
"""        position = 0
        for docid in docoffset.keys():
            offset.write("{0}\\t{1}\\n".format(docid, position))
            content = getcontent(docid, f, docoffset)
            out.write(content)
            position += len(content.encode("utf8"))
""")],
"Tracks the UTF-8 byte position instead of calling out.tell(), which flushes the text buffer on every call. The file is opened with encoding utf8 and no BOM, so the running count equals tell().")

sub("C10S2-convert-main-one-write", "C10.S2", "text-search/python/convert-to-vespa-format.py", "main", [(
"""            json.dump(doc, out)
""",
"""            out.write(json.dumps(doc))
""")],
"json.dumps with default arguments yields the same text json.dump writes, in one write call.")

sub("C3S2-select-documents-min-hoist", "C3.S2", "text-search/python/sample-queries-and-documents.py", "select_documents", [(
"""    docids = [docid for docid in offsets.keys()]
    while len(selected_doc_ids) < min(len(docids), documents_to_generate):
""",
"""    docids = [docid for docid in offsets.keys()]
    target = min(len(docids), documents_to_generate)
    while len(selected_doc_ids) < target:
""")],
"The target size does not change inside the loop; the random draws are unchanged.")

W = "examples/workshop-ecommerce/preprocess.py"
sub("C3S1-products-records", "C3.S1", W, "process_products", [(
"""        for i, (_, product) in enumerate(df_merged.iterrows()):
""",
"""        for i, product in enumerate(df_merged.to_dict("records")):
""")],
"to_dict('records') gives the same field values per row without a Series per row. Measured in full mode; sample mode breaks after ten rows.")

sub("C3S1-users-purchases-records", "C3.S1", W, "process_users", [(
"""            for _, purchase in user_purchases_df.iterrows():
""",
"""            for purchase in user_purchases_df.to_dict("records"):
""")],
"Iterates purchase records as dicts; every field is read by the same key and converted with int().")

sub("C3S1-orders-records-new", "C3.S1", W, "process_orders", [(
"""            for i, (_, order) in enumerate(df_orders_vespa.iterrows()):
""",
"""            for i, order in enumerate(df_orders_vespa.to_dict("records")):
""")],
"Iterates order records as dicts instead of a Series per row. Added in step 2 as suspicion b.")

P2 = "visual-retrieval-colpali/prepare_feed_deploy.py"
sub("C10S3-prepare-binary-packbits-bool", "C10.S3", P2, "float_to_binary_embedding", [(
"""        binary_vector = (
            np.packbits(np.where(np.array(v) > 0, 1, 0)).astype(np.int8).tolist()
        )
""",
"""        binary_vector = np.packbits(np.array(v) > 0).astype(np.int8).tolist()
""")],
"packbits takes the boolean array directly; the int64 intermediate from np.where is removed.")

V = "visual-retrieval-colpali/src/backend/vespa_app.py"
sub("C10S3-vespa-binary-packbits-bool", "C10.S3", V, "VespaQueryClient.float_to_binary_embedding", [(
"""            binary_vector = (
                np.packbits(np.where(np.array(vector) > 0, 1, 0))
                .astype(np.int8)
                .tolist()
            )
""",
"""            binary_vector = (
                np.packbits(np.array(vector) > 0)
                .astype(np.int8)
                .tolist()
            )
""")],
"Same edit as prepare_feed_deploy float_to_binary_embedding, in the method. Changed source is dedented to column zero.")

with open(ROOT + "submissions.jsonl", "w") as f:
    for s in S:
        f.write(json.dumps(s, ensure_ascii=False) + "\n")
print(len(S), "submissions")
for s in S[:3]:
    print(s["changed"][s["unit"]][:400]); print("----")
