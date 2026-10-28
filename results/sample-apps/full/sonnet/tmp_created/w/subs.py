import json
S=[]
def sub(id_,rc,unit,src,notes,evidence=None,extra=None):
    ch={unit:src}
    if extra: ch.update(extra)
    S.append({"id":id_,"root_cause":rc,"unit":unit,"changed":ch,"sole_caller_evidence":evidence,"notes":notes})
CT="incremental-search/search-suggestions/count_terms.py::"

sub("C3S4-process-docs-docfreq","C3.S4",CT+"process_docs",'''def process_docs(obj, term_length=1, common_words=set()):
    doc_counts = [
        process_doc(doc["fields"], term_length, common_words) for doc in obj
    ]
    terms = {}

    # Sum counts
    for counts in doc_counts:
        total_count = sum([count for count in counts.values()])
        for (term, count) in counts.items():
            if term in terms:
                terms[term]["count"] = terms[term]["count"] + count
                terms[term]["docs"] += 1
            else:
                terms[term] = {"term": term, "count": count, "docs": 1}

    return terms''',"C3.S4. The second loop tested `term in doc` for every doc and every term; each counts dict has unique keys, so the document frequency is the number of dicts a term appears in, counted in the first loop. Inner key order term,count,docs is unchanged. `total_count` line left in place (separate repair).")
sub("C1S1-process-docs-dead-total","C1.S1",CT+"process_docs",'''def process_docs(obj, term_length=1, common_words=set()):
    doc_counts = [
        process_doc(doc["fields"], term_length, common_words) for doc in obj
    ]
    terms = {}

    # Sum counts
    for counts in doc_counts:
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

    return terms''',"C1.S1. Only the unread `total_count = sum([...])` line is deleted; the quadratic document-frequency loop is left as it was.")
sub("C10S1-count-terms-isdisjoint","C10.S1",CT+"count_terms",'''def count_terms(doc, term_length=1, common_words=set()):
    counts = {}
    for win_len in range(1, term_length + 1):
        for i in range(len(doc) + 1 - win_len):
            if common_words.isdisjoint(doc[i : i + win_len]):
                term = " ".join(doc[i : i + win_len])
                if  len(term) > 0 and not term.isspace():
                    counts[term] = counts.get(term, 0) + 1
    return counts''',"C10.S1 (close to C10.S2). `any(map(lambda ...))` runs a Python lambda per word of each window; `isdisjoint` runs the same membership tests in C. common_words is a set at every call site (default set(), read_common_words returns a set).")
sub("C1S4-count-terms-window","C1.S4",CT+"count_terms",'''def count_terms(doc, term_length=1, common_words=set()):
    counts = {}
    for win_len in range(1, term_length + 1):
        for i in range(len(doc) + 1 - win_len):
            window = doc[i : i + win_len]
            if not any(
                map(lambda word: word in common_words, window)
            ):
                term = " ".join(window)
                if  len(term) > 0 and not term.isspace():
                    counts[term] = counts.get(term, 0) + 1
    return counts''',"C1.S4. The window slice is computed once per iteration instead of twice; nothing else changed.")
sub("C6S1-process-doc-chain","C6.S1",CT+"process_doc",'''def process_doc(doc_fields, term_length=1, common_words=set()):
    import itertools
    if doc_fields["title"] and doc_fields["content"]:
        title_counts = count_terms(
            clean_text(doc_fields["title"]), term_length, common_words
        )
        content_counts = count_terms(
            clean_text(doc_fields["content"]), term_length, common_words
        )
        return {
            term: title_counts.get(term, 0) + content_counts.get(term, 0)
            for term in itertools.chain(title_counts, content_counts)
        }
    else:
        return {}''',"C6.S1. `list(a.keys()) + list(b.keys())` builds three throwaway lists; chain yields the same term sequence, so the result dict has the same order and values.")
