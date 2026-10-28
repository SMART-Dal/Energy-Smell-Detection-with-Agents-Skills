# Energy report — sample-apps @ e2ed22d

166 units listed, 146 with an accepted suspicion · 31 repairs submitted, 164 deferred · 12 confirmed · 4 partial · 1 regressed · 3 negligible · 11 over_limit · 11 applied
Noise floor 1.1% (from: session calibration).

## Applied

### `incremental-search/search-suggestions/count_terms.py::process_docs` — C3S4-count_terms-process_docs-docfreq (C3.S4)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +39.8%.
The agent measured `partial`; re-measured `confirmed`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| many-docs | 111.28 | 45.59 | +59.0% | 0.7% | yes |
| bigrams | 101.38 | 55.73 | +45.0% | 4.1% | yes |
| trigrams | 103.38 | 47.99 | +53.6% | 2.1% | yes |
| high-duplicates | 57.38 | 56.38 | +1.7% | 0.8% | yes |

### `news/src/python/evaluate.py::predictions` — C3S4-news_evaluate-predictions-index (C3.S4)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +99.1%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 19 `url, cert = connect()` (FileNotFoundError); line 103 `train_metrics = calc_metrics(train_impressions_file)` (SystemExit); line 104 `valid_metrics = calc_metrics(valid_impressions_file)` (SystemExit); line 106 `print("Train: " + str(train_metrics))` (NameError); line 107 `print("Valid: " + str(valid_metrics))` (NameError).
Loaded skipping failing top-level statements: line 19 `url, cert = connect()` (FileNotFoundError); line 103 `train_metrics = calc_metrics(train_impressions_file)` (SystemExit); line 104 `valid_metrics = calc_metrics(valid_impressions_file)` (SystemExit); line 106 `print("Train: " + str(train_metrics))` (NameError); line 107 `print("Valid: " + str(valid_metrics))` (NameError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| wide-children | 112.64 | 0.79 | +99.3% | 0.1% | yes |
| tail-matches | 111.45 | 0.60 | +99.5% | 0.0% | yes |
| float-relevance | 113.63 | 1.06 | +99.1% | 0.1% | yes |
| many-children | 111.11 | 1.51 | +98.6% | 0.1% | yes |

### `news/src/python/create_bert_embeddings.py::write_embedding` — C10S1-create_bert-write_embedding-join (C10.S1)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +41.5%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 15 `data_dir = sys.argv[1]` (IndexError); line 18 `train_news_file = os.path.join(data_dir, "train", "news.t...` (NameError); line 19 `train_embedding_file = os.path.join(data_dir, "train", "n...` (NameError); line 20 `dev_news_file = os.path.join(data_dir, "dev", "news.tsv")` (NameError); line 21 `dev_embedding_file = os.path.join(data_dir, "dev", "news_...` (NameError).
Loaded skipping failing top-level statements: line 15 `data_dir = sys.argv[1]` (IndexError); line 18 `train_news_file = os.path.join(data_dir, "train", "news.t...` (NameError); line 19 `train_embedding_file = os.path.join(data_dir, "train", "n...` (NameError); line 20 `dev_news_file = os.path.join(data_dir, "dev", "news.tsv")` (NameError); line 21 `dev_embedding_file = os.path.join(data_dir, "dev", "news_...` (NameError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| normal-16384 | 92.99 | 53.77 | +42.2% | 3.0% | yes |
| normal-32768 | 93.36 | 53.72 | +42.5% | 1.2% | yes |
| normal-50000 | 83.88 | 50.04 | +40.3% | 0.3% | yes |
| mixed-magnitudes-20000 | 90.77 | 53.56 | +41.0% | 0.7% | yes |

### `incremental-search/search-suggestions/count_terms.py::count_terms` — C10S2-count_terms-count_terms-isdisjoint (C10.S2)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +43.8%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| trigrams-long | 98.92 | 54.41 | +45.0% | 10.3% | yes |
| fourgrams | 96.32 | 53.80 | +44.1% | 1.4% | yes |
| fivegrams | 103.73 | 53.70 | +48.2% | 2.1% | yes |
| all-unique-trigrams | 87.72 | 54.61 | +37.7% | 2.7% | yes |

### `incremental-search/search-suggestions/accepted_words.py::process_docs` — C10S3-accepted_words-process_docs-update (C10.S3)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +8.8%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large-corpus | 62.06 | 56.59 | +8.8% | 7.3% | yes |
| duplicates | 65.26 | 60.14 | +7.8% | 1.0% | yes |
| skipped-docs | 60.64 | 54.88 | +9.5% | 3.8% | yes |
| mixed-case-digits | 62.29 | 56.62 | +9.1% | 2.4% | yes |

### `visual-retrieval-colpali/prepare_feed_deploy.py::float_to_binary_embedding` — C6S1-prepare_feed-float_to_binary-boolmask (C6.S1)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +28.2%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 65 `from colpali_engine.models import ColPali, ColPaliProcessor` (ImportError); line 129 `VESPA_CLOUD_SECRET_TOKEN = os.getenv("VESPA_CLOUD_SECRET_...` (EOFError); line 138 `GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or input(` (EOFError); line 146 `gemini_client = genai.Client(api_key=GEMINI_API_KEY)` (NameError); line 150 `device = get_torch_device("auto")` (TypeError); line 151 `print(f"Using device: {device}")` (NameError); line 154 `model = ColPali.from_pretrained(` (NameError); line 160 `processor = ColPaliProcessor.from_pretrained(MODEL_NAME)` (NameError); line 360 `print(f"Max text length: {np.max(text_lengths)}")` (ValueError); line 361 `print(f"Min text length: {np.min(text_lengths)}")` (ValueError); line 461 `pdf_pages[46]["image"]` (IndexError); line 463 `pdf_pages[46]["queries"]` (IndexError); line 574 `embeddings = generate_embeddings(images, model, processor)` (NameError); line 576 `embeddings.shape` (NameError); line 596 `for pdf, embedding in zip(pdf_pages, embeddings):` (NameError); line 972 `VESPA_TEAM_API_KEY = os.getenv("VESPA_TEAM_API_KEY") or i...` (EOFError); line 977 `vespa_cloud = VespaCloud(` (NameError); line 985 `vespa_cloud.deploy()` (NameError); line 988 `endpoint_url = vespa_cloud.get_token_endpoint()` (NameError); line 989 `print(f"Application deployed. Token endpoint URL: {endpoi...` (NameError); line 1000 `app = Vespa(url=endpoint_url, vespa_cloud_secret_token=VE...` (NameError); line 1001 `app.get_application_status()` (NameError); line 1013 `app.feed_async_iterable(vespa_feed, schema=VESPA_SCHEMA_N...` (NameError).
Loaded skipping failing top-level statements: line 65 `from colpali_engine.models import ColPali, ColPaliProcessor` (ImportError); line 129 `VESPA_CLOUD_SECRET_TOKEN = os.getenv("VESPA_CLOUD_SECRET_...` (EOFError); line 138 `GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or input(` (EOFError); line 146 `gemini_client = genai.Client(api_key=GEMINI_API_KEY)` (NameError); line 150 `device = get_torch_device("auto")` (TypeError); line 151 `print(f"Using device: {device}")` (NameError); line 154 `model = ColPali.from_pretrained(` (NameError); line 160 `processor = ColPaliProcessor.from_pretrained(MODEL_NAME)` (NameError); line 360 `print(f"Max text length: {np.max(text_lengths)}")` (ValueError); line 361 `print(f"Min text length: {np.min(text_lengths)}")` (ValueError); line 461 `pdf_pages[46]["image"]` (IndexError); line 463 `pdf_pages[46]["queries"]` (IndexError); line 574 `embeddings = generate_embeddings(images, model, processor)` (NameError); line 576 `embeddings.shape` (NameError); line 596 `for pdf, embedding in zip(pdf_pages, embeddings):` (NameError); line 972 `VESPA_TEAM_API_KEY = os.getenv("VESPA_TEAM_API_KEY") or i...` (EOFError); line 977 `vespa_cloud = VespaCloud(` (NameError); line 985 `vespa_cloud.deploy()` (NameError); line 988 `endpoint_url = vespa_cloud.get_token_endpoint()` (NameError); line 989 `print(f"Application deployed. Token endpoint URL: {endpoi...` (NameError); line 1000 `app = Vespa(url=endpoint_url, vespa_cloud_secret_token=VE...` (NameError); line 1001 `app.get_application_status()` (NameError); line 1013 `app.feed_async_iterable(vespa_feed, schema=VESPA_SCHEMA_N...` (NameError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| colpali-large-2048x128 | 79.83 | 55.55 | +30.4% | 1.4% | yes |
| dim-64-3000-patches | 81.31 | 55.01 | +32.3% | 0.6% | yes |
| dim-1024-900-patches | 72.94 | 57.97 | +20.5% | 1.2% | yes |
| many-patches-4096x128 | 79.25 | 55.88 | +29.5% | 1.6% | yes |

### `visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.float_to_binary_embedding` — C6S1-vespa_app-float_to_binary-boolmask (C6.S1)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +19.1%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 10 `from .colpali import SimMapGenerator` (ImportError).
Loaded skipping failing top-level statements: line 10 `from .colpali import SimMapGenerator` (ImportError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| all-positive-1024 | 66.35 | 52.30 | +21.2% | 8.0% | yes |
| all-negative-1024 | 63.71 | 51.98 | +18.4% | 0.3% | yes |
| zeros-mixed-2048 | 64.98 | 52.34 | +19.4% | 0.2% | yes |
| wide-8192 | 66.30 | 54.87 | +17.2% | 1.0% | yes |

### `text-video-search/src/python/embedding.py::sample_images` — C7S4-embedding-sample_images-index_first (C7.S4)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +71.6%.
Behaviour compared under a relaxed rule: loaded with these uninstalled packages stood in for: clip.
Loaded with uninstalled packages stood in for: clip.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| sample-8-of-80-uint8 | 104.35 | 36.56 | +65.0% | 0.2% | yes |
| sample-30-of-320-mid | 105.80 | 28.22 | +73.3% | 0.0% | yes |
| sample-20-of-200-gray | 104.05 | 33.31 | +68.0% | 0.5% | yes |
| sample-8-of-80-float32 | 108.12 | 21.42 | +80.2% | 0.0% | yes |

### `feed-split.py::what_language` — C1S4-feed_split-what_language-text_once (C1.S4)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +14.8%.
Behaviour compared under a relaxed rule: loaded with these uninstalled packages stood in for: tiktoken.
Loaded with uninstalled packages stood in for: tiktoken.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| java-near-end | 56.83 | 50.65 | +10.9% | 1.2% | yes |
| no-markers | 56.97 | 51.92 | +8.9% | 5.2% | yes |
| curl-at-index-zero-large | 62.42 | 51.26 | +17.9% | 1.3% | yes |
| highlight-not-at-start | 66.03 | 51.88 | +21.4% | 2.1% | yes |

### `news/src/python/train_cold_start.py::read_bert_embeddings_from_file` — C10S1-train_cold_start-read_bert-np_parse (C10.S1)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +11.8%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| all-match | 69.73 | 62.68 | +10.1% | 1.3% | yes |
| half-match | 60.17 | 54.47 | +9.5% | 3.4% | yes |
| duplicates | 67.34 | 60.67 | +9.9% | 0.2% | yes |
| scientific-notation | 64.17 | 52.90 | +17.6% | 0.1% | yes |

### `news/src/python/create_category_ctrs.py::read_content_file` — C6S1-create_category_ctrs-read_content_file-csvreader (C6.S1)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +37.5%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large-30k | 94.13 | 56.59 | +39.9% | 4.4% | yes |
| duplicates-15k | 95.88 | 57.06 | +40.5% | 2.4% | yes |
| long-text-5k | 66.92 | 56.31 | +15.9% | 1.5% | yes |
| short-text-20k | 111.39 | 51.30 | +53.9% | 0.9% | yes |

## Confirmed, not applied

### `incremental-search/search-suggestions/count_terms.py::count_terms` — C1S4-count_terms-count_terms-slice_once (C1.S4)

**confirmed** — not applied: changes the same function as C10S2-count_terms-count_terms-isdisjoint, which is applied; both were written against the original, so only one can be
Mean saving across its cases: +9.2%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| trigrams-long | 71.17 | 63.97 | +10.1% | 3.0% | yes |
| fourgrams | 68.17 | 62.81 | +7.9% | 0.6% | yes |
| fivegrams | 70.27 | 64.67 | +8.0% | 4.0% | yes |
| all-unique-trigrams | 69.02 | 61.48 | +10.9% | 1.9% | yes |

## Measured, not confirmed

### `feed-split.py::split_text` — C10S4-feed_split-split_text-join (C10.S4)

**negligible** — no case moved more than the noise: the largest reading was +0.5% +-1.5% on 'lists-and-links', against a clean 1.1% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: +0.2%.
Behaviour compared under a relaxed rule: loaded with these uninstalled packages stood in for: tiktoken.
Loaded with uninstalled packages stood in for: tiktoken.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| lists-and-links | 67.50 | 67.19 | +0.5% | 1.5% | no: pairs disagree |
| top-level-tables | 62.49 | 62.51 | -0.0% | 1.1% | no: pairs disagree |
| tables-inside-divs | 60.95 | 61.05 | -0.2% | 1.3% | no: pairs disagree |
| mixed-large | 59.36 | 59.12 | +0.4% | 0.8% | no: pairs disagree |

### `colbert-long/scripts/convert.py::remove_control_characters` — C10S1-colbert_convert-remove_control_chars-regex (C10.S1)

**regressed** — the repair costs more than the code it replaces: 120.5% lost on 'long-line', above the 1.1% noise floor, and no case improved. Worse on 4 of 4 cases ('ascii-prose', 'unicode-mix', 'long-line', 'log-multiline').
Mean saving across its cases: -115.7%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 17 `documents = load_dataset('Shitao/MLDR', "corpus-en", spli...` (RuntimeError); line 19 `with open(feed_file, "w") as f:` (NameError).
Loaded skipping failing top-level statements: line 17 `documents = load_dataset('Shitao/MLDR', "corpus-en", spli...` (RuntimeError); line 19 `with open(feed_file, "w") as f:` (NameError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| ascii-prose | 44.69 | 99.22 | -122.0% | 21.6% | yes |
| unicode-mix | 53.01 | 105.56 | -99.1% | 6.0% | yes |
| long-line | 42.58 | 93.90 | -120.5% | 5.5% | yes |
| log-multiline | 42.14 | 93.20 | -121.2% | 10.1% | yes |

### `colbert-long/scripts/convert.py::remove_control_characters` — C4S7-colbert_convert-remove_control_chars-isprintable (C4.S7)

**partial** — saves energy on 1 of 4 inputs ('long-line'; best 98.3% +-0.0% on 'long-line'), and no saving that can be told from noise on the rest: 'ascii-prose' -2.1% +-2.3% (its pairs disagree too much to tell); 'unicode-mix' -2.3% +-3.1% (its pairs disagree too much to tell); 'log-multiline' -2.0% +-6.5% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does. Behaviour was compared under a relaxed rule, which the report must repeat: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 17 `documents = load_dataset('Shitao/MLDR', "corpus-en", spli...` (RuntimeError); line 19 `with open(feed_file, "w") as f:` (NameError).
Mean saving across its cases: +23.0%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 17 `documents = load_dataset('Shitao/MLDR', "corpus-en", spli...` (RuntimeError); line 19 `with open(feed_file, "w") as f:` (NameError).
Measured twice: the first measurement came out `partial` with an input too noisy to read, and this is the second.
Loaded skipping failing top-level statements: line 17 `documents = load_dataset('Shitao/MLDR', "corpus-en", spli...` (RuntimeError); line 19 `with open(feed_file, "w") as f:` (NameError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| ascii-prose | 58.74 | 59.97 | -2.1% | 2.2% | no: pairs disagree |
| unicode-mix | 56.55 | 57.86 | -2.3% | 3.1% | no: pairs disagree |
| long-line | 95.36 | 1.58 | +98.3% | 0.0% | yes |
| log-multiline | 51.37 | 52.41 | -2.0% | 6.5% | no: pairs disagree |

### `news/src/python/train_cold_start.py::write_embeddings` — C10S3-train_cold_start-write_embeddings-tolist (C10.S3)

**partial** — saves energy on 3 of 4 inputs ('large', 'narrow', 'many'; best 5.7% +-1.4% on 'narrow'), and no saving that can be told from noise on the rest: 'wide' +1.5% +-1.8% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +3.6%.
Measured twice: the first measurement came out `partial` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large | 60.35 | 57.77 | +4.3% | 1.9% | yes |
| wide | 57.38 | 56.51 | +1.5% | 1.8% | no: pairs disagree |
| narrow | 60.45 | 57.03 | +5.7% | 1.4% | yes |
| many | 64.54 | 62.66 | +2.9% | 2.4% | yes |

### `incremental-search/search-suggestions/count_terms.py::process_doc` — C6S3-count_terms-process_doc-merge (C6.S3)

**negligible** — no case moved more than the noise: the largest reading was +3.7% +-3.7% on 'tl4-huge', against a clean 1.1% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: +1.4%.
Measured twice: the first measurement came out `partial` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| tl3-large | 57.77 | 56.22 | +2.7% | 3.1% | no: pairs disagree |
| tl4-huge | 58.85 | 56.67 | +3.7% | 3.7% | no: pairs disagree |
| common-words | 56.83 | 56.82 | +0.0% | 3.1% | no: pairs disagree |
| repetitive | 53.02 | 53.52 | -0.9% | 0.1% | no: within the floor |

### `news/src/python/mind_data.py::MindData.sample_valid_data` — C7S4-mind_data-sample_valid_data-filter_first (C7.S4)

**negligible** — no case moved more than the noise: the largest reading was +0.7% +-0.8% on 'many-short-low-prob', against a clean 1.1% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: +0.4%.
Measured twice: the first measurement came out `negligible` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| typical-valid | 56.05 | 56.07 | -0.0% | 1.2% | no: pairs disagree |
| many-short-partial | 57.25 | 57.10 | +0.3% | 1.5% | no: pairs disagree |
| train-impressions | 58.24 | 57.89 | +0.6% | 0.6% | no: pairs disagree |
| many-short-low-prob | 58.95 | 58.56 | +0.7% | 0.8% | no: pairs disagree |

### `incremental-search/search-suggestions/count_terms.py::write_json_file` — C10S2-count_terms-write_json_file-replace (C10.S2)

**partial** — saves energy on 3 of 4 inputs ('many-terms', 'double-spaces', 'high-counts'; best 5.8% +-3.0% on 'double-spaces'), and no saving that can be told from noise on the rest: 'single-word-terms' +1.4% +-4.7% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +3.7%.
Measured twice: the first measurement came out `partial` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| single-word-terms | 59.99 | 59.16 | +1.4% | 4.8% | no: pairs disagree |
| many-terms | 59.93 | 57.71 | +3.7% | 2.2% | yes |
| double-spaces | 62.50 | 58.87 | +5.8% | 3.0% | yes |
| high-counts | 61.89 | 59.54 | +3.8% | 0.3% | yes |

### `incremental-search/search-suggestions/count_terms.py::process_docs` — C1S1-count_terms-process_docs-total_count (C1.S1)

**partial** — saves energy on 1 of 4 inputs ('high-duplicates'; best 1.4% +-0.7% on 'high-duplicates'), and no saving that can be told from noise on the rest: 'many-docs' +0.6% +-4.0% (its pairs disagree too much to tell); 'bigrams' -0.3% +-1.3% (its pairs disagree too much to tell); 'trigrams' -0.3% +-1.4% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +0.4%.
Measured twice: the first measurement came out `partial` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| many-docs | 61.08 | 60.72 | +0.6% | 4.0% | no: pairs disagree |
| bigrams | 59.50 | 59.66 | -0.3% | 1.3% | no: pairs disagree |
| trigrams | 58.09 | 58.26 | -0.3% | 1.4% | no: pairs disagree |
| high-duplicates | 60.98 | 60.10 | +1.4% | 0.7% | yes |

## Not measured

### `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator._prepare_similarity_map_tensor` — C10S3-colpali-prepare_sim_map-index_put (C10.S3)

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures
The agent measured `error`; re-measured `over_limit`.

### `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator._prepare_similarity_map_tensor` — C3S2-colpali-prepare_sim_map-hoist_seq_len (C3.S2)

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures
The agent measured `error`; re-measured `over_limit`.

### `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.should_filter_token` — C8S2-colpali-should_filter_token-precompile (C8.S2)

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures
The agent measured `error`; re-measured `over_limit`.

### `visual-retrieval-colpali/src/backend/cache.py::LRUCache.get` — C1S4-cache-lrucache_get-single_probe (C1.S4)

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures
The agent measured `inconclusive`; re-measured `over_limit`.

### `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/vespa_module/vespa_retriever.py::create_conditions` — C8S2-vespa_retriever-create_conditions-operators (C8.S2)

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures
The agent measured `inconclusive`; re-measured `over_limit`.

### `feed_to_vespa.py::get_feed_docids` — C3S2-feed_to_vespa-get_feed_docids-prefix (C3.S2)

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures
The agent measured `inconclusive`; re-measured `over_limit`.

### `feed_to_vespa.py::get_feed_docids` — C6S3-feed_to_vespa-get_feed_docids-setcomp (C6.S3)

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures
The agent measured `inconclusive`; re-measured `over_limit`.

### `news/src/python/mind_data.py::MindData.lookup_index` — C10S2-mind_data-lookup_index-setdefault (C10.S2)

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures
The agent measured `error`; re-measured `over_limit`.

### `news/src/python/mind_data.py::MindData.add_impressions` — C1S4-mind_data-add_impressions-content_once (C1.S4)

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures
The agent measured `inconclusive`; re-measured `over_limit`.

### `news/src/python/mind_data.py::MindData.sample_valid_data` — C1S4-mind_data-sample_valid_data-sum_once (C1.S4)

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures
The agent measured `inconclusive`; re-measured `over_limit`.

### `news/src/python/train_cold_start.py::read_bert_embeddings_from_file` — C8S3-train_cold_start-read_bert-news_map (C8.S3)

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures
The agent measured `inconclusive`; re-measured `over_limit`.

## Detected, not measured

Accepted findings with no measurement: deferred beyond the repairs chosen for measurement, or blocked.

- `incremental-search/search-suggestions/count_terms.py::read_common_words` a: deferred — over_limit: verify.py reported that 20 repairs in this session already have a verdict, the most it measures, so this repair was not measured
- `incremental-search/search-suggestions/accepted_words.py::read_common_words` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `feed-split.py::main` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `feed-split.py::main` c: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `feed-split.py::main` d: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `feed-split.py::move_linkable_item_to_single_entity` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `feed_to_vespa.py::get_feed_docids` a: deferred — over_limit: verify.py reported that 20 repairs in this session already have a verdict, the most it measures, so this repair was not measured
- `feed_to_vespa.py::get_feed_docids` b: deferred — over_limit: verify.py reported that 20 repairs in this session already have a verdict, the most it measures, so this repair was not measured
- `feed_to_vespa.py::update_endpoint` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `feed_to_vespa.py::get_indexed_docids` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `feed_to_vespa.py::vespa_visit` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `feed_to_vespa.py::vespa_remove` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `incremental-search/search-as-you-type/feed_to_vespa.py::vespa_feed` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `incremental-search/search-as-you-type/feed_to_vespa.py::vespa_remove` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `incremental-search/search-as-you-type/feed_to_vespa.py::update_endpoint` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `incremental-search/search-as-you-type/feed_to_vespa.py::update_endpoint` b: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `incremental-search/search-as-you-type/feed_to_vespa.py::get_feed_docids` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `msmarco-ranking/python/to-vespa-feed.py::<module>` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `msmarco-ranking/python/evaluate_passage_run.py::get_result` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `msmarco-ranking/python/evaluate_passage_run.py::eval_query` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `multilingual-search/ext/evaluate.py::search` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `scaling-tutorial/ext/transform_ms_marco.py::<module>` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `test/test.py::run_url` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `test/test.py::parse_file` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `test/test.py::exec_file` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `test/test.py::process_liquid` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `test/test.py::parse_page` a: deferred — over_limit: verify.py reported that 20 repairs in this session already have a verdict, the most it measures, so this repair was not measured
- `test/test.py::exec_wait` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `hypencoder/encode_query.py::main` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `news/src/python/evaluate.py::calc_metrics` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `news/src/python/evaluate.py::calc_metrics` b: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `news/src/python/evaluate.py::calc_impression` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `news/src/python/vespa_client.py::query_user_embedding` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `news/src/python/vespa_client.py::query_news` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `news/src/python/create_bert_embeddings.py::create_embeddings` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `news/src/python/create_bert_embeddings.py::create_embeddings` b: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `news/src/python/create_bert_embeddings.py::create_embeddings` d: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `news/src/python/create_bert_embeddings.py::create_embeddings` e: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `news/src/python/mind_data.py::MindData.read_news` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `news/src/python/mind_data.py::MindData.sample_valid_data` b: deferred — over_limit: verify.py reported that 20 repairs in this session already have a verdict, the most it measures, so this repair was not measured
- `news/src/python/mind_data.py::MindData.add_impressions` a: deferred — over_limit: verify.py reported that 20 repairs in this session already have a verdict, the most it measures, so this repair was not measured
- `news/src/python/mind_data.py::MindData.lookup_index` a: blocked — verify.py: each of the 1,667,301 calls in a window gets fresh arguments, and building them would take about 10.6s (limit 10s): one call does too little work for arguments to be built per call
- `news/src/python/mind_data.py::MindData.get_news_content_tensors` a: deferred — never measured: when writing the repair, no bulk form was equivalent, because indices absent from news_content must stay 0, which rules out arange; inputs were generated but no submission was made
- `news/src/python/train_cold_start.py::train_model` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `news/src/python/train_cold_start.py::save_embeddings` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `news/src/python/train_cold_start.py::read_bert_embeddings_from_file` a: deferred — over_limit: verify.py reported that 20 repairs in this session already have a verdict, the most it measures, so this repair was not measured
- `news/src/python/train_cold_start.py::read_bert_embeddings` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `news/src/python/train_mf.py::save_embeddings` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `news/src/python/train_mf.py::write_embeddings` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `news/src/python/convert_to_vespa_format.py::read_impressions_file` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `news/src/python/convert_to_vespa_format.py::generate_random_date` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `news/src/python/create_category_ctrs.py::read_impressions_file` a: deferred — over_limit: verify.py reported that 20 repairs in this session already have a verdict, the most it measures, so this repair was not measured
- `news/src/python/create_category_ctrs.py::write_news_category_ctr_update` a: deferred — over_limit: verify.py reported that 20 repairs in this session already have a verdict, the most it measures, so this repair was not measured
- `rag-blueprint/eval/train_lightgbm.py::perform_cross_validation` b: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `rag-blueprint/eval/train_lightgbm.py::perform_cross_validation` c: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `rag-blueprint/eval/train_lightgbm.py::perform_cross_validation` d: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `rag-blueprint/eval/train_logistic_regression.py::perform_cross_validation` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `rag-blueprint/eval/train_logistic_regression.py::perform_cross_validation` b: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `rag-blueprint/eval/evaluate_match_phase.py::match_semantic_query_fn` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/workshop-ecommerce/preprocess.py::process_users` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/workshop-ecommerce/preprocess.py::process_users` c: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/workshop-ecommerce/preprocess.py::process_orders` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/workshop-ecommerce/preprocess.py::process_orders` b: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/workshop-ecommerce/preprocess.py::process_orders` c: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/workshop-ecommerce/preprocess.py::process_products` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/ecommerce-user-preferences/webapp/app.py::chat` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/ecommerce-user-preferences/webapp/app.py::chat` b: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/ecommerce-user-preferences/webapp/app.py::get_wikipedia_image` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/ecommerce-user-preferences/webapp/app.py::get_wikipedia_image` b: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/ecommerce-user-preferences/webapp/app.py::get_wikipedia_image` c: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/ecommerce-user-preferences/webapp/app.py::query_vespa` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/ecommerce-user-preferences/webapp/app.py::query_vespa_facets` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/embedder-auto-training-evaluation/training-evaluation/positives-negatives.py::search` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/embedder-auto-training-evaluation/training-evaluation/positives-negatives.py::main` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/embedder-auto-training-evaluation/training-evaluation/evaluate.py::search` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/embedder-auto-training-evaluation/training-evaluation/evaluate.py::main` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/embedder-auto-training-evaluation/training-evaluation/train.py::TrainDataset.__init__` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/embedder-auto-training-evaluation/training-evaluation/train.py::TrainDataset.__init__` b: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/embedder-auto-training-evaluation/training-evaluation/train.py::TrainDataset.__getitem__` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/google-cloud/cloud-functions/python/main.py::get_blobs` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/google-cloud/cloud-functions/python/main.py::getlogs` b: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/google-cloud/cloud-functions/python/main.py::getlogs` c: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/in-context-learning/categorize_group.py::inference` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/in-context-learning/categorize_group.py::inference` b: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/in-context-learning/categorize_group.py::get_label` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/model-exporting/export_hf_model_from_hf.py::export_model` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/model-exporting/export_model_from_hf.py::export_model` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/part-purchases-demo/ext/parts.py::<module>` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `reverse-image-search/script/feed.py::run` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `reverse-image-search/script/feed.py::run` b: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `reverse-image-search/script/feed.py::run` c: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `reverse-image-search/script/feed.py::run` d: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `reverse-image-search/script/feed.py::_save_image` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `reverse-image-search/script/feed.py::_save_image` b: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `reverse-image-search/script/search.py::_search` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `text-search/python/collect_training_data.py::build_dataset` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `text-search/python/collect_training_data.py::build_dataset` b: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `text-search/python/collect_training_data.py::build_dataset` c: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `text-search/python/collect_training_data.py::get_features` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `text-search/python/collect_training_data.py::annotate_data` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `text-search/python/convert-to-vespa-format.py::main` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `text-search/python/convert-to-vespa-format.py::main` b: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `text-search/python/create-sample-data.py::<module>` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `text-search/python/extract-msmarco.py::getcontent` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `text-search/python/sample-queries-and-documents.py::select_documents` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `text-video-search/src/python/app.py::get_predefined_queries` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `text-video-search/src/python/embedding.py::VideoFeedDataset.__getitem__` b: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `text-video-search/src/python/embedding.py::compute_and_send_video_embeddings` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `text-video-search/src/python/embedding.py::extract_images` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `text-video-search/src/python/embedding.py::send_video_embeddings` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `text-video-search/src/python/embedding.py::search_video_file_names` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `use-case-shopping/convert_meta.py::main` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `use-case-shopping/convert_meta.py::process` b: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `use-case-shopping/convert_reviews.py::main` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `use-case-shopping/create_suggestions.py::<module>` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `use-case-shopping/create_suggestions.py::<module>` b: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `use-case-shopping/create_suggestions.py::<module>` c: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `use-case-shopping/create_suggestions.py::<module>` d: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `use-case-shopping/create_suggestions.py::filter` b: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `visual-retrieval-colpali/prepare_feed_deploy.py::<module>` b: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `visual-retrieval-colpali/refeed_from_hf.py::pil_to_base64` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `visual-retrieval-colpali/vespa_feed_to_hf_dataset.py::<module>` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.gen_similarity_maps` a: blocked — verify.py: the repository's own module does not load here, even skipping the top-level statements that fail: AttributeError: SimMapGenerator is not defined here: loading the module skipped line 19 `class SimMapGenerator:` (TypeError), with stand-ins for colpali_engine (shown for the sibling methods _prepare_similarity_map_tensor and should_filter_token of the same class)
- `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.gen_similarity_maps` b: blocked — verify.py: the repository's own module does not load here, even skipping the top-level statements that fail: AttributeError: SimMapGenerator is not defined here: loading the module skipped line 19 `class SimMapGenerator:` (TypeError), with stand-ins for colpali_engine (shown for the sibling methods of the same class)
- `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator._prepare_similarity_map_tensor` a: blocked — verify.py: the repository's own module does not load here, even skipping the top-level statements that fail: AttributeError: SimMapGenerator is not defined here: loading the module skipped line 19 `class SimMapGenerator:` (TypeError), with stand-ins for colpali_engine
- `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator._prepare_similarity_map_tensor` b: blocked — verify.py: the repository's own module does not load here, even skipping the top-level statements that fail: AttributeError: SimMapGenerator is not defined here: loading the module skipped line 19 `class SimMapGenerator:` (TypeError), with stand-ins for colpali_engine
- `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.should_filter_token` a: blocked — verify.py: the repository's own module does not load here, even skipping the top-level statements that fail: AttributeError: SimMapGenerator is not defined here: loading the module skipped line 19 `class SimMapGenerator:` (TypeError), with stand-ins for colpali_engine
- `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator._blend_image` a: blocked — inputs.py: the unit's module does not load here: AttributeError: SimMapGenerator is not defined here: loading the module skipped line 19 `class SimMapGenerator:` (TypeError), with stand-ins for colpali_engine
- `visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.format_query_results` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.get_result_from_query` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.get_result_from_query` b: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.get_suggestions` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.query_vespa_bm25` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `visual-retrieval-colpali/src/main.py::message_generator` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `visual-retrieval-colpali/src/main.py::message_generator` b: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `visual-retrieval-colpali/src/main.py::get_and_store_sim_maps` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `visual-retrieval-colpali/src/main.py::get_and_store_sim_maps` b: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `visual-retrieval-colpali/src/main.py::<module>` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `visual-retrieval-colpali/src/backend/cache.py::LRUCache.get` a: deferred — over_limit: verify.py reported that 20 repairs in this session already have a verdict, the most it measures, so this repair was not measured
- `billion-scale-image-search/app/src/main/python/create-centroid-feed.py::<module>` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `billion-scale-image-search/app/src/main/python/create-joined-feed.py::<module>` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `billion-scale-image-search/app/src/main/python/create-joined-feed.py::<module>` b: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `billion-scale-image-search/app/src/main/python/create-partial-update-feed.py::<module>` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `billion-scale-image-search/app/src/main/python/pca_train.py::<module>` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `billion-scale-vector-search/app/src/main/python/create-vespa-feed.py::<module>` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `billion-scale-vector-search/app/src/main/python/recall.py::main` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `billion-scale-vector-search/app/src/main/python/recall.py::knn_result_read` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `billion-scale-vector-search/app/src/main/python/recall.py::read_queries` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `colbert-long/scripts/convert.py::<module>` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `colbert-long/scripts/evaluate.py::search` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `commerce-product-ranking/scripts/evaluate.py::main` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `commerce-product-ranking/scripts/evaluate.py::main` b: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `commerce-product-ranking/scripts/evaluate.py::main` c: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `custom-embeddings/create-weights.py::<module>` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `custom-embeddings/weights.py::<module>` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/book-search/frontend/app.py::feed_catalog` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/book-search/frontend/app.py::<module>` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/agentic-streamlit-chatbot/simple_app/streamlit_vespa_app.py::VespaRetriever` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/agentic-streamlit-chatbot/simple_app/streamlit_vespa_app.py::<module>` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/agentic-streamlit-chatbot/simple_app/streamlit_vespa_app.py::<module>` b: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/streamlit_app.py::<module>` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/streamlit_app.py::<module>` b: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::subgraph_GenerateKeywords` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::subgraph_EvaluateCategory` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::subgraph_EvaluateFilters` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::EvaluateResults` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/vespa_module/vespa_retriever.py::create_conditions` a: deferred — over_limit: verify.py reported that 20 repairs in this session already have a verdict, the most it measures, so this repair was not measured
- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/vespa_module/vespa_retriever.py::VespaRetriever` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/vespa_module/update_vespa.py::update_document_quantity` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/vespa_module/update_vespa.py::fetch_documents` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/utils/helpers.py::get_latest_ai_or_human_message` a: deferred — not measured: outside the units chosen for the 20 measurement places (needs a live Vespa/HTTP endpoint, a model download, or is module-level script code), so no inputs were requested
