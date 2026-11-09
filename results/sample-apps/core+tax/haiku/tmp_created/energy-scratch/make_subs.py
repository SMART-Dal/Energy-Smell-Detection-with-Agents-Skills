import ast, json, re
REPO = "/home/javad/energy-run/sample-apps"
def func_source(path, qual):
    src = open(f"{REPO}/{path}", encoding="utf-8").read()
    lines = src.splitlines(keepends=True)
    tree = ast.parse(src)
    found = []
    def walk(node, prefix):
        for ch in ast.iter_child_nodes(node):
            if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = prefix + ch.name
                if name == qual: found.append(ch)
                walk(ch, name + ".")
            elif isinstance(ch, ast.ClassDef):
                walk(ch, prefix + ch.name + ".")
            else:
                walk(ch, prefix)
    walk(tree, "")
    assert len(found) == 1, (path, qual, len(found))
    f = found[0]
    start = min([f.lineno] + [d.lineno for d in f.decorator_list]) - 1
    seg = "".join(lines[start:f.end_lineno])
    # column-zero form: dedent methods to column zero
    first_indent = len(seg) - len(seg.lstrip(" "))
    if first_indent:
        seg = "\n".join(l[first_indent:] if l.startswith(" " * first_indent) else l for l in seg.split("\n"))
    return seg.rstrip("\n") + "\n"

def apply(path, qual, pairs):
    seg = func_source(path, qual)
    for old, new, count in pairs:
        n = seg.count(old)
        assert n == count, (path, qual, old[:60], n)
        seg = seg.replace(old, new)
    return seg

S = []
def sub(id_, rc, unit, changed_pairs, notes, path_qual_list=None):
    changed = {}
    for (p, q, pairs) in changed_pairs:
        changed[f"{p}::{q}"] = apply(p, q, pairs)
    S.append({"id": id_, "root_cause": rc, "unit": unit, "changed": changed,
              "sole_caller_evidence": None, "notes": notes})

P_SPLIT = "feed-split.py"
sub("C10S4-split-text", "C10.S4", "feed-split.py::split_text", [
 (P_SPLIT, "split_text", [
  ('\n    text = ""\n', '\n    parts = []\n', 1),
  ('            if text:\n                data.append((id, header, text))\n                text = ""\n',
   '            if parts:\n                data.append((id, header, "".join(parts)))\n                parts = []\n', 1),
  ('            text = text + "\\n" + line\n', '            parts.append("\\n" + line)\n', 1),
  ('    data.append((id, header, text)) #Flush any last data\n',
   '    data.append((id, header, "".join(parts))) #Flush any last data\n', 1),
 ])],
 "C10.S4. Section text is collected in a list and joined once per flush; the empty test becomes a test on the list, which is non-empty exactly when text would be.")

sub("C10S1-control-translate", "C10.S1", "colbert-long/scripts/convert.py::remove_control_characters", [
 ("colbert-long/scripts/convert.py", "remove_control_characters", [
  ('    return "".join(ch for ch in s if unicodedata.category(ch)[0]!="C")\n',
   '    import sys\n'
   '    table = getattr(remove_control_characters, "table", None)\n'
   '    if table is None:\n'
   '        table = {cp: None for cp in range(sys.maxunicode + 1) if unicodedata.category(chr(cp))[0] == "C"}\n'
   '        remove_control_characters.table = table\n'
   '    return s.translate(table)\n', 1)])],
 "C10.S1. The per-character unicodedata call is replaced by one str.translate against a table of every C-category code point, built on the first call and kept as an attribute of the function. Only caller: colbert-long/scripts/convert.py line 25.")

PC = "incremental-search/search-suggestions/count_terms.py"
sub("C3S4-process-docs-docs", "C3.S4", "incremental-search/search-suggestions/count_terms.py::process_docs", [
 (PC, "process_docs", [
  ('    terms = {}\n\n    # Sum counts\n', '    terms = {}\n\n    # Sum counts\n', 1),
  ('            if term in terms:\n                terms[term]["count"] = terms[term]["count"] + count\n            else:\n                terms[term] = {"term": term, "count": count}\n',
   '            if term in terms:\n                terms[term]["count"] = terms[term]["count"] + count\n                terms[term]["docs"] = terms[term]["docs"] + 1\n            else:\n                terms[term] = {"term": term, "count": count, "docs": 1}\n', 1),
  ('    # Find number of documents containing the term\n    for term in terms.keys():\n        terms[term]["docs"] = sum(\n            [1 if term in doc else 0 for doc in doc_counts]\n        )\n\n', '', 1),
 ])],
 "C3.S4. The document count is taken in the summing pass: a term is in a document exactly when it is a key of that document's counts, and each document reaches a term once, so each term's first occurrence starts docs at 1 and each later document adds 1. Dict key order (term, count, docs) is unchanged.")

