# Energy report — sample-apps @ e2ed22d

98 units listed, 81 with an accepted suspicion · 22 repairs submitted, 73 deferred · 13 confirmed · 4 partial · 1 regressed · 2 negligible · 2 over_limit · 13 applied
Noise floor 1.5% (from: session calibration).

## Applied

### `colbert-long/scripts/convert.py::remove_control_characters` — C10S1-control-translate (C10.S1)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +92.8%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 17 `documents = load_dataset('Shitao/MLDR', "corpus-en", spli...` (RuntimeError); line 19 `with open(feed_file, "w") as f:` (NameError).
Loaded skipping failing top-level statements: line 17 `documents = load_dataset('Shitao/MLDR', "corpus-en", spli...` (RuntimeError); line 19 `with open(feed_file, "w") as f:` (NameError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| ascii-prose | 106.32 | 0.73 | +99.3% | 0.0% | yes |
| unicode-mix | 103.17 | 27.31 | +73.5% | 1.1% | yes |
| long-line | 104.83 | 0.72 | +99.3% | 0.1% | yes |
| log-multiline | 100.15 | 0.87 | +99.1% | 0.1% | yes |

### `incremental-search/search-suggestions/count_terms.py::process_docs` — C3S4-process-docs-docs (C3.S4)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +38.5%.
The agent measured `partial`; re-measured `confirmed`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| many-docs | 108.39 | 46.01 | +57.6% | 0.4% | yes |
| bigrams | 99.28 | 56.92 | +42.7% | 0.5% | yes |
| trigrams | 109.90 | 52.74 | +52.0% | 0.6% | yes |
| high-duplicates | 61.43 | 60.23 | +1.9% | 1.2% | yes |

### `incremental-search/search-suggestions/count_terms.py::count_terms` — C10S1-count-isdisjoint (C10.S1)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +40.3%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| trigrams-long | 90.72 | 57.47 | +36.7% | 0.7% | yes |
| fourgrams | 94.18 | 54.59 | +42.0% | 0.7% | yes |
| fivegrams | 109.52 | 58.15 | +46.9% | 1.1% | yes |
| all-unique-trigrams | 87.19 | 56.30 | +35.4% | 0.8% | yes |

### `incremental-search/search-suggestions/count_terms.py::write_json_file` — C9S1-write-once (C9.S1)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +11.4%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| single-word-terms | 72.38 | 66.68 | +7.9% | 2.7% | yes |
| many-terms | 75.72 | 68.11 | +10.0% | 5.9% | yes |
| double-spaces | 72.73 | 61.37 | +15.6% | 2.1% | yes |
| high-counts | 71.52 | 62.96 | +12.0% | 1.7% | yes |

### `incremental-search/search-suggestions/accepted_words.py::process_docs` — C10S3-accepted-update (C10.S3)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +7.8%.
Measured twice: the first measurement came out `partial` with an input too noisy to read, and this is the second.
The agent measured `partial`; re-measured `confirmed`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large-corpus | 66.93 | 60.37 | +9.8% | 9.5% | yes |
| duplicates | 62.57 | 58.23 | +6.9% | 1.5% | yes |
| skipped-docs | 66.26 | 61.64 | +7.0% | 0.8% | yes |
| mixed-case-digits | 66.48 | 61.37 | +7.7% | 0.6% | yes |

### `text-video-search/src/python/embedding.py::sample_images` — C6S2-sample-index (C6.S2)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +71.6%.
Behaviour compared under a relaxed rule: loaded with these uninstalled packages stood in for: clip.
Loaded with uninstalled packages stood in for: clip.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| sample-8-of-80-uint8 | 107.33 | 37.87 | +64.7% | 2.2% | yes |
| sample-30-of-320-mid | 108.29 | 28.58 | +73.6% | 0.0% | yes |
| sample-20-of-200-gray | 107.13 | 34.49 | +67.8% | 0.2% | yes |
| sample-8-of-80-float32 | 108.26 | 21.38 | +80.2% | 0.1% | yes |

### `news/src/python/evaluate.py::predictions` — C5S2-predictions-index (C5.S2)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +99.1%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 19 `url, cert = connect()` (FileNotFoundError); line 103 `train_metrics = calc_metrics(train_impressions_file)` (SystemExit); line 104 `valid_metrics = calc_metrics(valid_impressions_file)` (SystemExit); line 106 `print("Train: " + str(train_metrics))` (NameError); line 107 `print("Valid: " + str(valid_metrics))` (NameError).
Loaded skipping failing top-level statements: line 19 `url, cert = connect()` (FileNotFoundError); line 103 `train_metrics = calc_metrics(train_impressions_file)` (SystemExit); line 104 `valid_metrics = calc_metrics(valid_impressions_file)` (SystemExit); line 106 `print("Train: " + str(train_metrics))` (NameError); line 107 `print("Valid: " + str(valid_metrics))` (NameError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| wide-children | 113.78 | 0.78 | +99.3% | 0.0% | yes |
| tail-matches | 116.86 | 0.63 | +99.5% | 0.1% | yes |
| float-relevance | 112.93 | 1.00 | +99.1% | 0.1% | yes |
| many-children | 115.08 | 1.53 | +98.7% | 0.0% | yes |

### `news/src/python/create_bert_embeddings.py::write_embedding` — C9S1-embedding-join (C9.S1)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +35.2%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 15 `data_dir = sys.argv[1]` (IndexError); line 18 `train_news_file = os.path.join(data_dir, "train", "news.t...` (NameError); line 19 `train_embedding_file = os.path.join(data_dir, "train", "n...` (NameError); line 20 `dev_news_file = os.path.join(data_dir, "dev", "news.tsv")` (NameError); line 21 `dev_embedding_file = os.path.join(data_dir, "dev", "news_...` (NameError).
Loaded skipping failing top-level statements: line 15 `data_dir = sys.argv[1]` (IndexError); line 18 `train_news_file = os.path.join(data_dir, "train", "news.t...` (NameError); line 19 `train_embedding_file = os.path.join(data_dir, "train", "n...` (NameError); line 20 `dev_news_file = os.path.join(data_dir, "dev", "news.tsv")` (NameError); line 21 `dev_embedding_file = os.path.join(data_dir, "dev", "news_...` (NameError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| normal-16384 | 89.89 | 57.56 | +36.0% | 1.6% | yes |
| normal-32768 | 89.87 | 57.72 | +35.8% | 1.9% | yes |
| normal-50000 | 82.44 | 54.76 | +33.6% | 1.1% | yes |
| mixed-magnitudes-20000 | 88.98 | 57.57 | +35.3% | 1.1% | yes |

### `visual-retrieval-colpali/prepare_feed_deploy.py::float_to_binary_embedding` — C10S1-binary-vectorise (C10.S1)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +61.1%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 65 `from colpali_engine.models import ColPali, ColPaliProcessor` (ImportError); line 129 `VESPA_CLOUD_SECRET_TOKEN = os.getenv("VESPA_CLOUD_SECRET_...` (EOFError); line 138 `GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or input(` (EOFError); line 146 `gemini_client = genai.Client(api_key=GEMINI_API_KEY)` (NameError); line 150 `device = get_torch_device("auto")` (TypeError); line 151 `print(f"Using device: {device}")` (NameError); line 154 `model = ColPali.from_pretrained(` (NameError); line 160 `processor = ColPaliProcessor.from_pretrained(MODEL_NAME)` (NameError); line 360 `print(f"Max text length: {np.max(text_lengths)}")` (ValueError); line 361 `print(f"Min text length: {np.min(text_lengths)}")` (ValueError); line 461 `pdf_pages[46]["image"]` (IndexError); line 463 `pdf_pages[46]["queries"]` (IndexError); line 574 `embeddings = generate_embeddings(images, model, processor)` (NameError); line 576 `embeddings.shape` (NameError); line 596 `for pdf, embedding in zip(pdf_pages, embeddings):` (NameError); line 972 `VESPA_TEAM_API_KEY = os.getenv("VESPA_TEAM_API_KEY") or i...` (EOFError); line 977 `vespa_cloud = VespaCloud(` (NameError); line 985 `vespa_cloud.deploy()` (NameError); line 988 `endpoint_url = vespa_cloud.get_token_endpoint()` (NameError); line 989 `print(f"Application deployed. Token endpoint URL: {endpoi...` (NameError); line 1000 `app = Vespa(url=endpoint_url, vespa_cloud_secret_token=VE...` (NameError); line 1001 `app.get_application_status()` (NameError); line 1013 `app.feed_async_iterable(vespa_feed, schema=VESPA_SCHEMA_N...` (NameError).
Loaded skipping failing top-level statements: line 65 `from colpali_engine.models import ColPali, ColPaliProcessor` (ImportError); line 129 `VESPA_CLOUD_SECRET_TOKEN = os.getenv("VESPA_CLOUD_SECRET_...` (EOFError); line 138 `GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or input(` (EOFError); line 146 `gemini_client = genai.Client(api_key=GEMINI_API_KEY)` (NameError); line 150 `device = get_torch_device("auto")` (TypeError); line 151 `print(f"Using device: {device}")` (NameError); line 154 `model = ColPali.from_pretrained(` (NameError); line 160 `processor = ColPaliProcessor.from_pretrained(MODEL_NAME)` (NameError); line 360 `print(f"Max text length: {np.max(text_lengths)}")` (ValueError); line 361 `print(f"Min text length: {np.min(text_lengths)}")` (ValueError); line 461 `pdf_pages[46]["image"]` (IndexError); line 463 `pdf_pages[46]["queries"]` (IndexError); line 574 `embeddings = generate_embeddings(images, model, processor)` (NameError); line 576 `embeddings.shape` (NameError); line 596 `for pdf, embedding in zip(pdf_pages, embeddings):` (NameError); line 972 `VESPA_TEAM_API_KEY = os.getenv("VESPA_TEAM_API_KEY") or i...` (EOFError); line 977 `vespa_cloud = VespaCloud(` (NameError); line 985 `vespa_cloud.deploy()` (NameError); line 988 `endpoint_url = vespa_cloud.get_token_endpoint()` (NameError); line 989 `print(f"Application deployed. Token endpoint URL: {endpoi...` (NameError); line 1000 `app = Vespa(url=endpoint_url, vespa_cloud_secret_token=VE...` (NameError); line 1001 `app.get_application_status()` (NameError); line 1013 `app.feed_async_iterable(vespa_feed, schema=VESPA_SCHEMA_N...` (NameError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| colpali-large-2048x128 | 104.86 | 34.05 | +67.5% | 0.4% | yes |
| dim-64-3000-patches | 105.98 | 22.78 | +78.5% | 0.3% | yes |
| dim-1024-900-patches | 84.42 | 57.53 | +31.9% | 1.0% | yes |
| many-patches-4096x128 | 106.74 | 35.80 | +66.5% | 0.3% | yes |

### `use-case-shopping/create_suggestions.py::filter_content` — C10S3-filter-tuple (C10.S3)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +56.9%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 10 `nlp = spacy.load("en_core_web_sm")` (OSError); line 79 `with open(sys.argv[1]) as fp:` (IndexError); line 97 `with open(sys.argv[1]) as fp:` (IndexError).
Loaded skipping failing top-level statements: line 10 `nlp = spacy.load("en_core_web_sm")` (OSError); line 79 `with open(sys.argv[1]) as fp:` (IndexError); line 97 `with open(sys.argv[1]) as fp:` (IndexError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| no-match-short | 61.68 | 26.58 | +56.9% | 2.8% | yes |
| no-match-long | 79.26 | 34.59 | +56.4% | 3.0% | yes |
| near-miss-another | 81.43 | 35.05 | +57.0% | 3.1% | yes |
| only-long-match | 77.38 | 32.98 | +57.4% | 0.1% | yes |

### `feed-split.py::what_language` — C1S4-what-language (C1.S4)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +15.1%.
Behaviour compared under a relaxed rule: loaded with these uninstalled packages stood in for: tiktoken.
Loaded with uninstalled packages stood in for: tiktoken.
The agent measured `partial`; re-measured `confirmed`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| java-near-end | 62.24 | 55.74 | +10.4% | 0.5% | yes |
| no-markers | 61.87 | 55.51 | +10.3% | 0.3% | yes |
| curl-at-index-zero-large | 67.80 | 55.81 | +17.7% | 0.5% | yes |
| highlight-not-at-start | 71.80 | 55.98 | +22.0% | 0.3% | yes |

### `news/src/python/mind_data.py::MindData.add_impressions` — C1S4-impression-lookup (C1.S4)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +6.7%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large-positives | 65.28 | 60.45 | +7.4% | 1.6% | yes |
| many-positives-few-negatives | 61.75 | 58.83 | +4.7% | 1.6% | yes |
| heavy-sampling | 66.19 | 61.64 | +6.9% | 0.6% | yes |
| medium | 64.98 | 59.95 | +7.7% | 0.3% | yes |

### `examples/workshop-ecommerce/preprocess.py::process_users` — C3S1-users-records (C3.S1)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +43.5%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| full-150-users | 98.35 | 50.40 | +48.8% | 0.0% | yes |
| limit-200 | 63.89 | 60.52 | +5.3% | 2.4% | yes |
| few-users-heavy | 86.29 | 9.61 | +88.9% | 0.6% | yes |
| many-duplicates | 83.32 | 57.48 | +31.0% | 0.6% | yes |

## Measured, not confirmed

### `feed-split.py::split_text` — C10S4-split-text (C10.S4)

**negligible** — no case moved more than the noise: the largest reading was -0.3% +-1.9% on 'mixed-large', against a clean 1.5% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: -0.0%.
Behaviour compared under a relaxed rule: loaded with these uninstalled packages stood in for: tiktoken.
Loaded with uninstalled packages stood in for: tiktoken.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| lists-and-links | 62.54 | 62.42 | +0.2% | 1.9% | no: pairs disagree |
| top-level-tables | 58.39 | 58.41 | -0.0% | 1.0% | no: pairs disagree |
| tables-inside-divs | 57.36 | 57.34 | +0.0% | 0.6% | no: pairs disagree |
| mixed-large | 55.86 | 56.00 | -0.3% | 1.9% | no: pairs disagree |

### `incremental-search/search-suggestions/count_terms.py::write_json_file` — C10S2-write-replace (C10.S2)

**partial** — saves energy on 3 of 4 inputs ('many-terms', 'double-spaces', 'high-counts'; best 4.4% +-2.4% on 'double-spaces'), and no saving that can be told from noise on the rest: 'single-word-terms' +1.8% +-5.1% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +3.5%.
Measured twice: the first measurement came out `partial` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| single-word-terms | 59.85 | 58.77 | +1.8% | 5.1% | no: pairs disagree |
| many-terms | 75.28 | 72.61 | +3.5% | 3.0% | yes |
| double-spaces | 62.67 | 59.88 | +4.5% | 2.4% | yes |
| high-counts | 62.44 | 59.83 | +4.2% | 2.0% | yes |

### `text-search/python/sample-queries-and-documents.py::select_documents` — C10S3-select-update (C10.S3)

**partial** — saves energy on 2 of 4 inputs ('many-qids', 'already-complete'; best 37.2% +-0.2% on 'already-complete'), and no saving that can be told from noise on the rest: 'query-duplicates' +2.9% +-27.6% (its pairs disagree too much to tell); 'large-offsets' +1.9% +-3.0% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does. Behaviour was compared under a relaxed rule, which the report must repeat: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 12 `data_dir = sys.argv[1]` (IndexError); line 16 `query_file = os.path.join(data_dir, "queries.tsv")` (NameError); line 17 `docs_file = os.path.join(data_dir, "docs.tsv")` (NameError); line 18 `offset_file = os.path.join(data_dir, "docs-offset.tsv")` (NameError); line 20 `sample_query_file = os.path.join(data_dir, "test-queries....` (NameError); line 21 `sample_offset_file = os.path.join(data_dir, "test-docs-of...` (NameError).
Mean saving across its cases: +17.4%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 12 `data_dir = sys.argv[1]` (IndexError); line 16 `query_file = os.path.join(data_dir, "queries.tsv")` (NameError); line 17 `docs_file = os.path.join(data_dir, "docs.tsv")` (NameError); line 18 `offset_file = os.path.join(data_dir, "docs-offset.tsv")` (NameError); line 20 `sample_query_file = os.path.join(data_dir, "test-queries....` (NameError); line 21 `sample_offset_file = os.path.join(data_dir, "test-docs-of...` (NameError).
Measured twice: the first measurement came out `partial` with an input too noisy to read, and this is the second.
Loaded skipping failing top-level statements: line 12 `data_dir = sys.argv[1]` (IndexError); line 16 `query_file = os.path.join(data_dir, "queries.tsv")` (NameError); line 17 `docs_file = os.path.join(data_dir, "docs.tsv")` (NameError); line 18 `offset_file = os.path.join(data_dir, "docs-offset.tsv")` (NameError); line 20 `sample_query_file = os.path.join(data_dir, "test-queries....` (NameError); line 21 `sample_offset_file = os.path.join(data_dir, "test-docs-of...` (NameError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| query-duplicates | 77.00 | 74.57 | +3.2% | 27.6% | no: pairs disagree |
| many-qids | 79.34 | 57.65 | +27.3% | 1.3% | yes |
| large-offsets | 59.01 | 57.91 | +1.9% | 3.0% | no: pairs disagree |
| already-complete | 93.31 | 58.56 | +37.2% | 0.2% | yes |

### `text-search/python/extract-msmarco.py::extract_documents` — C9S1-extract-offset (C9.S1)

**partial** — saves energy on 2 of 4 inputs ('unicode-1500', 'mixed-3000'; best 6.0% +-2.6% on 'unicode-1500'), and no saving that can be told from noise on the rest: 'long-800' +0.1% +-1.2% (its pairs disagree too much to tell); 'long-1200' +0.8% +-3.9% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +2.5%.
Measured twice: the first measurement came out `partial` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| unicode-1500 | 65.63 | 61.67 | +6.0% | 2.6% | yes |
| long-800 | 64.08 | 64.03 | +0.1% | 1.2% | no: pairs disagree |
| mixed-3000 | 63.84 | 61.78 | +3.2% | 0.9% | yes |
| long-1200 | 64.32 | 63.80 | +0.8% | 3.9% | no: pairs disagree |

### `examples/embedder-auto-training-evaluation/training-evaluation/train.py::TrainDataset.__init__` — C6S3-init-iterate (C6.S3)

**regressed** — the repair costs more than the code it replaces: 7.0% lost on 'string_ids', above the 1.5% noise floor, and no case improved. Worse on 4 of 4 cases ('docs_heavy', 'queries_heavy', 'sparse_fields', 'string_ids').
Mean saving across its cases: -5.9%.
Behaviour compared under a relaxed rule: loaded with these uninstalled packages stood in for: sentence_transformers.
Loaded with uninstalled packages stood in for: sentence_transformers.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| docs_heavy | 62.50 | 65.46 | -4.7% | 1.6% | yes |
| queries_heavy | 64.76 | 68.41 | -5.6% | 2.7% | yes |
| sparse_fields | 59.82 | 63.49 | -6.1% | 0.8% | yes |
| string_ids | 62.14 | 66.49 | -7.0% | 4.4% | yes |

### `news/src/python/train_cold_start.py::read_bert_embeddings` — C5S3-bert-float32 (C5.S3)

**partial** — saves energy on 2 of 4 inputs ('c6_longlines', 'c8_sparse'; best 2.5% +-1.8% on 'c6_longlines'), and no saving that can be told from noise on the rest: 'c5_large' +2.9% +-4.5% (its pairs disagree too much to tell); 'c7_partial' +2.7% +-4.2% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +2.5%.
Measured twice: the first measurement came out `partial` with an input too noisy to read, and this is the second.
The agent measured `negligible`; re-measured `partial`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| c5_large | 60.96 | 59.17 | +2.9% | 4.5% | no: pairs disagree |
| c6_longlines | 57.60 | 56.15 | +2.5% | 1.8% | yes |
| c7_partial | 58.88 | 57.28 | +2.7% | 4.2% | no: pairs disagree |
| c8_sparse | 61.88 | 60.85 | +1.7% | 0.5% | yes |

### `incremental-search/search-suggestions/count_terms.py::process_docs` — C1S1-dead-total (C1.S1)

**negligible** — no case moved more than the noise: the largest reading was +1.3% +-0.4% on 'trigrams', against a clean 1.5% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: +0.9%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| many-docs | 60.97 | 60.64 | +0.5% | 0.9% | no: pairs disagree |
| bigrams | 60.30 | 59.78 | +0.9% | 0.6% | no: within the floor |
| trigrams | 59.24 | 58.45 | +1.3% | 0.4% | no: within the floor |
| high-duplicates | 58.31 | 57.78 | +0.9% | 1.7% | no: pairs disagree |

## Not measured

### `rag-blueprint/eval/train_logistic_regression.py::perform_cross_validation` — C1S5-describe-stats (C1.S5)

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures
The agent measured `not_equivalent`; re-measured `over_limit`.

### `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.should_filter_token` — C8S2-filter-compiled (C8.S2)

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures
The agent measured `no_inputs`; re-measured `over_limit`.

## Detected, not measured

Accepted findings with no measurement: deferred beyond the repairs chosen for measurement, or blocked.

- `use-case-shopping/create_suggestions.py::filter` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `incremental-search/search-as-you-type/feed_to_vespa.py::vespa_feed` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `incremental-search/search-as-you-type/feed_to_vespa.py::vespa_remove` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `incremental-search/search-as-you-type/feed_to_vespa.py::update_endpoint` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `incremental-search/search-as-you-type/feed_to_vespa.py::get_docs` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `feed_to_vespa.py::vespa_remove` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `feed_to_vespa.py::update_endpoint` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `text-search/python/collect_training_data.py::build_dataset` a: blocked — inputs.py: it cannot run here: `build_dataset` calls `get_features`, which performs `requests.post(url, json=body)` against a Vespa server; every measured call would need network access to a live search endpoint, which is unavailable here.
- `text-search/python/collect_training_data.py::build_dataset` b: blocked — inputs.py: it cannot run here: `build_dataset` calls `get_features`, which performs `requests.post(url, json=body)` against a Vespa server; every measured call would need network access to a live search endpoint, which is unavailable here.
- `text-search/python/extract-msmarco.py::load_msmarco_queries` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `text-search/python/sample-queries-and-documents.py::select_documents` b: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `text-video-search/src/python/embedding.py::extract_images` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `text-video-search/src/python/embedding.py::extract_images` b: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `text-video-search/src/python/embedding.py::VideoFeedDataset.__getitem__` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `text-video-search/src/python/embedding.py::VideoFeedDataset.__getitem__` b: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `text-video-search/src/python/embedding.py::search_video_file_names` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `multilingual-search/ext/evaluate.py::search` a: blocked — inputs.py: it cannot run here: `search` performs an HTTP POST to `args.endpoint` via `requests.Session`, requiring a live Vespa endpoint; no input can avoid the network request.
- `news/src/python/evaluate.py::read_impressions_file` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `news/src/python/evaluate.py::calc_impression` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `news/src/python/create_bert_embeddings.py::create_embeddings` a: blocked — inputs.py: `create_embeddings` calls BertTokenizer/BertModel.from_pretrained, which download weights from the HuggingFace Hub over the network; no local model directory is available.
- `news/src/python/create_bert_embeddings.py::create_embeddings` b: blocked — inputs.py: `create_embeddings` calls BertTokenizer/BertModel.from_pretrained, which download weights from the HuggingFace Hub over the network; no local model directory is available.
- `news/src/python/create_bert_embeddings.py::create_embeddings` c: blocked — inputs.py: `create_embeddings` calls BertTokenizer/BertModel.from_pretrained, which download weights from the HuggingFace Hub over the network; no local model directory is available.
- `news/src/python/create_bert_embeddings.py::create_embeddings` d: blocked — inputs.py: `create_embeddings` calls BertTokenizer/BertModel.from_pretrained, which download weights from the HuggingFace Hub over the network; no local model directory is available.
- `news/src/python/create_bert_embeddings.py::create_embeddings` e: blocked — inputs.py: `create_embeddings` calls BertTokenizer/BertModel.from_pretrained, which download weights from the HuggingFace Hub over the network; no local model directory is available.
- `news/src/python/create_category_ctrs.py::write_news_category_ctr_update` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `news/src/python/mind_data.py::MindData.read_news` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `news/src/python/mind_data.py::MindData.read_news` b: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `news/src/python/mind_data.py::MindData.read_data` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `news/src/python/mind_data.py::MindData.sample_valid_data` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `news/src/python/train_cold_start.py::save_embeddings` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `news/src/python/train_cold_start.py::read_bert_embeddings_from_file` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `billion-scale-vector-search/app/src/main/python/recall.py::main` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `commerce-product-ranking/scripts/evaluate.py::main` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `commerce-product-ranking/scripts/evaluate.py::main` b: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `hypencoder/model2onnx.py::QueryEncoderWrapper.forward` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `hypencoder/model2onnx.py::_get_weights_and_biases_static` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::subgraph_GenerateKeywords` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::subgraph_EvaluateCategory` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::subgraph_EvaluateFilters` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::EvaluateResults` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `examples/book-search/frontend/app.py::feed_catalog` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `examples/ecommerce-user-preferences/webapp/app.py::chat` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `examples/ecommerce-user-preferences/webapp/app.py::chat` b: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `examples/ecommerce-user-preferences/webapp/app.py::chat` c: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `examples/ecommerce-user-preferences/webapp/app.py::chat` d: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `examples/ecommerce-user-preferences/webapp/app.py::update_preferences` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `examples/ecommerce-user-preferences/webapp/app.py::get_wikipedia_image` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `examples/google-cloud/cloud-functions/python/main.py::get_blobs` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `examples/google-cloud/cloud-functions/python/main.py::listfiles` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `examples/google-cloud/cloud-functions/python/main.py::getlogs` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `examples/in-context-learning/categorize_group.py::inference` a: blocked — inputs.py: `inference` performs an HTTP POST to a Vespa server at http://localhost:8080/search/, which needs a running Vespa instance and network access that is not available here.
- `examples/embedder-auto-training-evaluation/training-evaluation/evaluate.py::main` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `examples/embedder-auto-training-evaluation/training-evaluation/positives-negatives.py::main` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `examples/embedder-auto-training-evaluation/training-evaluation/positives-negatives.py::main` b: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `examples/embedder-auto-training-evaluation/training-evaluation/train.py::TrainDataset.__getitem__` a: blocked — inputs.py: every call of `TrainDataset.__getitem__` returns a `sentence_transformers.InputExample`, which needs the sentence_transformers package; not installed in this venv, and its install was not attempted in this run.
- `examples/mcp-server-app/script/generate_data.py::save_vespa_feed` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `examples/workshop-ecommerce/preprocess.py::process_orders` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `examples/workshop-ecommerce/preprocess.py::process_orders` b: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `examples/workshop-ecommerce/preprocess.py::process_orders` c: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `examples/workshop-ecommerce/preprocess.py::process_users` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `examples/workshop-ecommerce/preprocess.py::process_products` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `rag-blueprint/eval/evaluate_match_phase.py::match_weakand_query_fn` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `rag-blueprint/eval/train_lightgbm.py::perform_cross_validation` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `rag-blueprint/eval/train_lightgbm.py::perform_cross_validation` b: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `rag-blueprint/eval/train_logistic_regression.py::perform_cross_validation` a: blocked — verify.py: not_equivalent on 'empty-file': before raised KeyError, after raised ValueError. The original raises KeyError('mean') on a header-only file whose feature column is non-numeric, and the describe-free repair cannot reproduce that exception. The line stays in submissions.jsonl, not counted as measured.
- `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.gen_similarity_maps` a: blocked — inputs.py: the unit's module does not load here: AttributeError: SimMapGenerator is not defined here: loading the module skipped line 19 `class SimMapGenerator:` (TypeError), with stand-ins for colpali_engine.
- `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.gen_similarity_maps` b: blocked — inputs.py: the unit's module does not load here: AttributeError: SimMapGenerator is not defined here: loading the module skipped line 19 `class SimMapGenerator:` (TypeError), with stand-ins for colpali_engine.
- `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.gen_similarity_maps` c: blocked — inputs.py: the unit's module does not load here: AttributeError: SimMapGenerator is not defined here: loading the module skipped line 19 `class SimMapGenerator:` (TypeError), with stand-ins for colpali_engine.
- `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator._prepare_similarity_map_tensor` a: blocked — inputs.py: the unit's module does not load here: AttributeError: SimMapGenerator is not defined here: loading the module skipped line 19 `class SimMapGenerator:` (TypeError), with stand-ins for colpali_engine.
- `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.should_filter_token` a: blocked — verify.py: no_inputs: no inputs could be generated for visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.should_filter_token: the unit's module does not load here: AttributeError: SimMapGenerator is not defined here (line 19 class statement skipped, TypeError, with stand-ins for colpali_engine). The line stays in submissions.jsonl, unmeasured.
- `visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.get_result_from_query` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.query_vespa_colpali` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.get_suggestions` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `visual-retrieval-colpali/prepare_feed_deploy.py::generate_embeddings` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `visual-retrieval-colpali/src/main.py::get_and_store_sim_maps` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `visual-retrieval-colpali/src/main.py::get_and_store_sim_maps` b: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `visual-retrieval-colpali/src/main.py::get_and_store_sim_maps` c: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `visual-retrieval-colpali/src/main.py::fetch_results` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `visual-retrieval-colpali/src/main.py::get_suggestions` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `visual-retrieval-colpali/src/main.py::message_generator` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `visual-retrieval-colpali/src/main.py::message_generator` b: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `visual-retrieval-colpali/src/main.py::message_generator` d: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `visual-retrieval-colpali/src/main.py::get_sim_map` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `visual-retrieval-colpali/src/frontend/app.py::SearchResult` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `visual-retrieval-colpali/src/frontend/app.py::ChatResult` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `visual-retrieval-colpali/src/frontend/app.py::SimMapButtonPoll` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `reverse-image-search/script/feed.py::run` a: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `reverse-image-search/script/feed.py::run` b: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
- `reverse-image-search/script/feed.py::run` c: deferred — accepted; not measured. Outside the 20 repair places, or inputs not requested because the unit needs a network service, a live Vespa or LLM endpoint, cloud credentials or data the repository does not hold.
