# Energy report — sample-apps @ e2ed22d

141 units listed, 102 with an accepted suspicion · 26 repairs submitted, 95 deferred · 10 confirmed · 3 partial · 2 regressed · 5 negligible · 6 over_limit · 9 applied
Noise floor 2.3% (from: session calibration).

## Applied

### `incremental-search/search-suggestions/count_terms.py::count_terms` — C10S1-count-terms-isdisjoint (C10.S1)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +39.6%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| trigrams-long | 89.43 | 57.02 | +36.2% | 0.8% | yes |
| fourgrams | 94.73 | 55.95 | +40.9% | 0.3% | yes |
| fivegrams | 107.19 | 57.83 | +46.0% | 0.6% | yes |
| all-unique-trigrams | 89.73 | 58.27 | +35.1% | 1.7% | yes |

### `news/src/python/evaluate.py::predictions` — C3S4-predictions-dict (C3.S4)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +99.1%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 19 `url, cert = connect()` (FileNotFoundError); line 103 `train_metrics = calc_metrics(train_impressions_file)` (SystemExit); line 104 `valid_metrics = calc_metrics(valid_impressions_file)` (SystemExit); line 106 `print("Train: " + str(train_metrics))` (NameError); line 107 `print("Valid: " + str(valid_metrics))` (NameError).
Loaded skipping failing top-level statements: line 19 `url, cert = connect()` (FileNotFoundError); line 103 `train_metrics = calc_metrics(train_impressions_file)` (SystemExit); line 104 `valid_metrics = calc_metrics(valid_impressions_file)` (SystemExit); line 106 `print("Train: " + str(train_metrics))` (NameError); line 107 `print("Valid: " + str(valid_metrics))` (NameError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| wide-children | 109.60 | 0.79 | +99.3% | 0.1% | yes |
| tail-matches | 113.35 | 0.62 | +99.4% | 0.1% | yes |
| float-relevance | 112.78 | 1.04 | +99.1% | 0.0% | yes |
| many-children | 110.10 | 1.53 | +98.6% | 0.1% | yes |

### `visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.float_to_binary_embedding` — C5S4-float-to-binary-no-where (C5.S4)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +19.1%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 10 `from .colpali import SimMapGenerator` (ImportError).
Loaded skipping failing top-level statements: line 10 `from .colpali import SimMapGenerator` (ImportError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| all-positive-1024 | 65.96 | 53.55 | +18.8% | 1.3% | yes |
| all-negative-1024 | 68.15 | 54.65 | +19.8% | 6.0% | yes |
| zeros-mixed-2048 | 70.73 | 57.07 | +19.3% | 0.5% | yes |
| wide-8192 | 71.67 | 58.58 | +18.3% | 0.7% | yes |

### `text-video-search/src/python/embedding.py::sample_images` — C6S2-sample-images-select-first (C6.S2)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +72.3%.
Behaviour compared under a relaxed rule: loaded with these uninstalled packages stood in for: clip.
Loaded with uninstalled packages stood in for: clip.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| sample-8-of-80-uint8 | 113.86 | 39.03 | +65.7% | 0.2% | yes |
| sample-30-of-320-mid | 114.79 | 29.62 | +74.2% | 0.3% | yes |
| sample-20-of-200-gray | 105.10 | 33.03 | +68.6% | 0.3% | yes |
| sample-8-of-80-float32 | 108.30 | 21.05 | +80.6% | 0.3% | yes |

### `news/src/python/mind_data.py::MindData.add_impressions` — C1S4-add-impressions-local (C1.S4)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +7.8%.
The agent measured `partial`; re-measured `confirmed`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large-positives | 62.72 | 57.61 | +8.2% | 1.7% | yes |
| many-positives-few-negatives | 61.42 | 57.93 | +5.7% | 1.1% | yes |
| heavy-sampling | 66.87 | 61.76 | +7.6% | 0.8% | yes |
| medium | 64.94 | 58.67 | +9.7% | 2.3% | yes |

### `feed-split.py::what_language` — C1S4-what-language-text (C1.S4)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +15.1%.
Behaviour compared under a relaxed rule: loaded with these uninstalled packages stood in for: tiktoken.
Loaded with uninstalled packages stood in for: tiktoken.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| java-near-end | 62.75 | 56.15 | +10.5% | 0.4% | yes |
| no-markers | 62.81 | 56.30 | +10.4% | 0.5% | yes |
| curl-at-index-zero-large | 68.63 | 56.48 | +17.7% | 0.7% | yes |
| highlight-not-at-start | 72.32 | 56.56 | +21.8% | 1.5% | yes |

### `news/src/python/convert_to_vespa_format.py::convert_file` — C10S2-convert-file-dumps (C10.S2)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +27.2%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large-8k | 112.22 | 76.03 | +32.2% | 3.6% | yes |
| long-text | 74.19 | 60.75 | +18.1% | 2.5% | yes |
| short-text-8k | 99.83 | 62.93 | +37.0% | 1.0% | yes |
| entity-heavy | 79.51 | 62.49 | +21.4% | 0.8% | yes |

### `incremental-search/search-suggestions/accepted_words.py::process_docs` — C10S1-accepted-process-docs-update (C10.S1)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +8.2%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large-corpus | 69.44 | 63.53 | +8.5% | 0.5% | yes |
| duplicates | 74.39 | 68.82 | +7.5% | 1.9% | yes |
| skipped-docs | 68.46 | 63.05 | +7.9% | 0.5% | yes |
| mixed-case-digits | 71.66 | 65.43 | +8.7% | 0.8% | yes |

### `incremental-search/search-suggestions/count_terms.py::read_common_words` — C6S3-read-common-words-stream (C6.S3)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +5.3%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large | 62.69 | 58.39 | +6.9% | 1.4% | yes |
| duplicates | 59.92 | 56.69 | +5.4% | 1.5% | yes |
| long-lines | 61.14 | 58.51 | +4.3% | 1.1% | yes |
| numeric-tokens | 60.13 | 57.41 | +4.5% | 1.0% | yes |

## Confirmed, not applied

### `incremental-search/search-suggestions/count_terms.py::count_terms` — C1S4-count-terms-window (C1.S4)

**confirmed** — not applied: changes the same function as C10S1-count-terms-isdisjoint, which is applied; both were written against the original, so only one can be
Mean saving across its cases: +6.9%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| trigrams-long | 64.36 | 59.71 | +7.2% | 1.4% | yes |
| fourgrams | 61.89 | 57.90 | +6.5% | 1.8% | yes |
| fivegrams | 61.03 | 58.27 | +4.5% | 0.2% | yes |
| all-unique-trigrams | 64.05 | 58.14 | +9.2% | 1.9% | yes |

## Measured, not confirmed

### `incremental-search/search-suggestions/count_terms.py::process_docs` — C3S4-process-docs-docfreq (C3.S4)

**partial** — saves energy on 3 of 4 inputs ('many-docs', 'bigrams', 'trigrams'; best 59.0% +-0.7% on 'many-docs'), and no saving that can be told from noise on the rest: 'high-duplicates' +2.2% +-1.7% (within the 2.3% noise floor). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +39.6%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| many-docs | 110.70 | 45.41 | +59.0% | 0.7% | yes |
| bigrams | 102.22 | 57.58 | +43.7% | 0.2% | yes |
| trigrams | 108.60 | 50.57 | +53.4% | 1.7% | yes |
| high-duplicates | 61.70 | 60.36 | +2.2% | 1.7% | no: within the floor |

### `news/src/python/mind_data.py::MindData.sample_valid_data` — C4S2-sample-valid-filter-first (C4.S2)

**negligible** — no case moved more than the noise: the largest reading was +0.5% +-0.6% on 'typical-valid', against a clean 2.3% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: +0.1%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| typical-valid | 57.14 | 56.83 | +0.5% | 0.6% | no: pairs disagree |
| many-short-partial | 58.24 | 58.11 | +0.2% | 0.7% | no: pairs disagree |
| train-impressions | 58.83 | 58.81 | +0.0% | 0.5% | no: pairs disagree |
| many-short-low-prob | 59.60 | 59.85 | -0.4% | 2.0% | no: pairs disagree |

### `test/test.py::parse_page` — C3S1-parse-page-findall (C3.S1)

**regressed** — the repair costs more than the code it replaces: 2.4% lost on 'files', above the 2.3% noise floor, and no case improved. Worse on 1 of 4 cases ('files').
Mean saving across its cases: -2.1%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| many-exec | 59.35 | 61.00 | -2.8% | 3.6% | no: pairs disagree |
| files | 54.98 | 56.30 | -2.4% | 0.8% | yes |
| run-macro | 54.47 | 55.58 | -2.0% | 1.6% | no: within the floor |
| large-few-match | 79.95 | 80.81 | -1.1% | 1.6% | no: pairs disagree |

### `feed-split.py::split_text` — C10S4-split-text-parts (C10.S4)

**negligible** — no case moved more than the noise: the largest reading was +0.9% +-0.9% on 'lists-and-links', against a clean 2.3% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: +0.3%.
Behaviour compared under a relaxed rule: loaded with these uninstalled packages stood in for: tiktoken.
Loaded with uninstalled packages stood in for: tiktoken.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| lists-and-links | 67.37 | 66.78 | +0.9% | 0.9% | no: pairs disagree |
| top-level-tables | 62.60 | 62.40 | +0.3% | 0.6% | no: pairs disagree |
| tables-inside-divs | 61.32 | 61.58 | -0.4% | 1.3% | no: pairs disagree |
| mixed-large | 59.98 | 59.75 | +0.4% | 2.2% | no: pairs disagree |

### `incremental-search/search-suggestions/count_terms.py::process_doc` — C6S1-process-doc-chain (C6.S1)

**negligible** — no case moved more than the noise: the largest reading was +1.5% +-2.3% on 'tl4-huge', against a clean 2.3% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: +0.9%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| tl3-large | 60.19 | 59.49 | +1.2% | 2.5% | no: pairs disagree |
| tl4-huge | 60.61 | 59.72 | +1.5% | 2.4% | no: pairs disagree |
| common-words | 58.93 | 58.68 | +0.4% | 0.8% | no: pairs disagree |
| repetitive | 54.05 | 53.85 | +0.4% | 1.0% | no: pairs disagree |

### `use-case-shopping/create_suggestions.py::filter` — C10S1-filter-any (C10.S1)

**regressed** — the repair costs more than the code it replaces: 68.8% lost on 'hit-late-filter', above the 2.3% noise floor, and no case improved. Worse on 4 of 4 cases ('clean-64-full-scan', 'clean-40-full-scan', 'hit-late-filter', 'numeric-191').
Mean saving across its cases: -68.2%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 10 `nlp = spacy.load("en_core_web_sm")` (OSError); line 79 `with open(sys.argv[1]) as fp:` (IndexError); line 97 `with open(sys.argv[1]) as fp:` (IndexError).
Loaded skipping failing top-level statements: line 10 `nlp = spacy.load("en_core_web_sm")` (OSError); line 79 `with open(sys.argv[1]) as fp:` (IndexError); line 97 `with open(sys.argv[1]) as fp:` (IndexError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| clean-64-full-scan | 42.53 | 67.39 | -58.4% | 3.9% | yes |
| clean-40-full-scan | 41.87 | 70.53 | -68.5% | 7.8% | yes |
| hit-late-filter | 40.96 | 69.16 | -68.8% | 5.2% | yes |
| numeric-191 | 40.32 | 71.45 | -77.2% | 4.6% | yes |

### `feed_to_vespa.py::get_feed_docids` — C6S3-get-feed-docids-setcomp (C6.S3)

**negligible** — no case moved more than the noise: the largest reading was -1.4% +-1.5% on 'term-large', against a clean 2.3% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: -0.7%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| doc-large | 62.62 | 62.51 | +0.2% | 4.8% | no: pairs disagree |
| doc-dups | 56.71 | 57.07 | -0.6% | 1.4% | no: pairs disagree |
| doc-mixed | 55.31 | 55.80 | -0.9% | 4.5% | no: pairs disagree |
| term-large | 55.63 | 56.43 | -1.4% | 1.5% | no: pairs disagree |

### `test/test.py::parse_file` — C10S4-parse-file-parts (C10.S4)

**partial** — saves energy on 2 of 4 inputs ('many-comments', 'many-pis'; best 15.7% +-5.6% on 'many-comments'), and no saving that can be told from noise on the rest: 'plain-large' -0.3% +-1.5% (its pairs disagree too much to tell); 'leading-newline' -0.8% +-0.3% (within the 2.3% noise floor). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +5.6%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| plain-large | 57.73 | 57.91 | -0.3% | 1.5% | no: pairs disagree |
| many-comments | 57.28 | 48.29 | +15.7% | 5.6% | yes |
| many-pis | 54.27 | 50.10 | +7.7% | 2.7% | yes |
| leading-newline | 59.71 | 60.17 | -0.8% | 0.3% | no: within the floor |

### `incremental-search/search-suggestions/count_terms.py::write_json_file` — C10S2-write-json-term-replace (C10.S2)

**partial** — saves energy on 2 of 4 inputs ('double-spaces', 'high-counts'; best 4.7% +-0.6% on 'double-spaces'), and no saving that can be told from noise on the rest: 'single-word-terms' +2.2% +-2.2% (within the 2.3% noise floor); 'many-terms' +1.9% +-4.6% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +3.1%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| single-word-terms | 60.13 | 58.77 | +2.3% | 2.2% | no: within the floor |
| many-terms | 59.59 | 58.46 | +1.9% | 4.6% | no: pairs disagree |
| double-spaces | 62.53 | 59.57 | +4.7% | 0.6% | yes |
| high-counts | 62.12 | 59.85 | +3.7% | 1.5% | yes |

### `incremental-search/search-suggestions/count_terms.py::process_docs` — C1S1-process-docs-dead-total (C1.S1)

**negligible** — no case moved more than the noise: the largest reading was +0.5% +-2.3% on 'bigrams', against a clean 2.3% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: +0.3%.
The agent measured `partial`; re-measured `negligible`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| many-docs | 61.86 | 61.60 | +0.4% | 3.8% | no: pairs disagree |
| bigrams | 60.74 | 60.41 | +0.5% | 2.3% | no: pairs disagree |
| trigrams | 60.13 | 60.14 | -0.0% | 3.2% | no: pairs disagree |
| high-duplicates | 59.46 | 59.25 | +0.4% | 0.1% | no: within the floor |

## Not measured

### `feed_to_vespa.py::find` — C7S3-find-loop (C7.S3)

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures
The agent measured `not_equivalent`; re-measured `over_limit`.

### `test/test.py::parse_page` — C4S4-parse-page-elif (C4.S4)

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures

### `text-search/python/collect_training_data.py::annotate_data` — C8S3-annotate-data-local (C8.S3)

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures

### `use-case-shopping/convert_meta.py::process` — C10S4-convert-meta-categories-text (C10.S4)

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures

### `use-case-shopping/convert_reviews.py::contains_illegal_chars` — C1S3-illegal-chars-single-return (C1.S3)

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures

### `text-search/python/convert-to-vespa-format.py::main` — C10S2-convert-main-dumps (C10.S2)

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures

## Detected, not measured

Accepted findings with no measurement: deferred beyond the repairs chosen for measurement, or blocked.

- `incremental-search/search-suggestions/accepted_words.py::read_common_words` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `news/src/python/mind_data.py::MindData.sample_valid_data` b: deferred — accepted, no repair measured: a different edit of the same lines as submission C4S2-sample-valid-filter-first; outside the 20 measured
- `news/src/python/mind_data.py::MindData.read_data` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `news/src/python/evaluate.py::calc_metrics` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `news/src/python/train_cold_start.py::train_epoch` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `news/src/python/train_cold_start.py::read_bert_embeddings` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `news/src/python/train_cold_start.py::read_bert_embeddings_from_file` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `news/src/python/train_cold_start.py::save_embeddings` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `news/src/python/train_cold_start.py::write_embeddings` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `news/src/python/train_mf.py::train_epoch` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `news/src/python/train_mf.py::save_embeddings` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `news/src/python/create_bert_embeddings.py::create_embeddings` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `news/src/python/create_bert_embeddings.py::create_embeddings` b: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `news/src/python/create_bert_embeddings.py::write_embedding` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `rag-blueprint/eval/train_lightgbm.py::perform_cross_validation` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `rag-blueprint/eval/train_lightgbm.py::perform_cross_validation` b: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `rag-blueprint/eval/train_logistic_regression.py::perform_cross_validation` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `rag-blueprint/eval/train_logistic_regression.py::perform_cross_validation` b: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `feed-split.py::xml_fixup` a: deferred — accepted as C3.S4, but the only exact-equivalent repair I found (skip `replace` when escape(match) == match) is a C1.S2 edit, so none was written; the repeated replace also double-escapes duplicate blocks by design
- `feed-split.py::main` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `feed-split.py::main` c: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `feed_to_vespa.py::update_endpoint` b: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `incremental-search/search-as-you-type/feed_to_vespa.py::update_endpoint` b: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `incremental-search/search-as-you-type/feed_to_vespa.py::vespa_post` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `incremental-search/search-as-you-type/feed_to_vespa.py::vespa_delete` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `examples/in-context-learning/categorize_group.py::inference` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `examples/workshop-ecommerce/preprocess.py::process_users` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `examples/workshop-ecommerce/preprocess.py::process_users` c: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `examples/workshop-ecommerce/preprocess.py::process_products` b: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `examples/workshop-ecommerce/preprocess.py::process_orders` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `examples/workshop-ecommerce/preprocess.py::process_orders` c: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `examples/workshop-ecommerce/preprocess.py::process_orders` d: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `text-search/python/collect_training_data.py::build_dataset` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `text-search/python/collect_training_data.py::load_processed_queries` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `text-search/python/extract-msmarco.py::extract_documents` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `text-search/python/extract-msmarco.py::getcontent` a: deferred — inputs generated, no repair written: the saving is a regex-cache probe per call; outside the 20 measured
- `text-search/python/convert-to-vespa-format.py::main` a: deferred — submission C10S2-convert-main-dumps is in submissions.jsonl but verify.py returned over_limit: 20 repairs already had a verdict
- `text-video-search/src/python/embedding.py::extract_images` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `text-video-search/src/python/embedding.py::VideoFeedDataset.__getitem__` b: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `text-video-search/src/python/app.py::get_predefined_queries` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `test/test.py::exec_file` a: deferred — inputs generated, no repair measured: `os.makedirs(dirname, exist_ok=True)` raises no FileNotFoundError for absolute paths where the original does, so it is not behaviour-preserving as written
- `test/test.py::process_liquid` a: deferred — inputs generated, no repair written: precompiled patterns need module-level state a function-only replacement cannot add; outside the 20 measured
- `test/test.py::parse_page` b: deferred — submission C4S4-parse-page-elif is in submissions.jsonl but verify.py returned over_limit: 20 repairs already had a verdict
- `test/test.py::run_url` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.gen_similarity_maps` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator._prepare_similarity_map_tensor` a: blocked — inputs.py: the unit's module does not load here: AttributeError: SimMapGenerator is not defined here: loading the module skipped line 19 `class SimMapGenerator:` (TypeError), with stand-ins for colpali_engine
- `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator._blend_image` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.should_filter_token` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.get_suggestions` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.get_result_from_query` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `visual-retrieval-colpali/src/main.py::message_generator` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `visual-retrieval-colpali/src/main.py::get_and_store_sim_maps` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `visual-retrieval-colpali/src/main.py::get_and_store_sim_maps` b: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `visual-retrieval-colpali/prepare_feed_deploy.py::download_pdf` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `visual-retrieval-colpali/prepare_feed_deploy.py::float_to_binary_embedding` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `visual-retrieval-colpali/prepare_feed_deploy.py::generate_embeddings` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `visual-retrieval-colpali/refeed_from_hf.py::process_item_for_vespa` b: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `examples/ecommerce-user-preferences/webapp/app.py::get_wikipedia_image` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `examples/ecommerce-user-preferences/webapp/app.py::get_wikipedia_image` b: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `examples/ecommerce-user-preferences/webapp/app.py::get_car_image` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `examples/ecommerce-user-preferences/webapp/app.py::load_system_prompt` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `examples/ecommerce-user-preferences/webapp/app.py::chat` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `examples/google-cloud/cloud-functions/python/main.py::get_blobs` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `examples/google-cloud/cloud-functions/python/main.py::getlogs` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `examples/embedder-auto-training-evaluation/training-evaluation/positives-negatives.py::search` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `examples/embedder-auto-training-evaluation/training-evaluation/evaluate.py::search` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `examples/embedder-auto-training-evaluation/training-evaluation/train.py::TrainDataset.__getitem__` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `examples/embedder-auto-training-evaluation/training-evaluation/train.py::TrainDataset.__init__` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `examples/embedder-auto-training-evaluation/training-evaluation/train.py::TrainDataset.__init__` b: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::subgraph_GenerateKeywords` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::subgraph_EvaluateCategory` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::subgraph_EvaluateFilters` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::EvaluateResults` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/vespa_module/update_vespa.py::fetch_documents` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `examples/book-search/frontend/app.py::feed_catalog` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `examples/mcp-server-app/script/generate_data.py::generate_job` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `examples/mcp-server-app/script/generate_data.py::generate_candidate` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `examples/mcp-server-app/script/generate_data.py::save_vespa_feed` a: deferred — accepted, no repair written: `"\n".join(map(json.dumps, output))` already materialises its argument, so a generator would not remove the list
- `examples/model-exporting/export_hf_model_from_hf.py::export_model` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `examples/model-exporting/export_model_from_hf.py::export_model` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `billion-scale-vector-search/app/src/main/python/recall.py::knn_result_read` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `colbert-long/scripts/convert.py::remove_control_characters` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `colbert-long/scripts/evaluate.py::search` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `use-case-shopping/create_suggestions.py::filter` b: deferred — accepted, no repair written: the dead branch is one comparison after two earlier returns; outside the 20 measured
- `use-case-shopping/create_suggestions.py::filter_content` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `multilingual-search/ext/evaluate.py::search` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `reverse-image-search/script/feed.py::run` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `reverse-image-search/script/feed.py::run` b: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `reverse-image-search/script/search.py::_search` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `commerce-product-ranking/scripts/evaluate.py::main` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `commerce-product-ranking/scripts/evaluate.py::main` c: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `msmarco-ranking/python/evaluate_passage_run.py::eval_query` a: blocked — inputs.py: it cannot run here: `eval_query` calls `get_result`, which performs an HTTP POST to `args.endpoint` via `session.post`; the function's work starts with a network request to a ranking server, which cannot be mocked and is not available here.
- `billion-scale-image-search/app/src/main/python/create-joined-feed.py::nan_handler` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `incremental-search/search-as-you-type/feed_to_vespa.py::find` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `news/src/python/mind_data.py::MindData.lookup_news_index` a: deferred — accepted in step 2; outside the 20 repairs measured, and inputs were not requested for this unit
- `use-case-shopping/convert_meta.py::process` a: blocked — inputs.py: the generated inputs could not be used: refused: this source replaces code, at line 15: `convert_meta.time = _FrozenTime`. Everything measured has to run the real code (the unit reads the clock and random itself). Submission C10S4-convert-meta-categories-text is also over_limit.
- `use-case-shopping/convert_reviews.py::contains_illegal_chars` a: deferred — submission C1S3-illegal-chars-single-return is in submissions.jsonl but verify.py returned over_limit: 20 repairs already had a verdict
- `text-search/python/collect_training_data.py::annotate_data` a: deferred — submission C8S3-annotate-data-local is in submissions.jsonl but verify.py returned over_limit: 20 repairs already had a verdict
