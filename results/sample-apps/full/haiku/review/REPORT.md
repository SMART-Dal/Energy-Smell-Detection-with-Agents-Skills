# Energy report — sample-apps @ e2ed22d

81 units listed, 56 with an accepted suspicion · 20 repairs submitted, 23 deferred · 12 confirmed · 4 partial · 2 regressed · 2 negligible · 11 applied
Noise floor 1.8% (from: session calibration).

## Applied

### `incremental-search/search-suggestions/count_terms.py::count_terms` — C10S1-count-terms-isdisjoint (C10.S1)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +39.9%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| trigrams-long | 88.63 | 55.82 | +37.0% | 1.1% | yes |
| fourgrams | 90.86 | 53.61 | +41.0% | 0.5% | yes |
| fivegrams | 103.13 | 55.77 | +45.9% | 1.7% | yes |
| all-unique-trigrams | 85.01 | 54.53 | +35.8% | 1.3% | yes |

### `incremental-search/search-suggestions/count_terms.py::write_json_file` — C10S2-write-json-replace (C10.S2)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +3.4%.
Measured twice: the first measurement came out `partial` with an input too noisy to read, and this is the second.
The agent measured `partial`; re-measured `confirmed`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| single-word-terms | 61.37 | 59.65 | +2.8% | 1.1% | yes |
| many-terms | 60.59 | 59.05 | +2.5% | 1.5% | yes |
| double-spaces | 63.83 | 60.79 | +4.8% | 1.3% | yes |
| high-counts | 63.16 | 60.82 | +3.7% | 1.4% | yes |

### `incremental-search/search-suggestions/accepted_words.py::process_docs` — C10S3-accepted-process-update (C10.S3)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +6.8%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large-corpus | 64.63 | 59.97 | +7.2% | 7.0% | yes |
| duplicates | 68.43 | 63.62 | +7.0% | 2.7% | yes |
| skipped-docs | 64.71 | 61.26 | +5.3% | 2.1% | yes |
| mixed-case-digits | 65.90 | 60.79 | +7.8% | 0.7% | yes |

### `news/src/python/train_cold_start.py::read_bert_embeddings` — C5S3-bert-float32-buffer (C5.S3)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +3.8%.
Measured twice: the first measurement came out `partial` with an input too noisy to read, and this is the second.
The agent measured `partial`; re-measured `confirmed`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| c5_large | 60.98 | 58.77 | +3.6% | 0.3% | yes |
| c6_longlines | 58.62 | 56.58 | +3.5% | 2.7% | yes |
| c7_partial | 59.94 | 57.72 | +3.7% | 2.6% | yes |
| c8_sparse | 55.02 | 52.59 | +4.4% | 1.6% | yes |

### `news/src/python/mind_data.py::MindData.read_data` — C1S5-read-data-no-timestamp (C1.S5)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +66.1%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| medium | 119.84 | 44.49 | +62.9% | 3.2% | yes |
| many-lines-few-imps | 117.88 | 28.76 | +75.6% | 0.1% | yes |
| many-users | 122.00 | 41.54 | +66.0% | 0.9% | yes |
| many-news | 121.92 | 48.61 | +60.1% | 1.1% | yes |

### `text-video-search/src/python/embedding.py::sample_images` — C6S2-sample-images-copy-kept (C6.S2)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +73.2%.
Behaviour compared under a relaxed rule: loaded with these uninstalled packages stood in for: clip.
Loaded with uninstalled packages stood in for: clip.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| sample-8-of-80-uint8 | 112.63 | 37.33 | +66.9% | 0.5% | yes |
| sample-30-of-320-mid | 113.58 | 28.22 | +75.2% | 0.1% | yes |
| sample-20-of-200-gray | 112.46 | 33.76 | +70.0% | 0.3% | yes |
| sample-8-of-80-float32 | 111.47 | 21.54 | +80.7% | 1.6% | yes |

