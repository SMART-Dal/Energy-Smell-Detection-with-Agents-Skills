import json
subs = []

subs.append(dict(
 id="add-impressions-bind-content",
 unit="news/src/python/mind_data.py::MindData.add_impressions",
 changed={"news/src/python/mind_data.py::MindData.add_impressions": '''def add_impressions(self, impression, user_indices, news_indices, category_indices, subcategory_indices, entity_indices, labels, num_negatives):
    user_index = impression["user_index"]
    positive, negative = self.find_clicked(impression["news_indices"], impression["labels"])

    # add each positive label
    for pos_news_index in positive:
        user_indices.append(user_index)
        news_indices.append(pos_news_index)
        content = self.news_content[pos_news_index]
        category_indices.append(content["category_index"])
        subcategory_indices.append(content["subcategory_index"])
        entity_indices.append(content["entity_index"])
        labels.append(1)

        # for each positive label, sample negative labels
        for neg_news_index in random.sample(negative, min(num_negatives, len(negative))):
            user_indices.append(user_index)
            news_indices.append(neg_news_index)
            content = self.news_content[neg_news_index]
            category_indices.append(content["category_index"])
            subcategory_indices.append(content["subcategory_index"])
            entity_indices.append(content["entity_index"])
            labels.append(0)'''},
 sole_caller_evidence=None,
 notes="Binds self.news_content[index] once per generated row instead of three subscripts. Callers: sample_training_data only (mind_data.py), so no other reader sees the change.",
))

subs.append(dict(
 id="write-embedding-single-write",
 unit="news/src/python/create_bert_embeddings.py::write_embedding",
 changed={"news/src/python/create_bert_embeddings.py::write_embedding": '''def write_embedding(f, embedding):
    f.write("\\t")
    f.write(",".join("%.4f" % num for num in embedding))'''},
 sole_caller_evidence=None,
 notes="Writes the joined values in one call instead of one write per float; identical bytes.",
))

subs.append(dict(
 id="write-embeddings-tolist-once",
 unit="news/src/python/train_cold_start.py::write_embeddings",
 changed={"news/src/python/train_cold_start.py::write_embeddings": '''def write_embeddings(id_to_index_map, embeddings, file_name):
    rows = embeddings.tolist()
    with open(os.path.join(data_dir, file_name), "w") as f:
        for id, index in id_to_index_map.items():
            f.write("{}\\t{}\\n".format(id, ",".join(["%.6f" % i for i in rows[index]])))'''},
 sole_caller_evidence=None,
 notes="Converts the matrix once instead of one tensor view and tolist per row. Callers: save_embeddings only.",
))

subs.append(dict(
 id="split-text-join-lines",
 unit="feed-split.py::split_text",
 changed={"feed-split.py::split_text": '''def split_text(soup):
    split_tables(soup)
    split_lists(soup)
    md = markdownify(str(soup), heading_style='ATX', code_language_callback=what_language, strip=['img'])
    lines = md.split("\\n")
    header = ""
    id = ""
    data = []
    buf = []
    for line in lines:
        if line.startswith("#"):
            if buf:
                data.append((id, header, "".join("\\n" + l for l in buf)))
                buf = []
            header = line.lstrip("#")
            id = "-".join(header.split()).lower()
        else:
            buf.append(line)

    data.append((id, header, "".join("\\n" + l for l in buf))) #Flush any last data
    return data'''},
 sole_caller_evidence=None,
 notes="Collects section lines and joins once per section; the joined text equals the original running concatenation, and an empty buffer gives the empty string as before.",
))

subs.append(dict(
 id="format-q-embs-bulk-tolist",
 unit="visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.format_q_embs",
 changed={"visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.format_q_embs": '''def format_q_embs(self, q_embs: torch.Tensor) -> dict:
    """
    Convert query embeddings to a dictionary of lists.

    Args:
        q_embs (torch.Tensor): Query embeddings tensor.

    Returns:
        dict: Dictionary where each key is an index and value is the embedding list.
    """
    if isinstance(q_embs, torch.Tensor):
        return dict(enumerate(q_embs.tolist()))
    return {idx: emb.tolist() for idx, emb in enumerate(q_embs)}'''},
 sole_caller_evidence=None,
 notes="Tensor input converts in one tolist call; other inputs keep the original loop. Readers: query_vespa_bm25 and query_vespa_colpali in vespa_app.py.",
))