sub("C10S2-write-json-term-replace","C10.S2",CT+"write_json_file",'''def write_json_file(terms, file_path):
    feed_list = [
        {
            "update": f'id:term:term::{term.replace(" ", "/")}',
            "create": True,
            "fields": {
                "term": {"assign": data["term"]},
                "terms": {"assign": get_phrases(data["term"])},
                "corpus_count": {"assign": data["count"]},
                "document_count": {"assign": data["docs"]},
            },
        }
        for (term, data) in terms.items()
    ]
    with open(file_path, "w") as f:
        json.dump(feed_list, f, indent=2)''',"C10.S2. `re.sub(r\" \", \"/\", term)` replaced by `term.replace(\" \", \"/\")`, same string.")
sub("C6S3-read-common-words-stream","C6.S3",CT+"read_common_words",'''def read_common_words(file_path):
    common_words = set()
    with open(file_path, "r") as f:
        for line in f:
            common_words.add(line.strip())
    return common_words''',"C6.S3. The file is iterated directly instead of materialising readlines().")
AW="incremental-search/search-suggestions/accepted_words.py::"
sub("C10S1-accepted-process-docs-update","C10.S1",AW+"process_docs",'''def process_docs(obj):
    term_set = set()
    for doc in obj:
        if doc['fields']['title'] and doc['fields']['content']:
            term_set.update(clean_text(doc['fields']['title']))
            term_set.update(clean_text(doc['fields']['content']))
    return term_set''',"C10.S1. Two per-term add loops replaced by set.update on the same token lists.")
MD="news/src/python/mind_data.py::MindData."
sub("C4S2-sample-valid-filter-first","C4.S2",MD+"sample_valid_data",'''def sample_valid_data(self, prob=1.0, train=False):
    data = []
    impressions = self.train_impressions if train else self.valid_impressions
    for impression in impressions:
        if random.random() <= prob:
            news_indices = impression["news_indices"]
            labels = impression["labels"]
            if sum(labels) > 0 and sum(labels) != len(labels):
                category_indices = [ self.news_content[index]["category_index"] for index in news_indices ]
                subcategory_indices = [ self.news_content[index]["subcategory_index"] for index in news_indices ]
                entity_indices = [ self.news_content[index]["entity_index"] for index in news_indices ]
                user_index = [ impression["user_index"] ] * len(labels)
                data.append([
                    torch.LongTensor(user_index),
                    torch.LongTensor(news_indices),
                    torch.LongTensor(category_indices),
                    torch.LongTensor(subcategory_indices),
                    torch.LongTensor(entity_indices),
                    torch.FloatTensor(labels)
                ])
    return data''',"C4.S2 (the card's case where a test stands in front of work). The label test only reads labels, so it runs before the three index comprehensions and the user_index list; random.random() is still called once per impression in the same order. grep: sample_valid_data is called only from train_cold_start.eval_model and train_mf.eval_model.")
sub("C1S4-add-impressions-local","C1.S4",MD+"add_impressions",'''def add_impressions(self, impression, user_indices, news_indices, category_indices, subcategory_indices, entity_indices, labels, num_negatives):
    user_index = impression["user_index"]
    positive, negative = self.find_clicked(impression["news_indices"], impression["labels"])

    # add each positive label
    for pos_news_index in positive:
        pos_content = self.news_content[pos_news_index]
        user_indices.append(user_index)
        news_indices.append(pos_news_index)
        category_indices.append(pos_content["category_index"])
        subcategory_indices.append(pos_content["subcategory_index"])
        entity_indices.append(pos_content["entity_index"])
        labels.append(1)

        # for each positive label, sample negative labels
        for neg_news_index in random.sample(negative, min(num_negatives, len(negative))):
            neg_content = self.news_content[neg_news_index]
            user_indices.append(user_index)
            news_indices.append(neg_news_index)
            category_indices.append(neg_content["category_index"])
            subcategory_indices.append(neg_content["subcategory_index"])
            entity_indices.append(neg_content["entity_index"])
            labels.append(0)''',"C1.S4 (the scan labels this C8.S3 too). The row's news_content entry is read once per row instead of three times.")
