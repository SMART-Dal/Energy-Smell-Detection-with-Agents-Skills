import json
subs = []

subs.append(dict(
 id="sample-valid-data-cache-tensors",
 unit="news/src/python/mind_data.py::MindData.sample_valid_data",
 changed={"news/src/python/mind_data.py::MindData.sample_valid_data": '''def sample_valid_data(self, prob=1.0, train=False):
    data = []
    impressions = self.train_impressions if train else self.valid_impressions
    cache = self.__dict__.setdefault("_sample_valid_cache", {})
    for pos, impression in enumerate(impressions):
        if random.random() <= prob:
            key = (train, pos)
            if key not in cache:
                news_indices = impression["news_indices"]
                labels = impression["labels"]
                category_indices = [ self.news_content[index]["category_index"] for index in news_indices ]
                subcategory_indices = [ self.news_content[index]["subcategory_index"] for index in news_indices ]
                entity_indices = [ self.news_content[index]["entity_index"] for index in news_indices ]
                user_index = [ impression["user_index"] ] * len(labels)
                if sum(labels) > 0 and sum(labels) != len(labels):
                    cache[key] = [
                        torch.LongTensor(user_index),
                        torch.LongTensor(news_indices),
                        torch.LongTensor(category_indices),
                        torch.LongTensor(subcategory_indices),
                        torch.LongTensor(entity_indices),
                        torch.FloatTensor(labels)
                    ]
                else:
                    cache[key] = None
            if cache[key] is not None:
                data.append(cache[key])
    return data'''},
 sole_caller_evidence=None,
 notes="The per-impression tensors are built once per instance and reused; random.random() is still drawn once per impression in the same order, so the random stream is unchanged. Callers (train_mf.py, train_cold_start.py) read the tuples only.",
))

subs.append(dict(
 id="float-to-binary-stacked-packbits",
 unit="visual-retrieval-colpali/prepare_feed_deploy.py::float_to_binary_embedding",
 changed={"visual-retrieval-colpali/prepare_feed_deploy.py::float_to_binary_embedding": '''def float_to_binary_embedding(float_query_embedding: dict) -> dict:
    """Utility function to convert float query embeddings to binary query embeddings."""
    try:
        arr = np.array(list(float_query_embedding.values()))
    except ValueError:
        arr = None
    if arr is not None and arr.ndim == 2:
        packed = np.packbits(arr > 0, axis=1).astype(np.int8).tolist()
        return dict(zip(float_query_embedding.keys(), packed))
    binary_query_embeddings = {}
    for k, v in float_query_embedding.items():
        binary_vector = (
            np.packbits(np.where(np.array(v) > 0, 1, 0)).astype(np.int8).tolist()
        )
        binary_query_embeddings[k] = binary_vector
    return binary_query_embeddings'''},
 sole_caller_evidence=None,
 notes="Packs all rows in one numpy call when the rows form a 2-D array; ragged or empty input takes the original loop. Packing along axis 1 equals per-row packing of 1-D rows.",
))

subs.append(dict(
 id="should-filter-token-precompiled",
 unit="visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.should_filter_token",
 changed={"visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.should_filter_token": r'''@staticmethod
def should_filter_token(token: str, _pattern=re.compile(
    r"^<.*$|^\s+$|^(?!.*\d)(?!▁)[^\w\s]+$|^_.*$|^Question$|^▁$"
)) -> bool:
    """
    Determines if a token should be filtered out based on predefined patterns.

    The function filters out tokens that:

        - Start with '<' (e.g., '<bos>')
        - Consist entirely of whitespace
        - Are purely punctuation (excluding tokens that contain digits or start with '▁')
        - Start with an underscore '_'
        - Exactly match the word 'Question'
        - Are exactly the single character '▁'

    Output of test:
        Token: '2'         | False
        Token: '0'         | False
        Token: '2'         | False
        Token: '3'         | False
        Token: '▁2'        | False
        Token: '▁hi'       | False
        Token: 'norwegian' | False
        Token: 'unlisted'  | False
        Token: '<bos>'     | True
        Token: 'Question'  | True
        Token: ':'         | True
        Token: '<pad>'     | True
        Token: '\n'        | True
        Token: '▁'         | True
        Token: '?'         | True
        Token: ')'         | True
        Token: '%'         | True
        Token: '/)'        | True


    Args:
        token (str): The token to check.

    Returns:
        bool: True if the token should be filtered out, False otherwise.
    """
    return bool(_pattern.match(token))'''},
 sole_caller_evidence=None,
 notes="The pattern is compiled once as a default argument instead of on every call; callers pass one argument, so the return value is unchanged. The saving is only the per-call cache lookup in re, so it is expected to be small.",
))

