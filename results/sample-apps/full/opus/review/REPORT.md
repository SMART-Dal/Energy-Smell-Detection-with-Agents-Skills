# Energy report — sample-apps @ e2ed22d

141 units listed, 131 with an accepted suspicion · 22 repairs submitted, 148 deferred · 10 confirmed · 5 partial · 1 mixed · 4 negligible · 2 over_limit · 10 applied
Noise floor 1.8% (from: session calibration).

## Applied

### `incremental-search/search-suggestions/count_terms.py::count_terms` — C3S2-count_terms-count_terms-mask (C3.S2)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +44.7%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| trigrams-long | 88.93 | 51.87 | +41.7% | 1.2% | yes |
| fourgrams | 100.80 | 54.40 | +46.0% | 3.0% | yes |
| fivegrams | 114.07 | 54.22 | +52.5% | 1.3% | yes |
| all-unique-trigrams | 92.79 | 57.01 | +38.6% | 0.3% | yes |

### `colbert-long/scripts/convert.py::remove_control_characters` — C8S3-convert-remove_control-local (C8.S3)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +17.8%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 17 `documents = load_dataset('Shitao/MLDR', "corpus-en", spli...` (RuntimeError); line 19 `with open(feed_file, "w") as f:` (NameError).
Measured twice: the first measurement came out `partial` with an input too noisy to read, and this is the second.
Loaded skipping failing top-level statements: line 17 `documents = load_dataset('Shitao/MLDR', "corpus-en", spli...` (RuntimeError); line 19 `with open(feed_file, "w") as f:` (NameError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| ascii-prose | 72.65 | 58.84 | +19.0% | 3.6% | yes |
| unicode-mix | 66.72 | 57.22 | +14.2% | 1.3% | yes |
| long-line | 68.04 | 54.97 | +19.2% | 2.3% | yes |
| log-multiline | 73.20 | 59.43 | +18.8% | 3.5% | yes |

### `news/src/python/evaluate.py::predictions` — C3S4-news_evaluate-predictions-index (C3.S4)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +99.1%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 19 `url, cert = connect()` (FileNotFoundError); line 103 `train_metrics = calc_metrics(train_impressions_file)` (SystemExit); line 104 `valid_metrics = calc_metrics(valid_impressions_file)` (SystemExit); line 106 `print("Train: " + str(train_metrics))` (NameError); line 107 `print("Valid: " + str(valid_metrics))` (NameError).
Loaded skipping failing top-level statements: line 19 `url, cert = connect()` (FileNotFoundError); line 103 `train_metrics = calc_metrics(train_impressions_file)` (SystemExit); line 104 `valid_metrics = calc_metrics(valid_impressions_file)` (SystemExit); line 106 `print("Train: " + str(train_metrics))` (NameError); line 107 `print("Valid: " + str(valid_metrics))` (NameError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| wide-children | 100.18 | 0.76 | +99.2% | 0.2% | yes |
| tail-matches | 102.55 | 0.60 | +99.4% | 0.1% | yes |
| float-relevance | 105.50 | 0.94 | +99.1% | 0.0% | yes |
| many-children | 105.25 | 1.46 | +98.6% | 0.0% | yes |

### `news/src/python/train_cold_start.py::write_embeddings` — C10S3-train_cold_start-write_embeddings-bulk (C10.S3)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +5.7%.
Measured twice: the first measurement came out `partial` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large | 59.16 | 56.85 | +3.9% | 3.0% | yes |
| wide | 59.40 | 57.81 | +2.7% | 2.1% | yes |
| narrow | 61.32 | 56.07 | +8.6% | 4.3% | yes |
| many | 70.34 | 65.08 | +7.5% | 3.2% | yes |

### `news/src/python/create_bert_embeddings.py::write_embedding` — C10S3-create_bert-write_embedding-join (C10.S3)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +41.4%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 15 `data_dir = sys.argv[1]` (IndexError); line 18 `train_news_file = os.path.join(data_dir, "train", "news.t...` (NameError); line 19 `train_embedding_file = os.path.join(data_dir, "train", "n...` (NameError); line 20 `dev_news_file = os.path.join(data_dir, "dev", "news.tsv")` (NameError); line 21 `dev_embedding_file = os.path.join(data_dir, "dev", "news_...` (NameError).
Loaded skipping failing top-level statements: line 15 `data_dir = sys.argv[1]` (IndexError); line 18 `train_news_file = os.path.join(data_dir, "train", "news.t...` (NameError); line 19 `train_embedding_file = os.path.join(data_dir, "train", "n...` (NameError); line 20 `dev_news_file = os.path.join(data_dir, "dev", "news.tsv")` (NameError); line 21 `dev_embedding_file = os.path.join(data_dir, "dev", "news_...` (NameError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| normal-16384 | 91.78 | 52.80 | +42.5% | 7.0% | yes |
| normal-32768 | 92.90 | 54.41 | +41.4% | 3.2% | yes |
| normal-50000 | 81.77 | 48.76 | +40.4% | 0.7% | yes |
| mixed-magnitudes-20000 | 88.24 | 51.86 | +41.2% | 0.8% | yes |

### `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator._prepare_similarity_map_tensor` — C10S3-colpali-prepare_sim_map-bulk-assign (C10.S3)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +92.3%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| typical-4maps-16tokens | 112.82 | 9.47 | +91.6% | 0.1% | yes |
| many-maps-8 | 101.29 | 8.95 | +91.2% | 1.6% | yes |
| dense-two-maps | 112.25 | 8.87 | +92.1% | 0.1% | yes |
| duplicate-addresses | 112.34 | 6.59 | +94.1% | 0.1% | yes |

### `visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.float_to_binary_embedding` — C6S1-vespa_app-float_to_binary-boolmask (C6.S1)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +19.3%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| all-positive-1024 | 64.55 | 52.43 | +18.8% | 1.1% | yes |
| all-negative-1024 | 64.40 | 52.42 | +18.6% | 0.7% | yes |
| zeros-mixed-2048 | 67.67 | 53.37 | +21.1% | 7.1% | yes |
| wide-8192 | 69.18 | 56.22 | +18.7% | 4.4% | yes |

### `text-video-search/src/python/embedding.py::sample_images` — C6S2-embedding-sample_images-select-first (C6.S2)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +72.1%.
Behaviour compared under a relaxed rule: loaded with these uninstalled packages stood in for: clip.
Loaded with uninstalled packages stood in for: clip.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| sample-8-of-80-uint8 | 102.76 | 35.15 | +65.8% | 0.2% | yes |
| sample-30-of-320-mid | 101.63 | 26.56 | +73.9% | 0.2% | yes |
| sample-20-of-200-gray | 101.71 | 32.44 | +68.1% | 1.3% | yes |
| sample-8-of-80-float32 | 105.24 | 20.50 | +80.5% | 0.1% | yes |

### `incremental-search/search-suggestions/accepted_words.py::process_docs` — C10S3-accepted_words-process_docs-update (C10.S3)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +8.2%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large-corpus | 61.09 | 55.57 | +9.0% | 3.8% | yes |
| duplicates | 65.97 | 61.11 | +7.4% | 0.4% | yes |
| skipped-docs | 60.20 | 55.58 | +7.7% | 0.8% | yes |
| mixed-case-digits | 62.98 | 57.40 | +8.9% | 0.7% | yes |

### `feed_to_vespa.py::get_feed_docids` — C3S2-feed_to_vespa-get_feed_docids-hoist (C3.S2)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +8.3%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| doc-large | 62.04 | 57.30 | +7.6% | 2.4% | yes |
| doc-dups | 60.69 | 56.35 | +7.2% | 1.1% | yes |
| doc-mixed | 61.37 | 56.94 | +7.2% | 2.5% | yes |
| term-large | 60.16 | 53.41 | +11.2% | 2.4% | yes |

## Measured, not confirmed

### `incremental-search/search-suggestions/count_terms.py::process_docs` — C3S4-count_terms-process_docs-docfreq (C3.S4)

**partial** — saves energy on 3 of 4 inputs ('many-docs', 'bigrams', 'trigrams'; best 58.8% +-0.8% on 'many-docs'), and no saving that can be told from noise on the rest: 'high-duplicates' +1.7% +-2.0% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +39.1%.
Also the repair for suspicion(s) c of this unit.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| many-docs | 105.81 | 43.63 | +58.8% | 0.8% | yes |
| bigrams | 97.39 | 54.98 | +43.5% | 2.3% | yes |
| trigrams | 103.22 | 48.91 | +52.6% | 1.0% | yes |
| high-duplicates | 58.22 | 57.25 | +1.7% | 2.0% | no: pairs disagree |

### `incremental-search/search-suggestions/count_terms.py::process_docs` — C1S1-count_terms-process_docs-total (C1.S1)

**negligible** — no case moved more than the noise: the largest reading was +2.1% +-2.2% on 'high-duplicates', against a clean 1.8% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: +1.2%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| many-docs | 57.68 | 56.79 | +1.5% | 1.2% | no: within the floor |
| bigrams | 56.51 | 55.88 | +1.1% | 1.0% | no: within the floor |
| trigrams | 55.46 | 55.54 | -0.2% | 3.4% | no: pairs disagree |
| high-duplicates | 56.85 | 55.63 | +2.1% | 2.2% | no: pairs disagree |

### `incremental-search/search-suggestions/count_terms.py::count_terms` — C4S7-count_terms-count_terms-guard (C4.S7)

**partial** — saves energy on 1 of 4 inputs ('all-unique-trigrams'; best 56.1% +-2.1% on 'all-unique-trigrams'), and no saving that can be told from noise on the rest: 'trigrams-long' -1.4% +-2.2% (its pairs disagree too much to tell); 'fourgrams' -0.9% +-2.9% (its pairs disagree too much to tell); 'fivegrams' -3.0% +-3.4% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +12.7%.
The agent measured `mixed`; re-measured `partial`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| trigrams-long | 59.03 | 59.83 | -1.4% | 2.2% | no: pairs disagree |
| fourgrams | 57.13 | 57.64 | -0.9% | 2.9% | no: pairs disagree |
| fivegrams | 56.74 | 58.45 | -3.0% | 3.5% | no: pairs disagree |
| all-unique-trigrams | 113.59 | 49.82 | +56.1% | 2.1% | yes |

### `incremental-search/search-suggestions/count_terms.py::count_terms` — C1S4-count_terms-count_terms-slice (C1.S4)

**partial** — saves energy on 2 of 4 inputs ('trigrams-long', 'all-unique-trigrams'; best 11.5% +-5.9% on 'all-unique-trigrams'), and no saving that can be told from noise on the rest: 'fourgrams' +7.9% +-9.4% (its pairs disagree too much to tell); 'fivegrams' +3.8% +-13.9% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +8.2%.
Measured twice: the first measurement came out `partial` with an input too noisy to read, and this is the second.
The agent measured `confirmed`; re-measured `partial`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| trigrams-long | 61.46 | 55.53 | +9.6% | 6.3% | yes |
| fourgrams | 62.37 | 57.44 | +7.9% | 9.4% | no: pairs disagree |
| fivegrams | 59.00 | 56.73 | +3.8% | 13.9% | no: pairs disagree |
| all-unique-trigrams | 64.22 | 56.81 | +11.5% | 5.9% | yes |

### `incremental-search/search-suggestions/count_terms.py::process_doc` — C1S4-count_terms-process_doc-merge (C1.S4)

**partial** — saves energy on 2 of 4 inputs ('tl3-large', 'tl4-huge'; best 5.2% +-3.7% on 'tl4-huge'), and no saving that can be told from noise on the rest: 'common-words' +0.5% +-2.1% (its pairs disagree too much to tell); 'repetitive' -0.4% +-1.5% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +2.1%.
The agent measured `regressed`; re-measured `partial`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| tl3-large | 58.15 | 56.44 | +2.9% | 0.8% | yes |
| tl4-huge | 58.97 | 55.91 | +5.2% | 3.7% | yes |
| common-words | 56.98 | 56.68 | +0.5% | 2.1% | no: pairs disagree |
| repetitive | 56.43 | 56.65 | -0.4% | 1.5% | no: pairs disagree |

### `feed-split.py::split_text` — C10S4-feed_split-split_text-join (C10.S4)

**negligible** — no case moved more than the noise: the largest reading was +0.5% +-2.0% on 'lists-and-links', against a clean 1.8% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: +0.3%.
Behaviour compared under a relaxed rule: loaded with these uninstalled packages stood in for: tiktoken.
Loaded with uninstalled packages stood in for: tiktoken.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| lists-and-links | 63.73 | 63.38 | +0.5% | 2.0% | no: pairs disagree |
| top-level-tables | 59.56 | 59.24 | +0.5% | 3.3% | no: pairs disagree |
| tables-inside-divs | 57.96 | 57.86 | +0.2% | 0.5% | no: pairs disagree |
| mixed-large | 56.10 | 56.05 | +0.1% | 0.8% | no: pairs disagree |

### `news/src/python/mind_data.py::MindData.sample_valid_data` — C7S4-mind_data-sample_valid_data-filter-first (C7.S4)

**negligible** — no case moved more than the noise: the largest reading was +0.3% +-0.6% on 'train-impressions', against a clean 1.8% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: +0.1%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| typical-valid | 54.28 | 54.21 | +0.1% | 0.2% | no: pairs disagree |
| many-short-partial | 54.99 | 55.03 | -0.1% | 2.0% | no: pairs disagree |
| train-impressions | 55.87 | 55.68 | +0.3% | 0.6% | no: pairs disagree |
| many-short-low-prob | 56.34 | 56.27 | +0.1% | 2.3% | no: pairs disagree |

### `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator._prepare_similarity_map_tensor` — C3S2-colpali-prepare_sim_map-hoist (C3.S2)

**partial** — saves energy on 3 of 4 inputs ('typical-4maps-16tokens', 'dense-two-maps', 'duplicate-addresses'; best 3.2% +-2.8% on 'duplicate-addresses'), and no saving that can be told from noise on the rest: 'many-maps-8' +1.4% +-1.2% (within the 1.8% noise floor). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +2.4%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| typical-4maps-16tokens | 68.36 | 66.40 | +2.9% | 2.1% | yes |
| many-maps-8 | 84.65 | 83.44 | +1.4% | 1.2% | no: within the floor |
| dense-two-maps | 84.74 | 82.96 | +2.1% | 1.9% | yes |
| duplicate-addresses | 84.86 | 82.15 | +3.2% | 2.8% | yes |

### `test/test.py::parse_file` — C4S5-test-parse_file-isinstance (C4.S5)

**mixed** — a trade-off, not a fix: 51.8% saved on 'many-comments' but 7.4% lost on 'leading-newline', both clearing the 1.8% noise floor. Whether it pays depends on which input the code actually sees, so the report must name both.
Mean saving across its cases: +22.0%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| plain-large | 53.13 | 57.48 | -8.2% | 4.2% | yes |
| many-comments | 94.13 | 45.38 | +51.8% | 0.1% | yes |
| many-pis | 93.56 | 45.11 | +51.8% | 1.1% | yes |
| leading-newline | 52.72 | 56.61 | -7.4% | 0.3% | yes |

### `news/src/python/mind_data.py::MindData.sample_valid_data` — C1S4-mind_data-sample_valid_data-sum (C1.S4)

**negligible** — no case moved more than the noise: the largest reading was +1.3% +-3.6% on 'many-short-partial', against a clean 1.8% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: +0.7%.
Measured twice: the first measurement came out `negligible` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| typical-valid | 56.39 | 55.89 | +0.9% | 2.2% | no: pairs disagree |
| many-short-partial | 62.40 | 61.60 | +1.3% | 3.6% | no: pairs disagree |
| train-impressions | 57.99 | 57.75 | +0.4% | 0.6% | no: pairs disagree |
| many-short-low-prob | 58.53 | 58.48 | +0.1% | 1.0% | no: pairs disagree |

## Not measured

### `colbert-long/scripts/convert.py::remove_control_characters` — C10S1-convert-remove_control-translate (C10.S1)

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures
The agent measured `not_equivalent`; re-measured `over_limit`.

### `visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.format_q_embs` — C10S3-vespa_app-format_q_embs-bulk (C10.S3)

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures
The agent measured `not_equivalent`; re-measured `over_limit`.

## Detected, not measured

Accepted findings with no measurement: deferred beyond the repairs chosen for measurement, or blocked.

- `incremental-search/search-suggestions/count_terms.py::count_terms` d: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `incremental-search/search-suggestions/count_terms.py::write_json_file` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `incremental-search/search-suggestions/count_terms.py::read_common_words` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `incremental-search/search-suggestions/accepted_words.py::process_docs` b: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `incremental-search/search-suggestions/accepted_words.py::write_to_file` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `incremental-search/search-suggestions/accepted_words.py::read_common_words` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `feed-split.py::what_language` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `feed-split.py::move_linkable_item_to_single_entity` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `feed-split.py::main` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `feed-split.py::main` b: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `news/src/python/mind_data.py::MindData.read_news` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `news/src/python/mind_data.py::MindData.read_news` b: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `news/src/python/mind_data.py::MindData.add_impressions` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `news/src/python/mind_data.py::MindData.lookup_index` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `news/src/python/evaluate.py::calc_metrics` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `news/src/python/evaluate.py::calc_impression` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `news/src/python/train_mf.py::write_embeddings` a: deferred — verify.py over_limit: 20 repairs already had a verdict, so this repair was not measured
- `news/src/python/train_cold_start.py::save_embeddings` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `news/src/python/train_cold_start.py::save_embeddings` b: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `news/src/python/train_cold_start.py::train_model` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `news/src/python/train_cold_start.py::read_bert_embeddings_from_file` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `news/src/python/train_mf.py::main` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `news/src/python/train_mf.py::save_embeddings` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `news/src/python/create_bert_embeddings.py::create_embeddings` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `news/src/python/create_bert_embeddings.py::create_embeddings` b: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `news/src/python/create_bert_embeddings.py::create_embeddings` c: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `news/src/python/create_bert_embeddings.py::create_embeddings` d: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `news/src/python/convert_embeddings_to_vespa_format.py::convert_user_embeddings` a: deferred — verify.py over_limit: 20 repairs already had a verdict, so this repair was not measured
- `news/src/python/convert_embeddings_to_vespa_format.py::convert_news_embeddings` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `news/src/python/create_category_ctrs.py::write_news_category_ctr_update` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `news/src/python/convert_to_vespa_format.py::convert_file` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `news/src/python/metrics.py::dcg_score` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `news/src/python/vespa_client.py::query_news` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `news/src/python/vespa_client.py::query_news` b: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `news/src/python/vespa_client.py::query_user_embedding` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `news/src/python/vespa_client.py::query_user_embedding` b: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.should_filter_token` a: deferred — verify.py over_limit: 20 repairs already had a verdict, so this repair was not measured
- `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.gen_similarity_maps` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.gen_similarity_maps` b: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.format_query_results` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.get_result_from_query` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.query_vespa_colpali` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `visual-retrieval-colpali/src/main.py::message_generator` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `visual-retrieval-colpali/src/main.py::message_generator` b: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `visual-retrieval-colpali/src/main.py::get` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `visual-retrieval-colpali/src/main.py::get_and_store_sim_maps` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `visual-retrieval-colpali/src/frontend/app.py::SearchResult` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `visual-retrieval-colpali/src/backend/cache.py::LRUCache.get` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `visual-retrieval-colpali/prepare_feed_deploy.py::float_to_binary_embedding` a: deferred — verify.py over_limit: 20 repairs already had a verdict, so this repair was not measured
- `visual-retrieval-colpali/prepare_feed_deploy.py::download_pdf` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `visual-retrieval-colpali/prepare_feed_deploy.py::generate_embeddings` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `visual-retrieval-colpali/refeed_from_hf.py::process_item_for_vespa` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `visual-retrieval-colpali/refeed_from_hf.py::pil_to_base64` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `text-video-search/src/python/embedding.py::extract_images` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `text-video-search/src/python/embedding.py::VideoFeedDataset.__getitem__` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `text-video-search/src/python/embedding.py::VideoFeedDataset.__getitem__` b: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `text-video-search/src/python/embedding.py::VideoFeedDataset.__getitem__` c: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `text-video-search/src/python/app.py::get_predefined_queries` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `use-case-shopping/create_suggestions.py::filter` a: deferred — verify.py over_limit: 20 repairs already had a verdict, so this repair was not measured
- `use-case-shopping/create_suggestions.py::filter_content` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `use-case-shopping/convert_meta.py::process` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `use-case-shopping/convert_meta.py::process` b: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `use-case-shopping/convert_meta.py::process` c: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `use-case-shopping/convert_meta.py::main` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `use-case-shopping/convert_reviews.py::main` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `examples/in-context-learning/categorize_group.py::inference` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `examples/in-context-learning/categorize_group.py::get_label` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `examples/embedder-auto-training-evaluation/training-evaluation/train.py::TrainDataset.__getitem__` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `examples/embedder-auto-training-evaluation/training-evaluation/train.py::TrainDataset.__init__` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `examples/embedder-auto-training-evaluation/training-evaluation/train.py::TrainDataset.__init__` b: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `examples/ecommerce-user-preferences/webapp/app.py::query_vespa` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `examples/ecommerce-user-preferences/webapp/app.py::query_vespa_facets` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `examples/ecommerce-user-preferences/webapp/app.py::chat` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `examples/ecommerce-user-preferences/webapp/app.py::chat` b: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `examples/ecommerce-user-preferences/webapp/app.py::get_car_image` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `examples/ecommerce-user-preferences/webapp/app.py::get_wikipedia_image` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `examples/ecommerce-user-preferences/webapp/app.py::get_wikipedia_image` b: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `examples/ecommerce-user-preferences/webapp/app.py::load_system_prompt` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `examples/google-cloud/cloud-functions/python/main.py::getlogs` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `examples/google-cloud/cloud-functions/python/main.py::listfiles` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `examples/google-cloud/cloud-functions/python/main.py::get_blobs` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `examples/embedder-auto-training-evaluation/training-evaluation/positives-negatives.py::search` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `examples/embedder-auto-training-evaluation/training-evaluation/evaluate.py::search` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `examples/mcp-server-app/script/generate_data.py::generate_job` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `examples/workshop-ecommerce/preprocess.py::process_users` a: deferred — verify.py over_limit: 20 repairs already had a verdict, so this repair was not measured
- `examples/workshop-ecommerce/preprocess.py::process_users` b: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `examples/workshop-ecommerce/preprocess.py::process_products` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `examples/workshop-ecommerce/preprocess.py::process_products` b: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `examples/workshop-ecommerce/preprocess.py::process_orders` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `examples/workshop-ecommerce/preprocess.py::process_orders` b: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `examples/workshop-ecommerce/preprocess.py::process_orders` c: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `feed_to_vespa.py::get_feed_docids` b: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `feed_to_vespa.py::find` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `incremental-search/search-as-you-type/feed_to_vespa.py::get_feed_docids` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `feed_to_vespa.py::update_endpoint` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `incremental-search/search-as-you-type/feed_to_vespa.py::vespa_feed` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `incremental-search/search-as-you-type/feed_to_vespa.py::get_docs` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `incremental-search/search-as-you-type/feed_to_vespa.py::call` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `msmarco-ranking/python/evaluate_passage_run.py::main` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `msmarco-ranking/python/evaluate_passage_run.py::get_result` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `multilingual-search/ext/evaluate.py::search` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `hypencoder/encode_query.py::main` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `billion-scale-vector-search/app/src/main/python/recall.py::main` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `billion-scale-vector-search/app/src/main/python/recall.py::knn_result_read` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `billion-scale-vector-search/app/src/main/python/recall.py::read_queries` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `billion-scale-vector-search/app/src/main/python/recall.py::compute_recall_with_distance_ties` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `colbert-long/scripts/evaluate.py::search` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `commerce-product-ranking/scripts/evaluate.py::main` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `commerce-product-ranking/scripts/evaluate.py::main` b: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::subgraph_GenerateKeywords` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::subgraph_EvaluateCategory` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::subgraph_EvaluateFilters` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::EvaluateResults` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/vespa_module/vespa_retriever.py::VespaRetriever` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/vespa_module/vespa_retriever.py::create_conditions` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/utils/helpers.py::get_latest_ai_or_human_message` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/vespa_module/update_vespa.py::fetch_documents` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/vespa_module/update_vespa.py::update_document_quantity` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `examples/agentic-streamlit-chatbot/simple_app/streamlit_vespa_app.py::VespaRetriever` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `examples/book-search/frontend/app.py::feed_catalog` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `text-search/python/collect_training_data.py::build_dataset` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `text-search/python/collect_training_data.py::annotate_data` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `text-search/python/collect_training_data.py::load_processed_queries` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `text-search/python/sample-queries-and-documents.py::select_documents` a: deferred — verify.py over_limit: 20 repairs already had a verdict, so this repair was not measured
- `text-search/python/sample-queries-and-documents.py::select_documents` c: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `text-search/python/extract-msmarco.py::getcontent` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `text-search/python/extract-msmarco.py::load_msmarco_queries` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `text-search/python/sample-queries-and-documents.py::load_queries` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `text-search/python/convert-to-vespa-format.py::main` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `rag-blueprint/eval/train_lightgbm.py::perform_cross_validation` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `rag-blueprint/eval/train_lightgbm.py::perform_cross_validation` c: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `rag-blueprint/eval/train_lightgbm.py::perform_cross_validation` d: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `rag-blueprint/eval/train_lightgbm.py::strip_feature_prefix` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `rag-blueprint/eval/train_logistic_regression.py::perform_cross_validation` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `rag-blueprint/eval/train_logistic_regression.py::perform_cross_validation` b: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `test/test.py::parse_file` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `test/test.py::exec_file` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `test/test.py::run_url` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `test/test.py::process_liquid` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `test/test.py::parse_page` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `test/test.py::parse_page` b: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `test/pseudo_terminal.py::Log.write` a: deferred — verify.py over_limit: 20 repairs already had a verdict, so this repair was not measured
- `reverse-image-search/script/feed.py::run` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `reverse-image-search/script/feed.py::run` b: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `reverse-image-search/script/feed.py::run` c: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `reverse-image-search/script/search.py::_search` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `scripts/print-app-endpoints.py::main` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
- `visual-retrieval-colpali/tests/huggingface_smoke.py::main` a: deferred — accepted but not measured: outside the 20 repairs chosen for measurement (lower expected saving, or the unit needs network, a model, a GPU or a running Vespa)