NE="news/src/python/evaluate.py::"
sub("C3S4-predictions-dict","C3.S4",NE+"predictions",'''def predictions(hits, news_ids):
    preds = []
    by_id = None
    for news_id in news_ids:
        if by_id is None:
            by_id = {}
            for child in hits["root"]["children"]:
                by_id.setdefault(child["fields"]["news_id"], child)
        hit = by_id.get(news_id)
        relevance = hit["relevance"]
        preds.append(relevance)
    return preds''',"C3.S4. find_hit scanned the child list for every id; the dict is built once per call (first match kept, as find_hit returns the first), lazily so an empty news_ids never touches hits. find_hit itself is not changed.")
FS="feed-split.py::"
sub("C10S4-split-text-parts","C10.S4",FS+"split_text",'''def split_text(soup):
    split_tables(soup)
    split_lists(soup)
    md = markdownify(str(soup), heading_style='ATX', code_language_callback=what_language, strip=['img'])
    lines = md.split("\\n")
    header = ""
    parts = []
    id = ""
    data = []
    for line in lines:
        if line.startswith("#"):
            if parts:
                data.append((id, header, "".join(parts)))
                parts = []
            header = line.lstrip("#")
            id = "-".join(header.split()).lower()
        else:
            parts.append("\\n")
            parts.append(line)

    data.append((id, header, "".join(parts))) #Flush any last data
    return data''',"C10.S4. Text is collected as parts and joined at flush; `if parts` equals `if text` because every appended chunk starts with a newline. The C10.S4 card says the plain-local form may already be linear, so the measurement decides.")
sub("C1S4-what-language-text","C1.S4",FS+"what_language",'''def what_language(el):
    text = el.text
    z = re.match(r"{%\\s*highlight\\s*(\\w+)\\s%}", text)
    if z:
        lang =  z.group(1)
        return lang
    if text.find("curl") > 0:
        return "bash"
    if text.find("import com.yahoo") > 0:
        return "java"
    return ""''',"C1.S4. bs4's `.text` joins every descendant string on each access; read once.")
TS="test/test.py::"
sub("C3S1-parse-page-findall","C3.S1",TS+"parse_page",'''def parse_page(html):
    script = {
        "before": [],
        "steps": [],
        "after": []
    }

    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.find_all(["pre", "div", "p"], attrs={"data-test": True}):
        attr = tag.attrs["data-test"]

        if attr == "before":
            script["before"].extend(parse_cmds(tag.string, tag.attrs))

        if attr == "exec":
            script["steps"].extend(parse_cmds(tag.string, tag.attrs))

        if attr == "file":
            script["steps"].append(parse_file(tag.contents, tag.attrs))

        if attr == "after":
            script["after"].extend(parse_cmds(tag.string, tag.attrs))

        if re.search("^run-macro", attr):
            macro = re.sub("run-macro\\s?", "", attr)
            script["steps"].extend(get_macro(macro))

    return script''',"C3.S1 (a lambda filter that bs4 can do inside find_all). Matches the same tags in document order: name in pre/div/p and has the data-test attribute.")
sub("C4S4-parse-page-elif","C4.S4",TS+"parse_page",'''def parse_page(html):
    script = {
        "before": [],
        "steps": [],
        "after": []
    }

    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.find_all(lambda tag: (tag.name == "pre" or tag.name == "div" or tag.name == "p") and tag.has_attr("data-test")):
        attr = tag.attrs["data-test"]

        if attr == "before":
            script["before"].extend(parse_cmds(tag.string, tag.attrs))

        elif attr == "exec":
            script["steps"].extend(parse_cmds(tag.string, tag.attrs))

        elif attr == "file":
            script["steps"].append(parse_file(tag.contents, tag.attrs))

        elif attr == "after":
            script["after"].extend(parse_cmds(tag.string, tag.attrs))

        elif re.search("^run-macro", attr):
            macro = re.sub("run-macro\\s?", "", attr)
            script["steps"].extend(get_macro(macro))

    return script''',"C4.S4. The five tests on `attr` are exclusive (distinct literals, and a value starting run-macro equals none of them) and no branch rebinds attr.")