subs.append(dict(
 id="convert-user-embeddings-tolist",
 unit="news/src/python/convert_embeddings_to_vespa_format.py::convert_user_embeddings",
 changed={"news/src/python/convert_embeddings_to_vespa_format.py::convert_user_embeddings": '''def convert_user_embeddings():
    user_embeddings = read_embeddings(user_embeddings_file)
    with open(user_embeddings_vespa, "w") as out:
        out.write("[\\n")
        for i, (user_id, embedding) in enumerate(user_embeddings.items()):
            if i > 0:
                out.write(",\\n")
            embedding_str = ",".join(["%.6f" % v for v in embedding.tolist()])
            out.write('{"put": "id:user:user::%s", ' % user_id +
                      '"fields": {"user_id":"%s", ' % user_id +
                      '"embedding": {"values": [%s]} }}' % embedding_str)
        out.write("\\n]\\n")'''},
 sole_caller_evidence=None,
 notes="Converts each embedding with one tolist call instead of iterating numpy scalars; the formatted bytes are identical.",
))

subs.append(dict(
 id="convert-news-embeddings-tolist",
 unit="news/src/python/convert_embeddings_to_vespa_format.py::convert_news_embeddings",
 changed={"news/src/python/convert_embeddings_to_vespa_format.py::convert_news_embeddings": '''def convert_news_embeddings():
    news_embeddings = read_embeddings(news_embeddings_file)
    with open(news_embeddings_vespa, "w") as out:
        out.write("[\\n")
        for i, (news_id, embedding) in enumerate(news_embeddings.items()):
            if i > 0:
                out.write(",\\n")
            embedding_str = ",".join(["%.6f" % v for v in embedding.tolist()])
            out.write('{"update": "id:news:news::%s", ' % news_id +
                      '"fields": {"embedding": {"assign": { "values": [%s]} }}}' % embedding_str)
        out.write("\\n]\\n")'''},
 sole_caller_evidence=None,
 notes="Same as convert-user-embeddings-tolist for the news table.",
))

subs.append(dict(
 id="category-tensor-once-per-category",
 unit="news/src/python/create_category_ctrs.py::write_news_category_ctr_update",
 changed={"news/src/python/create_category_ctrs.py::write_news_category_ctr_update": '''def write_news_category_ctr_update(news_to_cat_map):
    global_ctr_document_id = "id:category_ctr:category_ctr::global"
    category_tensors = {}
    with open(news_category_ctr_update_file, "w") as out:
        out.write("[\\n")
        for i, (news_id, category) in enumerate(news_to_cat_map.items()):
            if i > 0:
                out.write(",\\n")
            if category not in category_tensors:
                category_tensors[category] = '{"cells": [{"address":{"category":"%s"}, "value": 1.0}]}' % category
            category_tensor = category_tensors[category]
            out.write('{"update": "id:news:news::%s", ' % news_id +
                      '"fields": {' +
                          '"category_ctr_ref": {"assign": "%s"}, ' % global_ctr_document_id +
                          '"category_tensor": {"assign": %s}' % category_tensor +
                      '}}')
        out.write("\\n]\\n")'''},
 sole_caller_evidence=None,
 notes="Formats the category tensor string once per distinct category instead of once per news item; the written bytes are identical.",
))

with open("submissions.jsonl", "a", encoding="utf-8") as f:
    for s in subs:
        f.write(json.dumps(s, ensure_ascii=False) + "\n")
print("appended", len(subs))