subs.append(dict(
 id="extract-documents-track-offset",
 unit="text-search/python/extract-msmarco.py::extract_documents",
 changed={"text-search/python/extract-msmarco.py::extract_documents": r'''def extract_documents(docoffset):
    print("Extracting {0} documents...".format(len(docoffset.keys())))
    with open(os.path.join(download_dir, "msmarco-docs.tsv"), encoding="utf8" ) as f, \
         open(docs_file, "w", encoding="utf8") as out, \
         open(offset_file, "w", encoding="utf8") as offset:
        pos = 0
        for docid in docoffset.keys():
            offset.write("{0}\t{1}\n".format(docid, pos))
            s = getcontent(docid, f, docoffset)
            out.write(s)
            pos += len(s.encode("utf8"))'''},
 sole_caller_evidence=None,
 notes="Keeps a running byte count instead of calling out.tell(), which flushes and seeks once per document. Files are utf8 text on Linux, so the offsets are identical.",
))

subs.append(dict(
 id="convert-main-json-dumps",
 unit="text-search/python/convert-to-vespa-format.py::main",
 changed={"text-search/python/convert-to-vespa-format.py::main": '''def main():
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

        out.write("\\n")'''},
 sole_caller_evidence=None,
 notes="One write of the encoded document instead of json.dump's per-fragment writes; with default arguments the text is identical.",
))

subs.append(dict(
 id="process-users-itertuples",
 unit="examples/workshop-ecommerce/preprocess.py::process_users",
 changed={"examples/workshop-ecommerce/preprocess.py::process_users": '''def process_users(output_dir: Path, full: bool = False, limit: int = 10) -> None:
    """Process user data by aggregating orders and building user profiles."""
    print("Processing users...")

    df_order = pd.read_csv("dataset/orders.csv")

    # Read order_products from train set to build user profiles
    df_order_products_train = pd.read_csv("dataset/order_products__train.csv")

    # Merge order_products with orders to get order metadata
    df_order_products_with_metadata = df_order_products_train.merge(
        df_order[["order_id", "user_id", "order_dow", "order_hour_of_day"]],
        on="order_id",
        how="left",
    )

    # Group by user_id to create user documents
    user_groups = df_order_products_with_metadata.groupby("user_id")

    output_file = output_dir / "users.jsonl"

    with open(output_file, "w") as f:
        for i, (user_id, user_purchases_df) in enumerate(user_groups):
            # Build user profile (weightedset of product_ids based on frequency)
            product_counts = user_purchases_df["product_id"].value_counts()
            user_profile = {
                int(prod_id): int(count) for prod_id, count in product_counts.items()
            }

            # Build user_purchases array - flatten each product into a separate purchase
            purchases_array = []
            for purchase in user_purchases_df.itertuples(index=False):
                purchase_struct = {
                    "order_dow": int(purchase.order_dow),
                    "order_hour_of_day": int(purchase.order_hour_of_day),
                    "order_id": int(purchase.order_id),
                    "product_id": int(purchase.product_id),
                }
                purchases_array.append(purchase_struct)

            doc = {
                "put": f"id:users:user::{int(user_id)}",
                "fields": {
                    "user_id": int(user_id),
                    "user_profile": user_profile,
                    "user_purchases": purchases_array,
                },
            }
            f.write(json.dumps(doc) + "\\n")

            if not full and i >= limit - 1:
                break

    total_users = len(user_groups) if full else min(limit, len(user_groups))
    print(f"✓ Wrote {total_users} users to {output_file}")'''},
 sole_caller_evidence="process_users is called only from main() in preprocess.py; the edit changes no other function or state.",
 notes="Reads each purchase by attribute instead of building a pandas Series per row; purchase order and values are unchanged.",
))

with open("submissions.jsonl", "w", encoding="utf-8") as f:
    for s in subs:
        f.write(json.dumps(s, ensure_ascii=False) + "\n")
print("wrote", len(subs))