sub("C10S1-count-isdisjoint", "C10.S1", "incremental-search/search-suggestions/count_terms.py::count_terms", [
 (PC, "count_terms", [
  ('            if not any(\n                map(lambda word: word in common_words, doc[i : i + win_len])\n            ):\n',
   '            if common_words.isdisjoint(doc[i : i + win_len]):\n', 1)])],
 "C10.S1. `not any(map(lambda ...))` becomes one C-level set.isdisjoint over the window; same answer for a set of common words, which is what callers pass (set() default, read_common_words).")

sub("C10S2-write-replace", "C10.S2", "incremental-search/search-suggestions/count_terms.py::write_json_file", [
 (PC, "write_json_file", [
  ('f\'id:term:term::{re.sub(r" ", "/", term)}\'', 'f\'id:term:term::{term.replace(" ", "/")}\'', 1)])],
 "C10.S2. The one-character literal replacement goes through str.replace instead of the regex engine; the output string is identical.")

sub("C9S1-write-once", "C9.S1", "incremental-search/search-suggestions/count_terms.py::write_json_file", [
 (PC, "write_json_file", [
  ('        json.dump(feed_list, f, indent=2)\n', '        f.write(json.dumps(feed_list, indent=2))\n', 1)])],
 "C9.S1. json.dump hands the encoder's chunks to f.write one by one; json.dumps builds the same text and it is written once. Same bytes (same indent, same default separators).")

sub("C10S3-accepted-update", "C10.S3", "incremental-search/search-suggestions/accepted_words.py::process_docs", [
 ("incremental-search/search-suggestions/accepted_words.py", "process_docs", [
  ("            for term in clean_text(doc['fields']['title']):\n                term_set.add(term)\n            for term in clean_text(doc['fields']['content']):\n                term_set.add(term)\n",
   "            term_set.update(clean_text(doc['fields']['title']))\n            term_set.update(clean_text(doc['fields']['content']))\n", 1)])],
 "C10.S3. Two per-term add loops become two set.update calls over the same token lists; the resulting set is identical.")

sub("C6S2-sample-index", "C6.S2", "text-video-search/src/python/embedding.py::sample_images", [
 ("text-video-search/src/python/embedding.py", "sample_images", [
  ("        return np.array(images)[idx]\n",
   "        if len(idx) == 0:\n            return np.array(images)[idx]\n        return np.array([images[i] for i in idx])\n", 1)])],
 "C6.S2. Only the sampled frames are copied: the list is indexed before the array is built. The empty-sample case keeps the original expression so the empty shape is unchanged. Only caller: extract_images, which passes a list.")

sub("C5S2-predictions-index", "C5.S2", "news/src/python/evaluate.py::predictions", [
 ("news/src/python/evaluate.py", "predictions", [
  ("    preds = []\n    for news_id in news_ids:\n        hit = find_hit(hits, news_id)\n",
   "    preds = []\n    children = {}\n    for child in hits[\"root\"][\"children\"]:\n        children.setdefault(child[\"fields\"][\"news_id\"], child)\n    for news_id in news_ids:\n        hit = children.get(news_id)\n", 1)])],
 "C5.S2. One index of the children by news_id, built once per call, keeps the first child per id (as find_hit does); a missing id still ends in hit['relevance'] on None, so the exception type is unchanged. Differs only on malformed hits, where a child without fields.news_id now fails while building the index.")

sub("C9S1-embedding-join", "C9.S1", "news/src/python/create_bert_embeddings.py::write_embedding", [
 ("news/src/python/create_bert_embeddings.py", "write_embedding", [
  ('    f.write("\\t")\n    for j, num in enumerate(embedding):\n        if j > 0:\n            f.write(",")\n        f.write("%.4f" % num)\n',
   '    f.write("\\t" + ",".join("%.4f" % num for num in embedding))\n', 1)])],
 "C9.S1. One write per embedding instead of one per float and per separator; the text written is the same.")

sub("C10S1-binary-vectorise", "C10.S1", "visual-retrieval-colpali/prepare_feed_deploy.py::float_to_binary_embedding", [
 ("visual-retrieval-colpali/prepare_feed_deploy.py", "float_to_binary_embedding", [
  ('    binary_query_embeddings = {}\n    for k, v in float_query_embedding.items():\n        binary_vector = (\n            np.packbits(np.where(np.array(v) > 0, 1, 0)).astype(np.int8).tolist()\n        )\n        binary_query_embeddings[k] = binary_vector\n    return binary_query_embeddings\n',
   '    if not float_query_embedding:\n        return {}\n    binary_vectors = (\n        np.packbits(np.array(list(float_query_embedding.values())) > 0, axis=-1).astype(np.int8).tolist()\n    )\n    return dict(zip(float_query_embedding.keys(), binary_vectors))\n', 1)])],
 "C10.S1. The per-vector np.array/np.where/packbits calls become one packbits over the stacked matrix; each row packs to the same bytes. Requires every vector in the dict to have the same length, which holds for ColPali embeddings (one hidden size per dict).")

