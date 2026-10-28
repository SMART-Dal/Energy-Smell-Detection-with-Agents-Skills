import json, sys
sys.argv = ["x"]
exec(open("/tmp/energy-scratch/make_subs.py").read().split("S = []")[0])  # reuse func_source/apply
S = []
def sub(id_, rc, unit, changed_pairs, notes):
    changed = {}
    for (p, q, pairs) in changed_pairs:
        changed[f"{p}::{q}"] = apply(p, q, pairs)
    S.append({"id": id_, "root_cause": rc, "unit": unit, "changed": changed, "sole_caller_evidence": None, "notes": notes})

sub("C5S3-bert-float32", "C5.S3", "news/src/python/train_cold_start.py::read_bert_embeddings", [
 ("news/src/python/train_cold_start.py", "read_bert_embeddings", [
  ("    embeddings = np.zeros([len(data_loader.news()), 512])\n",
   "    embeddings = np.zeros([len(data_loader.news()), 512], dtype=np.float32)\n", 1)])],
 "C5.S3. The buffer is float32 instead of float64; values are rounded to float32 on assignment either way, and torch.FloatTensor then sees the same float32 numbers, so the output tensor is identical at half the buffer size.")

def ded(s):
    return "\n".join(l[4:] if l.startswith("    ") else l for l in s.split("\n"))
_old1 = """        for pos_news_index in positive:
            user_indices.append(user_index)
            news_indices.append(pos_news_index)
            category_indices.append(self.news_content[pos_news_index]["category_index"])
            subcategory_indices.append(self.news_content[pos_news_index]["subcategory_index"])
            entity_indices.append(self.news_content[pos_news_index]["entity_index"])
"""
_new1 = """        for pos_news_index in positive:
            pos_content = self.news_content[pos_news_index]
            user_indices.append(user_index)
            news_indices.append(pos_news_index)
            category_indices.append(pos_content["category_index"])
            subcategory_indices.append(pos_content["subcategory_index"])
            entity_indices.append(pos_content["entity_index"])
"""
_old2 = """            for neg_news_index in random.sample(negative, min(num_negatives, len(negative))):
                user_indices.append(user_index)
                news_indices.append(neg_news_index)
                category_indices.append(self.news_content[neg_news_index]["category_index"])
                subcategory_indices.append(self.news_content[neg_news_index]["subcategory_index"])
                entity_indices.append(self.news_content[neg_news_index]["entity_index"])
"""
_new2 = """            for neg_news_index in random.sample(negative, min(num_negatives, len(negative))):
                neg_content = self.news_content[neg_news_index]
                user_indices.append(user_index)
                news_indices.append(neg_news_index)
                category_indices.append(neg_content["category_index"])
                subcategory_indices.append(neg_content["subcategory_index"])
                entity_indices.append(neg_content["entity_index"])
"""
sub("C1S4-impression-lookup", "C1.S4", "news/src/python/mind_data.py::MindData.add_impressions", [
 ("news/src/python/mind_data.py", "MindData.add_impressions", [
  (ded(_old1), ded(_new1), 1), (ded(_old2), ded(_new2), 1)])],
 "C1.S4. Each sample's news_content entry is looked up once into a local and read from there. The dict values are the same objects, so the appended values are unchanged.")

sub("C3S1-users-records", "C3.S1", "examples/workshop-ecommerce/preprocess.py::process_users", [
 ("examples/workshop-ecommerce/preprocess.py", "process_users", [
  ('            for _, purchase in user_purchases_df.iterrows():\n',
   '            for purchase in user_purchases_df.to_dict("records"):\n', 1)])],
 "C3.S1. Each purchase is a dict of native values instead of a per-row pandas Series; the four fields read are the same values converted with int() as before.")

sub("C1S1-dead-total", "C1.S1", "incremental-search/search-suggestions/count_terms.py::process_docs", [
 ("incremental-search/search-suggestions/count_terms.py", "process_docs", [
  ("        total_count = sum([count for count in counts.values()])\n", "", 1)])],
 "C1.S1. total_count is bound and never read; the sum over each document's counts is removed. Nothing else in the function depends on it.")

S2 = [json.loads(l) for l in open("/home/javad/energy-run/sample-apps/submissions.jsonl")]
for s in S: S2.append(s)
with open("/home/javad/energy-run/sample-apps/submissions.jsonl", "w") as f:
    for s in S2: f.write(json.dumps(s, ensure_ascii=False) + "\n")
print("total submissions:", len(S2))