sub("C10S4-parse-file-parts","C10.S4",TS+"parse_file",'''def parse_file(pre, attrs):
    if not "data-path" in attrs:
        raise ValueError("File element does not have required 'data-path' attribute.")
    path = attrs["data-path"]
    if path[0] == "/":
        raise ValueError("Absolute file paths are not permitted")
    if ".." in path:
        raise ValueError("'..' not permitted in file paths")
    parts = []
    for line in pre:
        if "ProcessingInstruction" in str(type(line)):  # xml: <? ... ?>
            parts.append("<?" + str(line) + ">")
        else:
            parts.append(str(line))
    content = "".join(parts)
    content = content[1:] if content[0] == "\\n" else content
    return {"type": "file", "content": content, "path": path}''',"C10.S4. Parts joined once; the type test and the leading-newline strip are left as they were (IndexError on empty content is preserved).")
CD="text-search/python/collect_training_data.py::"
sub("C8S3-annotate-data-local","C8.S3",CD+"annotate_data",'''def annotate_data(hits, query_id, relevant_id):
    data = []
    for h in hits:
        fields = h["fields"]
        rankfeatures = fields["rankfeatures"]
        doc_id = fields["id"]
        rankfeatures.update({"docid": doc_id})
        rankfeatures.update({"qid": query_id})
        rankfeatures.update({"relevant": 1 if doc_id == relevant_id else 0})
        data.append(rankfeatures)
    return data''',"C8.S3. h['fields'] and its id are read once per hit.")
US="use-case-shopping/create_suggestions.py::"
sub("C10S1-filter-any","C10.S1",US+"filter",'''def filter(text):
	if len(text) < 3 or len(text) > 64:
		return True
	if text.startswith("/") and len(text) < 3:
		return True
	return any(f in text for f in filters)''',"C10.S1. The explicit substring loop is `any(...)`; both iterate `filters` in order and stop at the first hit. The card says to measure which form fits.")
FV="feed_to_vespa.py::"
sub("C6S3-get-feed-docids-setcomp","C6.S3",FV+"get_feed_docids",'''def get_feed_docids(feed, namespace, doc_type):
    with open(feed, "r", encoding='utf-8') as f:
        feed_json = json.load(f)
    if doc_type == "doc":
        return {"id:{0}:doc::".format(namespace) + find(doc, "fields.namespace") + find(doc, "fields.path") for doc in feed_json}
    elif doc_type == "term":
        return {"id:{0}:term::".format(namespace) + str(find(doc, "fields.hash")) for doc in feed_json}
    elif doc_type == "paragraph":
        return {doc['put'] for doc in feed_json}''',"C6.S3 (the scan also labels it C5.S4). set([listcomp]) becomes a set comprehension.")
sub("C7S3-find-loop","C7.S3",FV+"find",'''def find(json, path, separator = "."):
    while len(path) != 0:
        head, _, path = path.partition(separator)
        if head not in json:
            return None
        json = json[head]
    return json''',"C7.S3. Linear recursion, one frame per path segment, turned into a loop with the same lookups and the same None for a missing key.",
 "find is defined in feed_to_vespa.py and called only from get_indexed_docids and get_feed_docids in the same file (grep -rn 'find(' feed_to_vespa.py); the signature and results are unchanged.")