PS = "text-search/python/sample-queries-and-documents.py"
sub("C10S3-select-update", "C10.S3", "text-search/python/sample-queries-and-documents.py::select_documents", [
 (PS, "select_documents", [
  ("        for docid in queries[qid][\"docs\"]:\n            selected_doc_ids.add(docid)\n",
   "        selected_doc_ids.update(queries[qid][\"docs\"])\n", 1)])],
 "C10.S3. One set.update per query instead of one add per document id; same set.")

sub("C10S3-filter-tuple", "C10.S3", "use-case-shopping/create_suggestions.py::filter_content", [
 ("use-case-shopping/create_suggestions.py", "filter_content", [
  ("\tfor f in invalid_starts:\n\t\tif text.startswith(f):\n\t\t\treturn True\n\treturn False\n",
   "\treturn text.startswith(tuple(invalid_starts))\n", 1)])],
 "C10.S3. One startswith call with a tuple of the prefixes in place of one call per prefix; same boolean.")

sub("C1S5-describe-stats", "C1.S5", "rag-blueprint/eval/train_logistic_regression.py::perform_cross_validation", [
 ("rag-blueprint/eval/train_logistic_regression.py", "perform_cross_validation", [
  ("        stats = X[feature].describe()\n        print(\n            f\"{feature:<35} | {stats['mean']:<10.4f} | {stats['std']:<10.4f} | {stats['min']:<10.4f} | {stats['max']:<10.4f}\"\n        )\n",
   "        column = X[feature]\n        print(\n            f\"{feature:<35} | {column.mean():<10.4f} | {column.std():<10.4f} | {column.min():<10.4f} | {column.max():<10.4f}\"\n        )\n", 1)])],
 "C1.S5. Only mean, std, min and max are printed, so the four are read straight off the column; describe() also computes count and quartiles, which need a sort per feature. pandas' describe uses the same mean and sample std.")

sub("C1S4-what-language", "C1.S4", "feed-split.py::what_language", [
 ("feed-split.py", "what_language", [
  ("    z = re.match(r\"{%\\s*highlight\\s*(\\w+)\\s%}\", el.text)\n", "    text = el.text\n    z = re.match(r\"{%\\s*highlight\\s*(\\w+)\\s%}\", text)\n", 1),
  ("    if el.text.find(\"curl\") > 0:\n", "    if text.find(\"curl\") > 0:\n", 1),
  ("    if el.text.find(\"import com.yahoo\") > 0:\n", "    if text.find(\"import com.yahoo\") > 0:\n", 1)])],
 "C1.S4. el.text is read once into a local; the three checks use the same string. el.text is a pure get_text() of the element.")

sub("C8S2-filter-compiled", "C8.S2", "visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.should_filter_token", [
 ("visual-retrieval-colpali/src/backend/colpali.py", "SimMapGenerator.should_filter_token", [
  ("def should_filter_token(token: str) -> bool:\n", "def should_filter_token(\n    token: str,\n    pattern=re.compile(r\"^<.*$|^\\s+$|^(?!.*\\d)(?!▁)[^\\w\\s]+$|^_.*$|^Question$|^▁$\"),\n) -> bool:\n", 1),
  ("    pattern = re.compile(\n        r\"^<.*$|^\\s+$|^(?!.*\\d)(?!▁)[^\\w\\s]+$|^_.*$|^Question$|^▁$\"\n    )\n", "", 1)])],
 "C8.S2. The pattern is compiled once, as a default argument evaluated when the function is defined, so the signature gains an optional parameter that no caller passes. The regex text is unchanged.")

sub("C9S1-extract-offset", "C9.S1", "text-search/python/extract-msmarco.py::extract_documents", [
 ("text-search/python/extract-msmarco.py", "extract_documents", [
  ("        for docid in docoffset.keys():\n            offset.write(\"{0}\\t{1}\\n\".format(docid, out.tell()))\n            out.write(getcontent(docid, f, docoffset))\n",
   "        position = 0\n        for docid in docoffset.keys():\n            offset.write(\"{0}\\t{1}\\n\".format(docid, position))\n            content = getcontent(docid, f, docoffset)\n            out.write(content)\n            position += len(content.encode(\"utf8\"))\n", 1)])],
 "C9.S1. out.tell() flushes the text buffer on every document; the byte offset is kept from the lengths written instead. utf8 with no newline translation on Linux, so the offsets equal what tell() reported.")

sub("C6S3-init-iterate", "C6.S3", "examples/embedder-auto-training-evaluation/training-evaluation/train.py::TrainDataset.__init__", [
 ("examples/embedder-auto-training-evaluation/training-evaluation/train.py", "TrainDataset.__init__", [
  ("        for line in file.readlines():\n", "        for line in file:\n", 2)])],
 "C6.S3. Both files are iterated line by line instead of readlines(); the same lines are parsed, and the list of raw lines is never built.")

with open(f"{REPO}/submissions.jsonl", "w") as f:
    for s in S:
        f.write(json.dumps(s, ensure_ascii=False) + "\n")
print("submissions:", len(S))