### `text-search/python/convert-to-vespa-format.py::main` — C10S2-convert-main-one-write (C10.S2)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +27.4%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 9 `if len(sys.argv) != 5:` (SystemExit); line 13 `source_dir, dest_dir, doc_type, fields = sys.argv[1:5]` (ValueError); line 14 `fields = fields.split(",")` (NameError); line 17 `if not os.path.isdir(source_dir):` (NameError); line 20 `if not os.path.isdir(dest_dir):` (NameError); line 24 `sample_offset_file = os.path.join(source_dir, "test-docs-...` (NameError); line 25 `docs_file = os.path.join(source_dir, "docs.tsv")` (NameError); line 26 `out_file = os.path.join(dest_dir, "documents.jsonl")` (NameError).
Measured twice: the first measurement came out `partial` with an input too noisy to read, and this is the second.
Loaded skipping failing top-level statements: line 9 `if len(sys.argv) != 5:` (SystemExit); line 13 `source_dir, dest_dir, doc_type, fields = sys.argv[1:5]` (ValueError); line 14 `fields = fields.split(",")` (NameError); line 17 `if not os.path.isdir(source_dir):` (NameError); line 20 `if not os.path.isdir(dest_dir):` (NameError); line 24 `sample_offset_file = os.path.join(source_dir, "test-docs-...` (NameError); line 25 `docs_file = os.path.join(source_dir, "docs.tsv")` (NameError); line 26 `out_file = os.path.join(dest_dir, "documents.jsonl")` (NameError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large | 88.00 | 62.98 | +28.4% | 1.3% | yes |
| tiny-lines | 80.32 | 57.30 | +28.7% | 0.7% | yes |
| long-titles | 84.77 | 62.62 | +26.1% | 1.4% | yes |
| single-field | 95.05 | 70.00 | +26.4% | 1.2% | yes |

### `examples/workshop-ecommerce/preprocess.py::process_products` — C3S1-products-records (C3.S1)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +84.1%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| limit-1500 | 106.36 | 24.10 | +77.3% | 0.4% | yes |
| limit-3000 | 102.58 | 16.00 | +84.4% | 0.2% | yes |
| limit-5000 | 100.34 | 12.71 | +87.3% | 0.1% | yes |
| full-all | 100.45 | 12.58 | +87.5% | 0.2% | yes |

### `examples/workshop-ecommerce/preprocess.py::process_users` — C3S1-users-purchases-records (C3.S1)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +42.3%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| full-150-users | 96.91 | 54.14 | +44.1% | 18.6% | yes |
| limit-200 | 63.09 | 59.67 | +5.4% | 0.4% | yes |
| few-users-heavy | 84.94 | 9.36 | +89.0% | 0.1% | yes |
| many-duplicates | 81.96 | 56.97 | +30.5% | 0.8% | yes |

### `visual-retrieval-colpali/prepare_feed_deploy.py::float_to_binary_embedding` — C10S3-prepare-binary-packbits-bool (C10.S3)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +28.2%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 65 `from colpali_engine.models import ColPali, ColPaliProcessor` (ImportError); line 129 `VESPA_CLOUD_SECRET_TOKEN = os.getenv("VESPA_CLOUD_SECRET_...` (EOFError); line 138 `GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or input(` (EOFError); line 146 `gemini_client = genai.Client(api_key=GEMINI_API_KEY)` (NameError); line 150 `device = get_torch_device("auto")` (TypeError); line 151 `print(f"Using device: {device}")` (NameError); line 154 `model = ColPali.from_pretrained(` (NameError); line 160 `processor = ColPaliProcessor.from_pretrained(MODEL_NAME)` (NameError); line 360 `print(f"Max text length: {np.max(text_lengths)}")` (ValueError); line 361 `print(f"Min text length: {np.min(text_lengths)}")` (ValueError); line 461 `pdf_pages[46]["image"]` (IndexError); line 463 `pdf_pages[46]["queries"]` (IndexError); line 574 `embeddings = generate_embeddings(images, model, processor)` (NameError); line 576 `embeddings.shape` (NameError); line 596 `for pdf, embedding in zip(pdf_pages, embeddings):` (NameError); line 972 `VESPA_TEAM_API_KEY = os.getenv("VESPA_TEAM_API_KEY") or i...` (EOFError); line 977 `vespa_cloud = VespaCloud(` (NameError); line 985 `vespa_cloud.deploy()` (NameError); line 988 `endpoint_url = vespa_cloud.get_token_endpoint()` (NameError); line 989 `print(f"Application deployed. Token endpoint URL: {endpoi...` (NameError); line 1000 `app = Vespa(url=endpoint_url, vespa_cloud_secret_token=VE...` (NameError); line 1001 `app.get_application_status()` (NameError); line 1013 `app.feed_async_iterable(vespa_feed, schema=VESPA_SCHEMA_N...` (NameError).
Loaded skipping failing top-level statements: line 65 `from colpali_engine.models import ColPali, ColPaliProcessor` (ImportError); line 129 `VESPA_CLOUD_SECRET_TOKEN = os.getenv("VESPA_CLOUD_SECRET_...` (EOFError); line 138 `GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or input(` (EOFError); line 146 `gemini_client = genai.Client(api_key=GEMINI_API_KEY)` (NameError); line 150 `device = get_torch_device("auto")` (TypeError); line 151 `print(f"Using device: {device}")` (NameError); line 154 `model = ColPali.from_pretrained(` (NameError); line 160 `processor = ColPaliProcessor.from_pretrained(MODEL_NAME)` (NameError); line 360 `print(f"Max text length: {np.max(text_lengths)}")` (ValueError); line 361 `print(f"Min text length: {np.min(text_lengths)}")` (ValueError); line 461 `pdf_pages[46]["image"]` (IndexError); line 463 `pdf_pages[46]["queries"]` (IndexError); line 574 `embeddings = generate_embeddings(images, model, processor)` (NameError); line 576 `embeddings.shape` (NameError); line 596 `for pdf, embedding in zip(pdf_pages, embeddings):` (NameError); line 972 `VESPA_TEAM_API_KEY = os.getenv("VESPA_TEAM_API_KEY") or i...` (EOFError); line 977 `vespa_cloud = VespaCloud(` (NameError); line 985 `vespa_cloud.deploy()` (NameError); line 988 `endpoint_url = vespa_cloud.get_token_endpoint()` (NameError); line 989 `print(f"Application deployed. Token endpoint URL: {endpoi...` (NameError); line 1000 `app = Vespa(url=endpoint_url, vespa_cloud_secret_token=VE...` (NameError); line 1001 `app.get_application_status()` (NameError); line 1013 `app.feed_async_iterable(vespa_feed, schema=VESPA_SCHEMA_N...` (NameError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| colpali-large-2048x128 | 77.02 | 53.68 | +30.3% | 1.9% | yes |
| dim-64-3000-patches | 78.33 | 53.28 | +32.0% | 0.9% | yes |
| dim-1024-900-patches | 72.09 | 56.92 | +21.0% | 0.4% | yes |
| many-patches-4096x128 | 79.86 | 56.39 | +29.4% | 1.3% | yes |

### `visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.float_to_binary_embedding` — C10S3-vespa-binary-packbits-bool (C10.S3)

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +18.5%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 10 `from .colpali import SimMapGenerator` (ImportError).
Loaded skipping failing top-level statements: line 10 `from .colpali import SimMapGenerator` (ImportError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| all-positive-1024 | 65.51 | 53.51 | +18.3% | 0.9% | yes |
| all-negative-1024 | 68.41 | 57.23 | +16.3% | 7.0% | yes |
| zeros-mixed-2048 | 71.60 | 56.52 | +21.1% | 5.1% | yes |
| wide-8192 | 72.12 | 59.00 | +18.2% | 1.5% | yes |

## Confirmed, not applied

### `incremental-search/search-suggestions/count_terms.py::count_terms` — C1S4-count-terms-window-once (C1.S4)

**confirmed** — not applied: changes the same function as C10S1-count-terms-isdisjoint, which is applied; both were written against the original, so only one can be
Mean saving across its cases: +8.8%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| trigrams-long | 64.34 | 57.65 | +10.4% | 2.4% | yes |
| fourgrams | 60.37 | 54.66 | +9.5% | 5.0% | yes |
| fivegrams | 56.03 | 53.55 | +4.4% | 2.8% | yes |
| all-unique-trigrams | 61.44 | 54.69 | +11.0% | 2.7% | yes |

## Measured, not confirmed

### `incremental-search/search-suggestions/count_terms.py::process_docs` — C3S4-process-docs-docs-in-loop (C3.S4)

**partial** — saves energy on 3 of 4 inputs ('many-docs', 'bigrams', 'trigrams'; best 57.7% +-0.3% on 'many-docs'), and no saving that can be told from noise on the rest: 'high-duplicates' +0.3% +-3.7% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +37.9%.
Measured twice: the first measurement came out `partial` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| many-docs | 113.74 | 48.15 | +57.7% | 0.3% | yes |
| bigrams | 103.25 | 60.21 | +41.7% | 0.7% | yes |
| trigrams | 109.44 | 52.68 | +51.9% | 0.5% | yes |
| high-duplicates | 59.67 | 59.51 | +0.3% | 3.7% | no: pairs disagree |

### `incremental-search/search-suggestions/count_terms.py::process_docs` — C1S1-process-docs-dead-total (C1.S1)

**negligible** — no case moved more than the noise: the largest reading was +0.9% +-2.5% on 'many-docs', against a clean 1.8% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: +0.3%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| many-docs | 59.02 | 58.47 | +0.9% | 2.5% | no: pairs disagree |
| bigrams | 58.26 | 58.24 | +0.0% | 1.6% | no: pairs disagree |
| trigrams | 55.77 | 55.83 | -0.1% | 3.5% | no: pairs disagree |
| high-duplicates | 54.47 | 54.39 | +0.2% | 2.8% | no: pairs disagree |

### `incremental-search/search-suggestions/accepted_words.py::write_to_file` — C10S3-accepted-write-join (C10.S3)

**partial** — saves energy on 3 of 4 inputs ('large-60k', 'unicode', 'mixed-punct'; best 35.5% +-1.1% on 'unicode'), and no saving that can be told from noise on the rest: 'huge-words' -22.1% +-205.7% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +20.3%.
Measured twice: the first measurement came out `partial` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large-60k | 68.73 | 57.29 | +16.6% | 1.3% | yes |
| huge-words | 162.95 | 146.86 | +9.9% | 205.7% | no: pairs disagree |
| unicode | 95.65 | 61.70 | +35.5% | 1.1% | yes |
| mixed-punct | 84.26 | 68.23 | +19.0% | 1.4% | yes |

### `colbert-long/scripts/convert.py::remove_control_characters` — C10S1-remove-control-fast-path (C10.S1)

**partial** — saves energy on 1 of 4 inputs ('long-line'; best 98.4% +-0.1% on 'long-line'), and no saving that can be told from noise on the rest: 'ascii-prose' +1.6% +-4.8% (its pairs disagree too much to tell); 'unicode-mix' -2.4% +-5.3% (its pairs disagree too much to tell); 'log-multiline' +0.3% +-4.2% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does. Behaviour was compared under a relaxed rule, which the report must repeat: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 17 `documents = load_dataset('Shitao/MLDR', "corpus-en", spli...` (RuntimeError); line 19 `with open(feed_file, "w") as f:` (NameError).
Mean saving across its cases: +24.5%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 17 `documents = load_dataset('Shitao/MLDR', "corpus-en", spli...` (RuntimeError); line 19 `with open(feed_file, "w") as f:` (NameError).
Loaded skipping failing top-level statements: line 17 `documents = load_dataset('Shitao/MLDR', "corpus-en", spli...` (RuntimeError); line 19 `with open(feed_file, "w") as f:` (NameError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| ascii-prose | 54.72 | 53.82 | +1.6% | 4.8% | no: pairs disagree |
| unicode-mix | 59.43 | 60.85 | -2.4% | 5.3% | no: pairs disagree |
| long-line | 103.30 | 1.64 | +98.4% | 0.1% | yes |
| log-multiline | 60.36 | 60.16 | +0.3% | 4.2% | no: pairs disagree |

### `feed-split.py::split_text` — C10S4-split-text-parts-list (C10.S4)

**negligible** — no case moved more than the noise: the largest reading was +0.8% +-1.5% on 'lists-and-links', against a clean 1.8% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: +0.3%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| lists-and-links | 67.25 | 66.72 | +0.8% | 1.5% | no: pairs disagree |
| top-level-tables | 62.21 | 62.29 | -0.1% | 1.0% | no: pairs disagree |
| tables-inside-divs | 60.89 | 60.81 | +0.1% | 0.0% | no: within the floor |
| mixed-large | 59.44 | 59.16 | +0.5% | 1.5% | no: pairs disagree |

### `text-search/python/extract-msmarco.py::extract_documents` — C9S1-extract-docs-running-offset (C9.S1)

**partial** — saves energy on 2 of 4 inputs ('unicode-1500', 'mixed-3000'; best 5.9% +-0.2% on 'unicode-1500'), and no saving that can be told from noise on the rest: 'long-800' +0.6% +-0.5% (within the 1.8% noise floor); 'long-1200' +0.2% +-1.2% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +2.4%.
Measured twice: the first measurement came out `partial` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| unicode-1500 | 66.28 | 62.36 | +5.9% | 0.2% | yes |
| long-800 | 64.59 | 64.23 | +0.6% | 0.5% | no: within the floor |
| mixed-3000 | 63.95 | 62.10 | +2.9% | 1.6% | yes |
| long-1200 | 62.99 | 62.89 | +0.2% | 1.2% | no: pairs disagree |

### `text-search/python/sample-queries-and-documents.py::select_documents` — C3S2-select-documents-min-hoist (C3.S2)

**regressed** — the repair costs more than the code it replaces: 4.2% lost on 'large-offsets', above the 1.8% noise floor, and no case improved. Worse on 1 of 4 cases ('large-offsets').
Mean saving across its cases: +7.0%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 12 `data_dir = sys.argv[1]` (IndexError); line 16 `query_file = os.path.join(data_dir, "queries.tsv")` (NameError); line 17 `docs_file = os.path.join(data_dir, "docs.tsv")` (NameError); line 18 `offset_file = os.path.join(data_dir, "docs-offset.tsv")` (NameError); line 20 `sample_query_file = os.path.join(data_dir, "test-queries....` (NameError); line 21 `sample_offset_file = os.path.join(data_dir, "test-docs-of...` (NameError).
Measured twice: the first measurement came out `negligible` with an input too noisy to read, and this is the second.
Loaded skipping failing top-level statements: line 12 `data_dir = sys.argv[1]` (IndexError); line 16 `query_file = os.path.join(data_dir, "queries.tsv")` (NameError); line 17 `docs_file = os.path.join(data_dir, "docs.tsv")` (NameError); line 18 `offset_file = os.path.join(data_dir, "docs-offset.tsv")` (NameError); line 20 `sample_query_file = os.path.join(data_dir, "test-queries....` (NameError); line 21 `sample_offset_file = os.path.join(data_dir, "test-docs-of...` (NameError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| query-duplicates | 111.74 | 71.44 | +36.1% | 49.5% | no: pairs disagree |
| many-qids | 57.62 | 58.33 | -1.2% | 2.7% | no: pairs disagree |
| large-offsets | 60.42 | 62.99 | -4.2% | 1.1% | yes |
| already-complete | 57.37 | 58.81 | -2.5% | 3.3% | no: pairs disagree |

### `examples/workshop-ecommerce/preprocess.py::process_orders` — C3S1-orders-records-new (C3.S1)

**regressed** — the repair costs more than the code it replaces: 5.2% lost on 'prior-and-train', above the 1.8% noise floor, and no case improved. Worse on 3 of 4 cases ('prior-limit-10', 'prior-and-train', 'orphan-orders').
Mean saving across its cases: -3.4%.
Measured twice: the first measurement came out `regressed` with an input too noisy to read, and this is the second.
The agent measured `mixed`; re-measured `regressed`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| prior-limit-10 | 69.24 | 74.07 | -7.0% | 0.8% | yes |
| prior-and-train | 94.46 | 99.33 | -5.2% | 2.4% | yes |
| mixed-three-sets | 66.19 | 65.06 | +1.7% | 1.1% | no: within the floor |
| orphan-orders | 63.85 | 65.79 | -3.0% | 0.5% | yes |

## Detected, not measured

Accepted findings with no measurement: deferred beyond the repairs chosen for measurement, or blocked.

- `news/src/python/train_cold_start.py::read_bert_embeddings_from_file` a: deferred — accepted; its inputs are ready, but the 20 measurement places went to higher-expected repairs; not measured
- `news/src/python/mind_data.py::MindData.read_data` b: deferred — accepted; the second part (lookup wrapper, line 100) is small and the 20 measurement places went to higher-expected repairs; not measured
- `text-search/python/collect_training_data.py::build_dataset` a: blocked — it cannot run here: `build_dataset` calls `get_features`, which issues `requests.post` to a Solr server at http://localhost:8080/search/; no input can avoid the network request.
- `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.gen_similarity_maps` a: blocked — it cannot run here: constructing `SimMapGenerator` loads the ColPali model from the HuggingFace hub (network access) as the repository's own caller does at startup, and the internal structure of the Vespa similarity maps consumed by the elided `_prepare_similarity_map_tensor` is not specified, so no valid input can be built.
- `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.gen_similarity_maps` b: blocked — it cannot run here: constructing `SimMapGenerator` loads the ColPali model from the HuggingFace hub (network access) as the repository's own caller does at startup, and the internal structure of the Vespa similarity maps consumed by the elided `_prepare_similarity_map_tensor` is not specified, so no valid input can be built.
- `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator._prepare_similarity_map_tensor` a: blocked — the unit's module does not load here: AttributeError: SimMapGenerator is not defined here: loading the module skipped line 19 `class SimMapGenerator:` (TypeError), with stand-ins for colpali_engine
- `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator._prepare_similarity_map_tensor` b: blocked — the unit's module does not load here: AttributeError: SimMapGenerator is not defined here: loading the module skipped line 19 `class SimMapGenerator:` (TypeError), with stand-ins for colpali_engine
- `visual-retrieval-colpali/prepare_feed_deploy.py::generate_embeddings` a: blocked — it cannot run here: `generate_embeddings` requires a pretrained ColPali model and processor from `ColPali.from_pretrained(MODEL_NAME)`, which needs network access to Hugging Face; the inputs.py generator reported this and no input can avoid it.
- `examples/workshop-ecommerce/preprocess.py::process_users` b: deferred — accepted; the purchase-group filter before the merge is more code than the other repairs and was not measured; the 20 places were used
- `examples/ecommerce-user-preferences/webapp/app.py::get_wikipedia_image` b: deferred — accepted; the batched imageinfo request needs Wikipedia, which cannot be reached here, and it was not requested
- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::subgraph_GenerateKeywords` a: blocked — it cannot run here: the node builds a `ChatOpenAI` model and invokes the chain, a network request to the OpenAI API; no input can avoid that.
- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::subgraph_EvaluateCategory` a: blocked — it cannot run here: the node builds a `ChatOpenAI` chain and invokes it, a request to the OpenAI API.
- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::subgraph_EvaluateFilters` a: blocked — it cannot run here: the node builds a `ChatOpenAI` model and invokes the chain, a request to the OpenAI API.
- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::EvaluateResults` a: blocked — it cannot run here: the node builds a `ChatOpenAI` model and invokes the chain, a request to the OpenAI API.
- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/vespa_module/vespa_retriever.py::VespaRetriever` a: blocked — it cannot run here: the node builds a `Vespa` client and queries a server at `VESPA_URL`, which needs network access and live credentials.
- `examples/agentic-streamlit-chatbot/simple_app/streamlit_vespa_app.py::VespaRetriever` a: deferred — accepted; it needs Vespa, and it was not requested because the 30-unit holding limit was reached
- `examples/google-cloud/cloud-functions/python/main.py::get_blobs` a: blocked — it cannot run here: get_blobs calls google.cloud.storage.Client() and list_blobs(bucket), an authenticated network request to Google Cloud Storage.
- `examples/in-context-learning/categorize_group.py::inference` a: blocked — it cannot run here: inference posts to http://localhost:8080/search/, which needs a running Vespa server.
- `examples/in-context-learning/categorize_group.py::inference` b: blocked — it cannot run here: inference posts to http://localhost:8080/search/, which needs a running Vespa server.
- `news/src/python/create_bert_embeddings.py::create_embeddings` a: blocked — it cannot run here: `create_embeddings` calls `BertTokenizer.from_pretrained('bert-base-uncased')` and `BertModel.from_pretrained('google/bert_uncased_L-8_H-512_A-8')`, which download pretrained models from the Hugging Face Hub and need network access.
- `news/src/python/create_bert_embeddings.py::create_embeddings` b: blocked — it cannot run here: `create_embeddings` calls `BertTokenizer.from_pretrained('bert-base-uncased')` and `BertModel.from_pretrained('google/bert_uncased_L-8_H-512_A-8')`, which download pretrained models from the Hugging Face Hub and need network access.
- `news/src/python/create_bert_embeddings.py::create_embeddings` c: blocked — it cannot run here: `create_embeddings` calls `BertTokenizer.from_pretrained('bert-base-uncased')` and `BertModel.from_pretrained('google/bert_uncased_L-8_H-512_A-8')`, which download pretrained models from the Hugging Face Hub and need network access.
- `news/src/python/create_bert_embeddings.py::create_embeddings` d: blocked — it cannot run here: `create_embeddings` calls `BertTokenizer.from_pretrained('bert-base-uncased')` and `BertModel.from_pretrained('google/bert_uncased_L-8_H-512_A-8')`, which download pretrained models from the Hugging Face Hub and need network access.
- `news/src/python/create_bert_embeddings.py::create_embeddings` e: blocked — it cannot run here: `create_embeddings` calls `BertTokenizer.from_pretrained('bert-base-uncased')` and `BertModel.from_pretrained('google/bert_uncased_L-8_H-512_A-8')`, which download pretrained models from the Hugging Face Hub and need network access.
- `news/src/python/vespa_client.py::query_news` a: blocked — it cannot run here: `query_news` performs `requests.post` to a Vespa search server; no input can avoid the network request.
- `news/src/python/vespa_client.py::query_user_embedding` a: blocked — it cannot run here: `query_user_embedding` performs a live `requests.get` to a Vespa search endpoint; no input can avoid the network request.
- `news/src/python/evaluate.py::calc_impression` a: deferred — accepted; it needs Vespa, and it was not requested because the 30-unit holding limit was reached
- `rag-blueprint/eval/collect_pyvespa.py::feature_collection_second_phase_query_fn` a: blocked — the repair cannot be made to behave identically: the returned query body has two keys, input.query(embedding) and input.query(float_embedding), both embed(text); removing either key changes the returned dict, and sharing one embed value would change it too. Inputs were generated (ready), but no repair could keep the return value equal, so none was submitted.
- `rag-blueprint/eval/collect_pyvespa.py::feature_collection_first_phase_query_fn` a: deferred — accepted; it needs Vespa, and it was not requested because the 30-unit holding limit was reached
- `rag-blueprint/eval/evaluate_ranking.py::rank_first_phase_query_fn` a: deferred — accepted; it needs Vespa, and it was not requested because the 30-unit holding limit was reached
- `rag-blueprint/eval/evaluate_ranking.py::rank_second_phase_query_fn` a: deferred — accepted; it needs Vespa, and it was not requested because the 30-unit holding limit was reached
- `text-video-search/src/python/embedding.py::VideoFeedDataset.__getitem__` a: blocked — it cannot run here: the class's `__init__` loads the CLIP model via `clip.load(model_name)`, which downloads model weights from a remote server.
- `text-video-search/src/python/embedding.py::VideoFeedDataset.__getitem__` b: blocked — it cannot run here: the class's `__init__` loads the CLIP model via `clip.load(model_name)`, which downloads model weights from a remote server.
- `text-video-search/src/python/embedding.py::TextProcessor.embed` a: blocked — it cannot run here: `TextProcessor.embed` needs the CLIP model from `clip.load("ViT-B/32")`, which downloads weights from the network; the `clip` package is not installed.
- `text-video-search/src/python/app.py::get_predefined_queries` a: deferred — accepted; it fetches a remote URL, and it was not requested because the 30-unit holding limit was reached
- `incremental-search/search-as-you-type/feed_to_vespa.py::vespa_feed` a: blocked — it cannot run here: `vespa_feed` posts every document to a Vespa endpoint through curl, a network request.
- `incremental-search/search-as-you-type/feed_to_vespa.py::update_endpoint` a: deferred — accepted; it needs a Vespa endpoint, and it was not requested because the 30-unit holding limit was reached
- `feed_to_vespa.py::vespa_remove` a: blocked — it cannot run here: `vespa_delete` makes a live HTTP request for every document id, to a Vespa endpoint.
- `feed_to_vespa.py::update_endpoint` a: deferred — accepted; it needs a Vespa endpoint, and it was not requested because the 30-unit holding limit was reached
- `reverse-image-search/script/feed.py::run` a: deferred — accepted; it needs a dataset download and a Vespa endpoint, and it was not requested because the 30-unit holding limit was reached
- `reverse-image-search/script/feed.py::run` b: deferred — accepted; it needs a dataset download and a Vespa endpoint, and it was not requested because the 30-unit holding limit was reached
- `reverse-image-search/script/feed.py::run` c: deferred — accepted; it needs a dataset download and a Vespa endpoint, and it was not requested because the 30-unit holding limit was reached
- `commerce-product-ranking/scripts/evaluate.py::main` a: deferred — accepted; it needs a Vespa endpoint and a parquet file not in the repository, and it was not requested because the 30-unit holding limit was reached
- `colbert-long/scripts/evaluate.py::main` a: deferred — accepted; it needs a Vespa endpoint, and it was not requested because the 30-unit holding limit was reached
- `multilingual-search/ext/evaluate.py::search` a: deferred — accepted; it needs a Vespa endpoint, and it was not requested because the 30-unit holding limit was reached
- `visual-retrieval-colpali/src/main.py::get_and_store_sim_maps` a: deferred — accepted; it needs Vespa, and it was not requested because the 30-unit holding limit was reached
- `visual-retrieval-colpali/src/main.py::message_generator` a: deferred — accepted; it calls the Gemini client after its wait loop, and it was not requested because the 30-unit holding limit was reached
- `visual-retrieval-colpali/src/main.py::message_generator` b: deferred — accepted; it calls the Gemini client after its wait loop, and it was not requested because the 30-unit holding limit was reached
- `visual-retrieval-colpali/src/main.py::full_image` a: blocked — the inputs that run here reach only 0% of the function (lines 327-329, 331-333, 335-337 never ran), so they would not measure its real work
- `visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.query_vespa_bm25` a: deferred — accepted; it needs Vespa, and it was not requested because the 30-unit holding limit was reached
- `visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.get_suggestions` a: deferred — accepted; it needs Vespa, and it was not requested because the 30-unit holding limit was reached