EMB="text-video-search/src/python/embedding.py::"
sub("C6S2-sample-images-select-first","C6.S2",EMB+"sample_images",'''def sample_images(images, number_to_sample):
    """
    Sample equally spaced frames from a list of image frames

    :param images: a list of image frames.
    :param number_to_sample: int representing the number os frames to sample.

    :return: a numpy array containing the sample of frames.
    """
    if number_to_sample < len(images):
        idx = np.round(np.linspace(0, len(images) - 1, number_to_sample)).astype(int)
        if len(idx) == 0:
            return np.array(images)[idx]
        return np.array([images[i] for i in idx])
    else:
        return np.array(images)''',"C6.S2. Only the sampled frames are stacked into an array, not all of them first; number_to_sample == 0 keeps the original path so the empty-array shape is the same.")
VA="visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient."
sub("C5S4-float-to-binary-no-where","C5.S4",VA+"float_to_binary_embedding",'''def float_to_binary_embedding(self, float_query_embedding: dict) -> dict:
    """
    Convert float query embeddings to binary embeddings.

    Args:
        float_query_embedding (dict): Dictionary of float embeddings.

    Returns:
        dict: Dictionary of binary embeddings.
    """
    binary_query_embeddings = {}
    for key, vector in float_query_embedding.items():
        binary_vector = (
            np.packbits(np.array(vector) > 0)
            .astype(np.int8)
            .tolist()
        )
        binary_query_embeddings[key] = binary_vector
        if len(binary_query_embeddings) >= self.MAX_QUERY_TERMS:
            self.logger.warning(
                f"Warning: Query has more than {self.MAX_QUERY_TERMS} terms. Truncating."
            )
            break
    return binary_query_embeddings''',"Step 2 listed this as C10.S3; the edit actually made is the one C5.S4 describes: `np.where(mask, 1, 0)` converts a boolean array to int before packbits, which accepts the boolean array directly and packs the same bits. Close call between C5.S4 and C10.S2.")
NV="news/src/python/convert_to_vespa_format.py::"
sub("C10S2-convert-file-dumps","C10.S2",NV+"convert_file",'''def convert_file(output, file_name, docids, click_map):
    if not os.path.exists(file_name):
        print("{} not found.".format(file_name))
        sys.exit(1)
    print("Reading news data from " + file_name)

    with io.open(file_name, "r", encoding="utf-8") as f:

        field_list = ["news_id", "category", "subcategory", "title", "abstract", "url", "title_entities", "abstract_entities"]
        include_fields = set(field_list[0:6])

        reader = csv.DictReader(f, delimiter="\\t", fieldnames=field_list)
        for line in reader:
            if line["news_id"] in docids:
                continue
            if len(docids) > 0:
                output.write(",\\n")
            docid = line["news_id"]
            docids.add(docid)

            clicks = click_map[docid]["clicks"]
            impressions = click_map[docid]["impressions"]

            doc = {"put": f"id:{doc_type}:{doc_type}::{docid}", "fields" : {} }
            for field in include_fields:
                doc["fields"][field] = line[field]
            doc["fields"]["date"] = generate_random_date()  # data set does not include a publish date
            doc["fields"]["clicks"] = clicks
            doc["fields"]["impressions"] = impressions
            output.write(json.dumps(doc))''',"C10.S2 (close to C9.S1 fragmented writes). json.dump(doc, output) encodes through the pure-Python iterencode and writes many chunks; json.dumps uses the C encoder and one write, with the same text.")
TV="text-search/python/convert-to-vespa-format.py::"
sub("C10S2-convert-main-dumps","C10.S2",TV+"main",'''def main():
    document_offsets = load_document_offsets()

    docs = 0
    with io.open(docs_file, "r", encoding="utf-8") as f, open(out_file, "w") as out:
        for docid in document_offsets.keys():
            f.seek(document_offsets[docid])
            line = f.readline()
            line = line.strip()
            content = line.split("\\t")

            found_docid = content[0]
            if found_docid != docid:
                continue  # dataset has some wrong lookup values
            if len(content) != len(fields):
                continue  # missing fields

            if docs > 0:
                out.write("\\n")
            docs += 1

            doc = { "put" : f"id:{doc_type}:{doc_type}::{docid}", "fields" : {} }
            for i, field in enumerate(fields):
                doc["fields"][field] = content[i]
            out.write(json.dumps(doc))

        out.write("\\n")''',"C10.S2. Same json.dump to json.dumps-then-write change as in news convert_file.")
