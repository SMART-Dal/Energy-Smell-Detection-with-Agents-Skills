# Energy report — sample-apps @ e2ed22d

94 units listed, 83 with an accepted suspicion · 27 repairs submitted, 66 deferred · 11 confirmed · 5 partial · 1 mixed · 3 negligible · 7 over_limit · 11 applied
Noise floor 2.1% (from: session calibration).

## Applied

### `news/src/python/evaluate.py::predictions` — C3S4-predictions-index (C3.S4)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +99.1%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 19 `url, cert = connect()` (FileNotFoundError); line 103 `train_metrics = calc_metrics(train_impressions_file)` (SystemExit); line 104 `valid_metrics = calc_metrics(valid_impressions_file)` (SystemExit); line 106 `print("Train: " + str(train_metrics))` (NameError); line 107 `print("Valid: " + str(valid_metrics))` (NameError).
Loaded skipping failing top-level statements: line 19 `url, cert = connect()` (FileNotFoundError); line 103 `train_metrics = calc_metrics(train_impressions_file)` (SystemExit); line 104 `valid_metrics = calc_metrics(valid_impressions_file)` (SystemExit); line 106 `print("Train: " + str(train_metrics))` (NameError); line 107 `print("Valid: " + str(valid_metrics))` (NameError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| wide-children | 106.50 | 0.76 | +99.3% | 0.1% | yes |
| tail-matches | 100.96 | 0.57 | +99.4% | 0.0% | yes |
| float-relevance | 104.76 | 0.97 | +99.1% | 0.0% | yes |
| many-children | 99.83 | 1.37 | +98.6% | 0.1% | yes |

### `incremental-search/search-suggestions/count_terms.py::count_terms` — C3S2-count_terms-common-once (C3.S2)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +41.4%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| trigrams-long | 100.05 | 61.93 | +38.1% | 1.8% | yes |
| fourgrams | 110.01 | 61.96 | +43.7% | 1.4% | yes |
| fivegrams | 114.27 | 57.66 | +49.5% | 3.1% | yes |
| all-unique-trigrams | 79.49 | 52.35 | +34.1% | 0.7% | yes |

### `colbert-long/scripts/convert.py::remove_control_characters` — C10S1-remove_control_characters-translate (C10.S1)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +80.7%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 17 `documents = load_dataset('Shitao/MLDR', "corpus-en", spli...` (RuntimeError); line 19 `with open(feed_file, "w") as f:` (NameError).
Loaded skipping failing top-level statements: line 17 `documents = load_dataset('Shitao/MLDR', "corpus-en", spli...` (RuntimeError); line 19 `with open(feed_file, "w") as f:` (NameError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| ascii-prose | 99.89 | 7.99 | +92.0% | 0.8% | yes |
| unicode-mix | 102.68 | 53.29 | +48.1% | 1.0% | yes |
| long-line | 104.48 | 9.68 | +90.7% | 0.2% | yes |
| log-multiline | 104.09 | 8.49 | +91.8% | 0.4% | yes |

### `feed-split.py::what_language` — C1S4-what_language-text-once (C1.S4)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +15.3%.
Behaviour compared under a relaxed rule: loaded with these uninstalled packages stood in for: tiktoken.
Loaded with uninstalled packages stood in for: tiktoken.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| java-near-end | 61.75 | 55.17 | +10.7% | 1.1% | yes |
| no-markers | 61.45 | 55.06 | +10.4% | 0.1% | yes |
| curl-at-index-zero-large | 67.45 | 55.12 | +18.3% | 3.4% | yes |
| highlight-not-at-start | 70.48 | 55.09 | +21.8% | 0.1% | yes |

### `news/src/python/mind_data.py::MindData.add_impressions` — C8S3-add_impressions-content-once (C8.S3)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +6.6%.
Measured twice: the first measurement came out `partial` with an input too noisy to read, and this is the second.
The agent measured `partial`; re-measured `confirmed`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large-positives | 61.32 | 57.50 | +6.2% | 3.1% | yes |
| many-positives-few-negatives | 58.13 | 55.82 | +4.0% | 1.7% | yes |
| heavy-sampling | 65.56 | 60.54 | +7.7% | 1.6% | yes |
| medium | 63.80 | 58.41 | +8.4% | 0.7% | yes |

### `visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.float_to_binary_embedding` — C10S2-float_to_binary-bool (C10.S2)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +18.1%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 10 `from .colpali import SimMapGenerator` (ImportError).
Loaded skipping failing top-level statements: line 10 `from .colpali import SimMapGenerator` (ImportError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| all-positive-1024 | 65.19 | 53.70 | +17.6% | 5.5% | yes |
| all-negative-1024 | 64.77 | 53.11 | +18.0% | 0.2% | yes |
| zeros-mixed-2048 | 65.75 | 53.23 | +19.0% | 0.4% | yes |
| wide-8192 | 65.69 | 54.05 | +17.7% | 1.1% | yes |

### `text-video-search/src/python/embedding.py::sample_images` — C6S2-sample_images-index-first (C6.S2)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +73.2%.
Behaviour compared under a relaxed rule: loaded with these uninstalled packages stood in for: clip.
Loaded with uninstalled packages stood in for: clip.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| sample-8-of-80-uint8 | 114.48 | 38.54 | +66.3% | 0.8% | yes |
| sample-30-of-320-mid | 114.65 | 28.50 | +75.1% | 0.1% | yes |
| sample-20-of-200-gray | 108.36 | 31.89 | +70.6% | 2.5% | yes |
| sample-8-of-80-float32 | 109.03 | 21.13 | +80.6% | 0.1% | yes |

### `news/src/python/create_category_ctrs.py::read_impressions_file` — C10S2-category_ctrs-read_impressions-reader (C10.S2)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +32.6%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large | 72.02 | 55.73 | +22.6% | 6.7% | yes |
| single-impression | 106.87 | 42.22 | +60.5% | 1.6% | yes |
| skewed-categories | 66.92 | 53.78 | +19.6% | 2.5% | yes |
| diverse | 70.95 | 51.21 | +27.8% | 0.8% | yes |

### `news/src/python/mind_data.py::MindData.lookup_news_index` — C2S1-lookup_news_index-inline (C2.S1)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +25.1%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| hit-short-big-map | 42.03 | 31.25 | +25.6% | 2.1% | yes |
| hit-32-chars | 39.88 | 29.31 | +26.5% | 1.5% | yes |
| hit-64000-chars | 36.55 | 27.60 | +24.5% | 5.2% | yes |
| hit-100000-chars | 38.79 | 29.57 | +23.8% | 5.5% | yes |

### `news/src/python/mind_data.py::MindData.read_news` — C3S5-read_news-lazy-abstract (C3.S5)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +21.6%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| few-entities | 86.51 | 69.96 | +19.1% | 2.9% | yes |
| many-entities | 107.94 | 66.23 | +38.6% | 1.2% | yes |
| all-distinct-keys | 87.14 | 70.68 | +18.9% | 4.9% | yes |
| large-mixed | 80.72 | 73.00 | +9.6% | 4.6% | yes |

### `incremental-search/search-suggestions/accepted_words.py::process_docs` — C10S3-accepted_words-process_docs-update (C10.S3)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +8.5%.
The agent measured `partial`; re-measured `confirmed`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large-corpus | 66.00 | 59.97 | +9.1% | 5.7% | yes |
| duplicates | 70.07 | 64.21 | +8.4% | 4.0% | yes |
| skipped-docs | 65.91 | 60.76 | +7.8% | 0.8% | yes |
| mixed-case-digits | 70.45 | 64.22 | +8.8% | 1.5% | yes |

## Measured, not confirmed

### `incremental-search/search-suggestions/count_terms.py::process_docs` — C3S4-process_docs-docs-count (C3.S4)

**partial** — saves energy on 3 of 4 inputs ('many-docs', 'bigrams', 'trigrams'; best 59.6% +-3.0% on 'many-docs'), and no saving that can be told from noise on the rest: 'high-duplicates' +0.9% +-3.0% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +39.1%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| many-docs | 106.59 | 43.05 | +59.6% | 3.0% | yes |
| bigrams | 95.14 | 54.30 | +42.9% | 0.4% | yes |
| trigrams | 101.43 | 47.69 | +53.0% | 1.5% | yes |
| high-duplicates | 54.07 | 53.58 | +0.9% | 3.0% | no: pairs disagree |

### `news/src/python/mind_data.py::MindData.sample_valid_data` — C1S5-sample_valid_data-filter-first (C1.S5)

**negligible** — no case moved more than the noise: the largest reading was +1.3% +-1.9% on 'typical-valid', against a clean 2.1% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: +0.5%.
Also the repair for suspicion(s) b of this unit.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| typical-valid | 66.61 | 65.70 | +1.4% | 1.9% | no: pairs disagree |
| many-short-partial | 67.77 | 67.98 | -0.3% | 1.2% | no: pairs disagree |
| train-impressions | 60.77 | 60.22 | +0.9% | 2.5% | no: pairs disagree |
| many-short-low-prob | 54.62 | 54.49 | +0.2% | 0.8% | no: pairs disagree |

### `text-search/python/extract-msmarco.py::extract_documents` — C1S8-extract_documents-tell (C1.S8)

**partial** — saves energy on 2 of 4 inputs ('unicode-1500', 'mixed-3000'; best 7.9% +-7.2% on 'unicode-1500'), and no saving that can be told from noise on the rest: 'long-800' +0.5% +-1.4% (its pairs disagree too much to tell); 'long-1200' -0.4% +-3.2% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +2.9%.
Measured twice: the first measurement came out `partial` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| unicode-1500 | 62.73 | 57.73 | +8.0% | 7.2% | yes |
| long-800 | 59.55 | 59.26 | +0.5% | 1.4% | no: pairs disagree |
| mixed-3000 | 59.70 | 57.52 | +3.6% | 0.8% | yes |
| long-1200 | 59.30 | 59.51 | -0.3% | 3.2% | no: pairs disagree |

### `feed-split.py::split_text` — C10S4-split_text-join (C10.S4)

**negligible** — no case moved more than the noise: the largest reading was +0.9% +-0.3% on 'mixed-large', against a clean 2.1% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: +0.2%.
Behaviour compared under a relaxed rule: loaded with these uninstalled packages stood in for: tiktoken.
Loaded with uninstalled packages stood in for: tiktoken.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| lists-and-links | 65.23 | 65.53 | -0.4% | 4.3% | no: pairs disagree |
| top-level-tables | 61.06 | 60.76 | +0.5% | 1.7% | no: pairs disagree |
| tables-inside-divs | 59.71 | 59.84 | -0.2% | 1.6% | no: pairs disagree |
| mixed-large | 58.32 | 57.83 | +0.9% | 0.2% | no: within the floor |

### `news/src/python/metrics.py::ndcg_score` — C1S4-ndcg_score-discounts-once (C1.S4)

**mixed** — a trade-off, not a fix: 10.7% saved on 'k-gt-n-50k' but 4.2% lost on 'xlarge-300k-k10', both clearing the 2.1% noise floor. Whether it pays depends on which input the code actually sees, so the report must name both.
Mean saving across its cases: +2.1%.
Measured twice: the first measurement came out `mixed` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large-100k-k10 | 53.80 | 52.80 | +1.9% | 6.5% | no: pairs disagree |
| large-100k-k100 | 52.97 | 52.90 | +0.1% | 0.8% | no: pairs disagree |
| xlarge-300k-k10 | 54.15 | 56.44 | -4.2% | 1.8% | yes |
| k-gt-n-50k | 59.29 | 52.94 | +10.7% | 2.8% | yes |

### `examples/workshop-ecommerce/preprocess.py::process_users` — C3S6-process_users-limit-first (C3.S6)

**partial** — saves energy on 2 of 4 inputs ('limit-200', 'many-duplicates'; best 17.3% +-2.7% on 'limit-200'), and no saving that can be told from noise on the rest: 'full-150-users' +1.8% +-3.5% (its pairs disagree too much to tell); 'few-users-heavy' +0.5% +-0.9% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +8.5%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| full-150-users | 69.85 | 68.59 | +1.8% | 3.5% | no: pairs disagree |
| limit-200 | 78.88 | 65.25 | +17.3% | 2.7% | yes |
| few-users-heavy | 80.11 | 79.72 | +0.5% | 0.9% | no: pairs disagree |
| many-duplicates | 68.68 | 58.67 | +14.6% | 0.5% | yes |

### `news/src/python/train_cold_start.py::write_embeddings` — C10S3-train_cold_start-write_embeddings-tolist-once (C10.S3)

**partial** — saves energy on 3 of 4 inputs ('large', 'narrow', 'many'; best 8.7% +-3.3% on 'narrow'), and no saving that can be told from noise on the rest: 'wide' +0.0% +-0.8% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +5.5%.
Measured twice: the first measurement came out `partial` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large | 60.75 | 58.02 | +4.5% | 3.1% | yes |
| wide | 60.26 | 60.26 | +0.0% | 0.8% | no: pairs disagree |
| narrow | 63.02 | 57.52 | +8.7% | 3.3% | yes |
| many | 68.23 | 62.32 | +8.7% | 3.0% | yes |

### `incremental-search/search-suggestions/count_terms.py::process_docs` — C1S1-process_docs-total_count (C1.S1)

**negligible** — no case moved more than the noise: the largest reading was +1.1% +-2.9% on 'bigrams', against a clean 2.1% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: +0.7%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| many-docs | 60.77 | 60.56 | +0.3% | 1.9% | no: pairs disagree |
| bigrams | 58.67 | 58.04 | +1.1% | 2.9% | no: pairs disagree |
| trigrams | 55.61 | 55.26 | +0.6% | 1.6% | no: pairs disagree |
| high-duplicates | 54.92 | 54.50 | +0.8% | 0.3% | no: within the floor |

### `text-search/python/sample-queries-and-documents.py::select_documents` — C3S2-select_documents-bound (C3.S2)

**partial** — saves energy on 1 of 4 inputs ('query-duplicates'; best 31.4% +-5.7% on 'query-duplicates'), and no saving that can be told from noise on the rest: 'many-qids' -1.1% +-1.0% (within the 2.1% noise floor); 'large-offsets' +0.2% +-0.8% (its pairs disagree too much to tell); 'already-complete' +0.5% +-3.4% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does. Behaviour was compared under a relaxed rule, which the report must repeat: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 12 `data_dir = sys.argv[1]` (IndexError); line 16 `query_file = os.path.join(data_dir, "queries.tsv")` (NameError); line 17 `docs_file = os.path.join(data_dir, "docs.tsv")` (NameError); line 18 `offset_file = os.path.join(data_dir, "docs-offset.tsv")` (NameError); line 20 `sample_query_file = os.path.join(data_dir, "test-queries....` (NameError); line 21 `sample_offset_file = os.path.join(data_dir, "test-docs-of...` (NameError).
Mean saving across its cases: +7.7%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 12 `data_dir = sys.argv[1]` (IndexError); line 16 `query_file = os.path.join(data_dir, "queries.tsv")` (NameError); line 17 `docs_file = os.path.join(data_dir, "docs.tsv")` (NameError); line 18 `offset_file = os.path.join(data_dir, "docs-offset.tsv")` (NameError); line 20 `sample_query_file = os.path.join(data_dir, "test-queries....` (NameError); line 21 `sample_offset_file = os.path.join(data_dir, "test-docs-of...` (NameError).
Measured twice: the first measurement came out `negligible` with an input too noisy to read, and this is the second.
The agent measured `negligible`; re-measured `partial`.
Loaded skipping failing top-level statements: line 12 `data_dir = sys.argv[1]` (IndexError); line 16 `query_file = os.path.join(data_dir, "queries.tsv")` (NameError); line 17 `docs_file = os.path.join(data_dir, "docs.tsv")` (NameError); line 18 `offset_file = os.path.join(data_dir, "docs-offset.tsv")` (NameError); line 20 `sample_query_file = os.path.join(data_dir, "test-queries....` (NameError); line 21 `sample_offset_file = os.path.join(data_dir, "test-docs-of...` (NameError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| query-duplicates | 87.30 | 59.96 | +31.3% | 5.7% | yes |
| many-qids | 56.41 | 57.05 | -1.1% | 1.0% | no: within the floor |
| large-offsets | 54.84 | 54.71 | +0.2% | 0.8% | no: pairs disagree |
| already-complete | 55.62 | 55.31 | +0.6% | 3.5% | no: pairs disagree |

## Not measured

### `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator._prepare_similarity_map_tensor` — C3S2-prepare_sim_map-seq-length (C3.S2)

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures
The agent measured `no_inputs`; re-measured `over_limit`.

### `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.should_filter_token` — C8S2-should_filter_token-compiled-default (C8.S2)

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures
The agent measured `no_inputs`; re-measured `over_limit`.

### `news/src/python/evaluate.py::read_impressions_file` — C10S2-evaluate-read_impressions-reader (C10.S2)

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures

### `news/src/python/train_cold_start.py::read_bert_embeddings_from_file` — C8S3-read_bert_embeddings_from_file-news-once (C8.S3)

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures

### `incremental-search/search-suggestions/count_terms.py::write_json_file` — C10S2-write_json_file-replace (C10.S2)

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures

### `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.gen_similarity_maps` — C6S2-gen_similarity_maps-no-copy (C6.S2)

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures

### `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.gen_similarity_maps` — C3S2-gen_similarity_maps-filter-once (C3.S2)

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures

## Detected, not measured

Accepted findings with no measurement: deferred beyond the repairs chosen for measurement, or blocked.

- `news/src/python/evaluate.py::calc_metrics` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `news/src/python/evaluate.py::read_impressions_file` a: deferred — submitted as C10S2-evaluate-read_impressions-reader but over_limit: 20 repairs already had a verdict, so it was not measured
- `news/src/python/mind_data.py::MindData.read_news` b: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `news/src/python/train_cold_start.py::save_embeddings` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `news/src/python/train_cold_start.py::train_model` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `news/src/python/train_cold_start.py::read_bert_embeddings` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `news/src/python/train_cold_start.py::read_bert_embeddings_from_file` a: deferred — submitted as C8S3-read_bert_embeddings_from_file-news-once but over_limit: 20 repairs already had a verdict, so it was not measured
- `news/src/python/train_mf.py::save_embeddings` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `news/src/python/train_mf.py::write_embeddings` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `news/src/python/train_mf.py::eval_model` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `news/src/python/create_category_ctrs.py::read_impressions_file` b: deferred — inputs were requested and the unit is runnable here, but the 20 measured places went to repairs expected to save more, so no repair was submitted
- `news/src/python/create_category_ctrs.py::read_content_file` a: deferred — inputs were requested and the unit is runnable here, but the 20 measured places went to repairs expected to save more, so no repair was submitted
- `news/src/python/create_category_ctrs.py::write_news_category_ctr_update` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `incremental-search/search-suggestions/count_terms.py::process_doc` a: deferred — inputs were requested and the unit is runnable here, but the 20 measured places went to repairs expected to save more, so no repair was submitted
- `incremental-search/search-suggestions/count_terms.py::write_json_file` a: deferred — submitted as C10S2-write_json_file-replace but over_limit: 20 repairs already had a verdict, so it was not measured
- `incremental-search/search-suggestions/count_terms.py::read_common_words` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `incremental-search/search-suggestions/accepted_words.py::write_to_file` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `incremental-search/search-suggestions/accepted_words.py::read_common_words` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `text-search/python/extract-msmarco.py::getcontent` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `text-search/python/collect_training_data.py::build_dataset` b: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `text-search/python/collect_training_data.py::load_processed_queries` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `text-search/python/sample-queries-and-documents.py::load_queries` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `text-search/python/convert-to-vespa-format.py::main` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.gen_similarity_maps` b: blocked — inputs.py: the unit's module does not load here: AttributeError: SimMapGenerator is not defined here: loading the module skipped line 19 `class SimMapGenerator:` (TypeError), with stand-ins for colpali_engine (repair written in submissions.jsonl as C3S2-gen_similarity_maps-filter-once)
- `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.gen_similarity_maps` c: blocked — inputs.py: the unit's module does not load here: AttributeError: SimMapGenerator is not defined here: loading the module skipped line 19 `class SimMapGenerator:` (TypeError), with stand-ins for colpali_engine (repair written in submissions.jsonl as C6S2-gen_similarity_maps-no-copy)
- `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.should_filter_token` a: blocked — verify.py: no_inputs: the unit's module does not load here: AttributeError: SimMapGenerator is not defined here: loading the module skipped line 19 `class SimMapGenerator:` (TypeError), with stand-ins for colpali_engine (repair is written in submissions.jsonl as C8S2-should_filter_token-compiled-default)
- `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator._prepare_similarity_map_tensor` a: blocked — verify.py: no_inputs: the unit's module does not load here: AttributeError: SimMapGenerator is not defined here: loading the module skipped line 19 `class SimMapGenerator:` (TypeError), with stand-ins for colpali_engine (repair is written in submissions.jsonl as C3S2-prepare_sim_map-seq-length)
- `visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.get_suggestions` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `visual-retrieval-colpali/src/main.py::get_and_store_sim_maps` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `visual-retrieval-colpali/src/main.py::get_and_store_sim_maps` b: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `visual-retrieval-colpali/src/main.py::message_generator` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `visual-retrieval-colpali/src/backend/cache.py::LRUCache.get` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `visual-retrieval-colpali/src/backend/cache.py::LRUCache.delete` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `visual-retrieval-colpali/src/frontend/app.py::SearchResult` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `visual-retrieval-colpali/src/frontend/app.py::ChatResult` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `visual-retrieval-colpali/prepare_feed_deploy.py::download_pdf` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `visual-retrieval-colpali/prepare_feed_deploy.py::float_to_binary_embedding` b: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `test/pseudo_terminal.py::Log.write` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `test/test.py::exec_file` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `test/test.py::exec_wait` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/utils/helpers.py::get_latest_ai_or_human_message` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::subgraph_GenerateKeywords` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `examples/embedder-auto-training-evaluation/training-evaluation/train.py::TrainDataset.__getitem__` a: blocked — inputs.py: it cannot run here: `TrainDataset.__getitem__` always finishes by constructing a `sentence_transformers.InputExample`, and `sentence_transformers` is not available in this environment (it is stubbed)
- `examples/embedder-auto-training-evaluation/training-evaluation/train.py::TrainDataset.__init__` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `examples/embedder-auto-training-evaluation/training-evaluation/positives-negatives.py::search` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `text-video-search/src/python/embedding.py::extract_images` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `text-video-search/src/python/embedding.py::VideoFeedDataset.__getitem__` b: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `text-video-search/src/python/app.py::get_predefined_queries` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `examples/workshop-ecommerce/preprocess.py::process_users` b: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `examples/workshop-ecommerce/preprocess.py::process_orders` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `use-case-shopping/convert_meta.py::main` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `use-case-shopping/convert_reviews.py::main` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `billion-scale-vector-search/app/src/main/python/recall.py::knn_result_read` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `rag-blueprint/eval/train_lightgbm.py::perform_cross_validation` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `rag-blueprint/eval/train_logistic_regression.py::perform_cross_validation` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `rag-blueprint/eval/train_logistic_regression.py::perform_cross_validation` b: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `examples/ecommerce-user-preferences/webapp/app.py::query_vespa` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `examples/ecommerce-user-preferences/webapp/app.py::get_car_image` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `examples/ecommerce-user-preferences/webapp/app.py::load_system_prompt` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `examples/ecommerce-user-preferences/webapp/app.py::get_wikipedia_image` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `examples/google-cloud/cloud-functions/python/main.py::get_blobs` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `examples/google-cloud/cloud-functions/python/main.py::getlogs` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `multilingual-search/ext/evaluate.py::search` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `news/src/python/vespa_client.py::query_news` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `billion-scale-image-search/app/src/main/python/clip_export.py::CLIPTransformerExporter.encode_text` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `examples/in-context-learning/categorize_group.py::inference` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `feed_to_vespa.py::update_endpoint` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `feed_to_vespa.py::vespa_remove` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `incremental-search/search-as-you-type/feed_to_vespa.py::update_endpoint` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `incremental-search/search-as-you-type/feed_to_vespa.py::update_endpoint` b: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
- `reverse-image-search/script/feed.py::run` a: deferred — outside the 20 repairs measured; inputs not requested (expected saving small, or the unit calls a live service, model download or cloud API in its body)