CM="use-case-shopping/convert_meta.py::"
sub("C10S4-convert-meta-categories-text","C10.S4",CM+"process",'''def process(data):
    fields = {}
    fields["asin"] = data["asin"]
    fields["timestamp"] = int(time.time()) - random.randint(0, 60*60*24*365)  # no date in data, set to a random value up to one year back
    fields["title"] = data["title"]
    fields["description"] = data["description"]
    fields["price"] = data["price"]
    fields["rating_stars"] = 0
    fields["rating_count"] = 0
    fields["images"] = [data["imUrl"]]

    if "brand" in data:
        fields["brand"] = data["brand"]

    # In the data set, categories are of the form
    #   [ ["Sports & Outdoors", "Accessories", "Sport Watches"] ]
    # For filtering on categories, these should be matched exactly, so we transform to
    #   [ "Sports & Outdoors", "Sports & Outdoors|Accessories", "Sports & Outdoors|Accessories|Sport Watches"]
    # because there are multiple subcategories with the same name, and
    # we want to maintain the category hierarchy for grouping.
    # For free text search however, we want to match on stemmed terms.
    # We have another field for this, and reverse the categories for better relevance:
    #   "Sport Watches Accessories Sports & Outdoors"
    if "categories" in data:
        fields["categories"] = []
        text_parts = []

        for category in data["categories"]:
            for level in range(len(category)):
                fields["categories"].append("|".join(category[0:level+1]))
            text_parts.append(" ".join(category[::-1]))
        fields["categories_text"] = "".join(text_parts)

    if "related" in data:
        related = []
        for key in data["related"]:
            related.extend(data["related"][key])
        fields["related"] = related

    document = {}
    document["put"] = "id:item:item::" + fields["asin"]
    document["fields"] = fields
    return document''',"C10.S4. `fields['categories_text'] +=` grows through a subscript; parts are joined once (no separator, as before).")
CR="use-case-shopping/convert_reviews.py::"
sub("C1S3-illegal-chars-single-return","C1.S3",CR+"contains_illegal_chars",'''def contains_illegal_chars(fields):
    return "\\u001a" in fields["reviewer_name"] or "\\u001a" in fields["title"] or "\\u001a" in fields["text"]''',"C1.S3. Three if-return-True branches then return False collapse to the boolean expression; `in` yields a bool and `or` short-circuits in the same order, so exceptions are the same.")
order=["C3S4-process-docs-docfreq","C10S1-count-terms-isdisjoint","C3S4-predictions-dict","C4S2-sample-valid-filter-first","C5S4-float-to-binary-no-where","C6S2-sample-images-select-first","C3S1-parse-page-findall","C10S4-split-text-parts","C1S4-add-impressions-local","C6S1-process-doc-chain","C1S4-what-language-text","C10S1-filter-any","C7S3-find-loop","C6S3-get-feed-docids-setcomp","C10S4-parse-file-parts","C10S2-convert-file-dumps","C10S2-write-json-term-replace","C10S1-accepted-process-docs-update","C6S3-read-common-words-stream","C1S1-process-docs-dead-total","C1S4-count-terms-window","C4S4-parse-page-elif","C8S3-annotate-data-local","C10S4-convert-meta-categories-text","C1S3-illegal-chars-single-return","C10S2-convert-main-dumps"]
assert sorted(order)==sorted(x["id"] for x in S)
S.sort(key=lambda x:order.index(x["id"]))
with open("/home/javad/energy-run/sample-apps/submissions.jsonl","w") as f:
    for s in S: f.write(json.dumps(s)+"\n")
print(len(S))
