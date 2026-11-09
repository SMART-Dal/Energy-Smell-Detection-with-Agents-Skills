# Energy report — sample-apps @ e2ed22d

105 units listed, 69 with an accepted suspicion · 29 repairs submitted, 63 deferred · 12 confirmed · 3 partial · 2 mixed · 3 negligible · 9 over_limit · 12 applied
Noise floor 1.7% (from: session calibration).

## Applied

### `incremental-search/search-suggestions/count_terms.py::process_docs` — count-terms-docfreq-one-pass

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +39.1%.
The agent measured `partial`; re-measured `confirmed`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| many-docs | 109.04 | 44.89 | +58.8% | 0.2% | yes |
| bigrams | 100.71 | 57.27 | +43.1% | 0.5% | yes |
| trigrams | 107.20 | 50.91 | +52.5% | 1.8% | yes |
| high-duplicates | 60.42 | 59.29 | +1.9% | 1.7% | yes |

### `news/src/python/evaluate.py::predictions` — news-predictions-hit-index

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +99.1%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 19 `url, cert = connect()` (FileNotFoundError); line 103 `train_metrics = calc_metrics(train_impressions_file)` (SystemExit); line 104 `valid_metrics = calc_metrics(valid_impressions_file)` (SystemExit); line 106 `print("Train: " + str(train_metrics))` (NameError); line 107 `print("Valid: " + str(valid_metrics))` (NameError).
Loaded skipping failing top-level statements: line 19 `url, cert = connect()` (FileNotFoundError); line 103 `train_metrics = calc_metrics(train_impressions_file)` (SystemExit); line 104 `valid_metrics = calc_metrics(valid_impressions_file)` (SystemExit); line 106 `print("Train: " + str(train_metrics))` (NameError); line 107 `print("Valid: " + str(valid_metrics))` (NameError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| wide-children | 107.80 | 0.73 | +99.3% | 0.1% | yes |
| tail-matches | 106.81 | 0.58 | +99.5% | 0.0% | yes |
| float-relevance | 108.99 | 0.96 | +99.1% | 0.1% | yes |
| many-children | 111.81 | 1.52 | +98.6% | 0.0% | yes |

### `colbert-long/scripts/convert.py::remove_control_characters` — colbert-control-chars-per-distinct

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +80.1%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 17 `documents = load_dataset('Shitao/MLDR', "corpus-en", spli...` (RuntimeError); line 19 `with open(feed_file, "w") as f:` (NameError).
Loaded skipping failing top-level statements: line 17 `documents = load_dataset('Shitao/MLDR', "corpus-en", spli...` (RuntimeError); line 19 `with open(feed_file, "w") as f:` (NameError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| ascii-prose | 103.07 | 9.91 | +90.4% | 0.9% | yes |
| unicode-mix | 106.14 | 55.38 | +47.8% | 1.8% | yes |
| long-line | 103.37 | 9.94 | +90.4% | 0.4% | yes |
| log-multiline | 107.05 | 8.78 | +91.8% | 0.3% | yes |

### `examples/workshop-ecommerce/preprocess.py::process_users` — preprocess-users-no-iterrows

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +66.6%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| full-150-users | 96.11 | 23.74 | +75.3% | 0.8% | yes |
| limit-200 | 104.82 | 57.56 | +45.1% | 2.4% | yes |
| few-users-heavy | 85.27 | 6.64 | +92.2% | 0.1% | yes |
| many-duplicates | 104.11 | 48.08 | +53.8% | 1.9% | yes |

### `incremental-search/search-suggestions/count_terms.py::count_terms` — count-terms-common-flags-once

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +44.1%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| trigrams-long | 95.56 | 57.99 | +39.3% | 3.6% | yes |
| fourgrams | 105.28 | 56.46 | +46.4% | 2.0% | yes |
| fivegrams | 110.67 | 53.06 | +52.1% | 2.8% | yes |
| all-unique-trigrams | 91.91 | 56.44 | +38.6% | 3.8% | yes |

### `text-video-search/src/python/embedding.py::sample_images` — video-sample-images-select-first

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +71.9%.
Behaviour compared under a relaxed rule: loaded with these uninstalled packages stood in for: clip.
Loaded with uninstalled packages stood in for: clip.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| sample-8-of-80-uint8 | 110.56 | 38.02 | +65.6% | 0.1% | yes |
| sample-30-of-320-mid | 75.75 | 20.14 | +73.4% | 0.3% | yes |
| sample-20-of-200-gray | 105.05 | 33.37 | +68.2% | 0.7% | yes |
| sample-8-of-80-float32 | 106.27 | 21.05 | +80.2% | 1.2% | yes |

### `news/src/python/create_bert_embeddings.py::write_embedding` — bert-write-embedding-one-write

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +40.4%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 15 `data_dir = sys.argv[1]` (IndexError); line 18 `train_news_file = os.path.join(data_dir, "train", "news.t...` (NameError); line 19 `train_embedding_file = os.path.join(data_dir, "train", "n...` (NameError); line 20 `dev_news_file = os.path.join(data_dir, "dev", "news.tsv")` (NameError); line 21 `dev_embedding_file = os.path.join(data_dir, "dev", "news_...` (NameError).
Loaded skipping failing top-level statements: line 15 `data_dir = sys.argv[1]` (IndexError); line 18 `train_news_file = os.path.join(data_dir, "train", "news.t...` (NameError); line 19 `train_embedding_file = os.path.join(data_dir, "train", "n...` (NameError); line 20 `dev_news_file = os.path.join(data_dir, "dev", "news.tsv")` (NameError); line 21 `dev_embedding_file = os.path.join(data_dir, "dev", "news_...` (NameError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| normal-16384 | 91.07 | 53.25 | +41.5% | 2.0% | yes |
| normal-32768 | 90.03 | 52.66 | +41.5% | 2.8% | yes |
| normal-50000 | 83.71 | 50.85 | +39.3% | 2.2% | yes |
| mixed-magnitudes-20000 | 87.27 | 52.99 | +39.3% | 0.9% | yes |

### `news/src/python/convert_embeddings_to_vespa_format.py::convert_user_embeddings` — news-convert-user-embeddings-tolist

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +24.0%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| wide-128d | 70.64 | 54.26 | +23.2% | 4.0% | yes |
| narrow-32d | 77.57 | 57.04 | +26.5% | 5.5% | yes |
| deep-300d | 79.38 | 61.01 | +23.1% | 2.0% | yes |
| bert-768d | 69.19 | 53.17 | +23.2% | 1.4% | yes |

### `visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.float_to_binary_embedding` — vespa-app-packbits-bool

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +18.6%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 10 `from .colpali import SimMapGenerator` (ImportError).
Loaded skipping failing top-level statements: line 10 `from .colpali import SimMapGenerator` (ImportError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| all-positive-1024 | 67.83 | 54.90 | +19.1% | 1.8% | yes |
| all-negative-1024 | 67.90 | 56.05 | +17.5% | 7.3% | yes |
| zeros-mixed-2048 | 69.27 | 55.79 | +19.5% | 0.2% | yes |
| wide-8192 | 68.37 | 55.84 | +18.3% | 0.4% | yes |

### `news/src/python/convert_to_vespa_format.py::convert_file` — news-convert-file-dumps

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +27.6%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large-8k | 110.02 | 72.95 | +33.7% | 2.6% | yes |
| long-text | 69.96 | 56.49 | +19.2% | 0.8% | yes |
| short-text-8k | 94.52 | 58.83 | +37.8% | 3.7% | yes |
| entity-heavy | 79.05 | 63.33 | +19.9% | 2.8% | yes |

### `visual-retrieval-colpali/prepare_feed_deploy.py::float_to_binary_embedding` — prepare-feed-packbits-bool

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +29.5%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 65 `from colpali_engine.models import ColPali, ColPaliProcessor` (ImportError); line 129 `VESPA_CLOUD_SECRET_TOKEN = os.getenv("VESPA_CLOUD_SECRET_...` (EOFError); line 138 `GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or input(` (EOFError); line 146 `gemini_client = genai.Client(api_key=GEMINI_API_KEY)` (NameError); line 150 `device = get_torch_device("auto")` (TypeError); line 151 `print(f"Using device: {device}")` (NameError); line 154 `model = ColPali.from_pretrained(` (NameError); line 160 `processor = ColPaliProcessor.from_pretrained(MODEL_NAME)` (NameError); line 360 `print(f"Max text length: {np.max(text_lengths)}")` (ValueError); line 361 `print(f"Min text length: {np.min(text_lengths)}")` (ValueError); line 461 `pdf_pages[46]["image"]` (IndexError); line 463 `pdf_pages[46]["queries"]` (IndexError); line 574 `embeddings = generate_embeddings(images, model, processor)` (NameError); line 576 `embeddings.shape` (NameError); line 596 `for pdf, embedding in zip(pdf_pages, embeddings):` (NameError); line 972 `VESPA_TEAM_API_KEY = os.getenv("VESPA_TEAM_API_KEY") or i...` (EOFError); line 977 `vespa_cloud = VespaCloud(` (NameError); line 985 `vespa_cloud.deploy()` (NameError); line 988 `endpoint_url = vespa_cloud.get_token_endpoint()` (NameError); line 989 `print(f"Application deployed. Token endpoint URL: {endpoi...` (NameError); line 1000 `app = Vespa(url=endpoint_url, vespa_cloud_secret_token=VE...` (NameError); line 1001 `app.get_application_status()` (NameError); line 1013 `app.feed_async_iterable(vespa_feed, schema=VESPA_SCHEMA_N...` (NameError).
Loaded skipping failing top-level statements: line 65 `from colpali_engine.models import ColPali, ColPaliProcessor` (ImportError); line 129 `VESPA_CLOUD_SECRET_TOKEN = os.getenv("VESPA_CLOUD_SECRET_...` (EOFError); line 138 `GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or input(` (EOFError); line 146 `gemini_client = genai.Client(api_key=GEMINI_API_KEY)` (NameError); line 150 `device = get_torch_device("auto")` (TypeError); line 151 `print(f"Using device: {device}")` (NameError); line 154 `model = ColPali.from_pretrained(` (NameError); line 160 `processor = ColPaliProcessor.from_pretrained(MODEL_NAME)` (NameError); line 360 `print(f"Max text length: {np.max(text_lengths)}")` (ValueError); line 361 `print(f"Min text length: {np.min(text_lengths)}")` (ValueError); line 461 `pdf_pages[46]["image"]` (IndexError); line 463 `pdf_pages[46]["queries"]` (IndexError); line 574 `embeddings = generate_embeddings(images, model, processor)` (NameError); line 576 `embeddings.shape` (NameError); line 596 `for pdf, embedding in zip(pdf_pages, embeddings):` (NameError); line 972 `VESPA_TEAM_API_KEY = os.getenv("VESPA_TEAM_API_KEY") or i...` (EOFError); line 977 `vespa_cloud = VespaCloud(` (NameError); line 985 `vespa_cloud.deploy()` (NameError); line 988 `endpoint_url = vespa_cloud.get_token_endpoint()` (NameError); line 989 `print(f"Application deployed. Token endpoint URL: {endpoi...` (NameError); line 1000 `app = Vespa(url=endpoint_url, vespa_cloud_secret_token=VE...` (NameError); line 1001 `app.get_application_status()` (NameError); line 1013 `app.feed_async_iterable(vespa_feed, schema=VESPA_SCHEMA_N...` (NameError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| colpali-large-2048x128 | 88.41 | 62.33 | +29.5% | 2.9% | yes |
| dim-64-3000-patches | 92.40 | 62.82 | +32.0% | 1.9% | yes |
| dim-1024-900-patches | 86.12 | 68.04 | +21.0% | 20.3% | yes |
| many-patches-4096x128 | 83.70 | 54.08 | +35.4% | 20.5% | yes |

### `rag-blueprint/eval/evaluate_match_phase.py::match_semantic_query_fn` — match-semantic-yql-once

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +91.9%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 89 `for evaluator_name, query_fn in [` (RetryError).
Loaded skipping failing top-level statements: line 89 `for evaluator_name, query_fn in [` (RetryError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| very-long-query | 92.07 | 12.60 | +86.3% | 0.9% | yes |
| multi-sentence-query | 90.61 | 6.69 | +92.6% | 0.1% | yes |
| unicode-query | 93.35 | 4.79 | +94.9% | 0.1% | yes |
| numeric-query-top1000 | 92.96 | 5.60 | +94.0% | 0.2% | yes |

## Measured, not confirmed

### `feed-split.py::split_text` — feed-split-split-text-join

**negligible** — no case moved more than the noise: the largest reading was +3.2% +-5.5% on 'lists-and-links', against a clean 1.7% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: +0.8%.
Behaviour compared under a relaxed rule: loaded with these uninstalled packages stood in for: tiktoken.
Loaded with uninstalled packages stood in for: tiktoken.
Measured twice: the first measurement came out `partial` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| lists-and-links | 65.93 | 63.83 | +3.2% | 5.5% | no: pairs disagree |
| top-level-tables | 60.10 | 59.44 | +1.1% | 4.0% | no: pairs disagree |
| tables-inside-divs | 59.82 | 59.99 | -0.3% | 1.1% | no: pairs disagree |
| mixed-large | 58.06 | 58.54 | -0.8% | 2.4% | no: pairs disagree |

### `news/src/python/train_cold_start.py::write_embeddings` — cold-start-write-embeddings-tolist-once

**partial** — saves energy on 1 of 4 inputs ('narrow'; best 6.3% +-1.0% on 'narrow'), and no saving that can be told from noise on the rest: 'large' +1.8% +-6.3% (its pairs disagree too much to tell); 'wide' +1.2% +-3.4% (its pairs disagree too much to tell); 'many' +1.3% +-7.6% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +2.7%.
Measured twice: the first measurement came out `partial` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large | 67.18 | 65.94 | +1.8% | 6.3% | no: pairs disagree |
| wide | 64.72 | 63.93 | +1.2% | 3.4% | no: pairs disagree |
| narrow | 67.31 | 63.07 | +6.3% | 1.0% | yes |
| many | 71.34 | 70.41 | +1.3% | 7.5% | no: pairs disagree |

### `examples/workshop-ecommerce/preprocess.py::process_orders` — preprocess-orders-no-iterrows

**partial** — saves energy on 1 of 4 inputs ('mixed-three-sets'; best 7.1% +-6.6% on 'mixed-three-sets'), and no saving that can be told from noise on the rest: 'prior-limit-10' +0.7% +-2.6% (its pairs disagree too much to tell); 'prior-and-train' +0.5% +-0.7% (its pairs disagree too much to tell); 'orphan-orders' -0.5% +-10.0% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +2.0%.
Measured twice: the first measurement came out `partial` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| prior-limit-10 | 64.00 | 63.54 | +0.7% | 2.5% | no: pairs disagree |
| prior-and-train | 86.67 | 86.22 | +0.5% | 0.7% | no: pairs disagree |
| mixed-three-sets | 59.49 | 55.25 | +7.1% | 6.6% | yes |
| orphan-orders | 58.84 | 59.10 | -0.4% | 10.0% | no: pairs disagree |

### `incremental-search/search-suggestions/count_terms.py::process_doc` — count-terms-merge-without-key-lists

**partial** — saves energy on 1 of 4 inputs ('tl3-large'; best 3.0% +-2.8% on 'tl3-large'), and no saving that can be told from noise on the rest: 'tl4-huge' +2.4% +-4.4% (its pairs disagree too much to tell); 'common-words' +1.5% +-3.5% (its pairs disagree too much to tell); 'repetitive' +0.5% +-4.7% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +1.9%.
Measured twice: the first measurement came out `negligible` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| tl3-large | 59.79 | 57.97 | +3.0% | 2.8% | yes |
| tl4-huge | 60.27 | 58.83 | +2.4% | 4.4% | no: pairs disagree |
| common-words | 56.33 | 55.49 | +1.5% | 3.5% | no: pairs disagree |
| repetitive | 55.41 | 55.13 | +0.5% | 4.7% | no: pairs disagree |

### `news/src/python/convert_embeddings_to_vespa_format.py::read_embeddings` — news-read-embeddings-fromstring

**mixed** — a trade-off, not a fix: 6.7% saved on 'mid-64d-1500' but 33.6% lost on 'tiny-2d-20000', both clearing the 1.7% noise floor. Whether it pays depends on which input the code actually sees, so the report must name both.
Mean saving across its cases: -13.2%.
The agent measured `regressed`; re-measured `mixed`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| short-8d-8000 | 55.12 | 63.74 | -15.6% | 4.2% | yes |
| duplicate-ids-16d-3000 | 53.48 | 58.93 | -10.2% | 0.7% | yes |
| mid-64d-1500 | 57.14 | 53.30 | +6.7% | 0.3% | yes |
| tiny-2d-20000 | 55.18 | 73.71 | -33.6% | 2.5% | yes |

### `use-case-shopping/create_suggestions.py::filter` — suggestions-filter-one-regex

**mixed** — a trade-off, not a fix: 28.7% saved on 'clean-40-full-scan' but 13.5% lost on 'numeric-191', both clearing the 1.7% noise floor. Whether it pays depends on which input the code actually sees, so the report must name both.
Mean saving across its cases: +8.9%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 10 `nlp = spacy.load("en_core_web_sm")` (OSError); line 79 `with open(sys.argv[1]) as fp:` (IndexError); line 97 `with open(sys.argv[1]) as fp:` (IndexError).
Loaded skipping failing top-level statements: line 10 `nlp = spacy.load("en_core_web_sm")` (OSError); line 79 `with open(sys.argv[1]) as fp:` (IndexError); line 97 `with open(sys.argv[1]) as fp:` (IndexError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| clean-64-full-scan | 47.58 | 40.21 | +15.5% | 1.3% | yes |
| clean-40-full-scan | 56.41 | 40.18 | +28.8% | 10.7% | yes |
| hit-late-filter | 42.28 | 40.31 | +4.7% | 1.8% | yes |
| numeric-191 | 38.05 | 43.19 | -13.5% | 0.8% | yes |

### `news/src/python/mind_data.py::MindData.sample_valid_data` — mind-valid-filter-first

**negligible** — no case moved more than the noise: the largest reading was -1.4% +-3.9% on 'many-short-low-prob', against a clean 1.7% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: -0.7%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| typical-valid | 56.92 | 56.97 | -0.1% | 0.6% | no: pairs disagree |
| many-short-partial | 57.21 | 57.63 | -0.7% | 1.3% | no: pairs disagree |
| train-impressions | 56.83 | 57.07 | -0.4% | 2.8% | no: pairs disagree |
| many-short-low-prob | 57.17 | 57.95 | -1.4% | 3.9% | no: pairs disagree |

### `examples/workshop-ecommerce/preprocess.py::process_users` — preprocess-users-usecols

**negligible** — no case moved more than the noise: the largest reading was +0.6% +-0.8% on 'many-duplicates', against a clean 1.7% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: +0.2%.
Measured twice: the first measurement came out `negligible` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| full-150-users | 73.30 | 73.30 | +0.0% | 4.0% | no: pairs disagree |
| limit-200 | 63.88 | 63.60 | +0.4% | 1.5% | no: pairs disagree |
| few-users-heavy | 57.04 | 57.07 | -0.0% | 0.3% | no: pairs disagree |
| many-duplicates | 65.13 | 64.75 | +0.6% | 0.8% | no: pairs disagree |

## Not measured

### `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator._prepare_similarity_map_tensor` — colpali-simmap-single-scatter

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures
The agent measured `error`; re-measured `over_limit`.

### `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.gen_similarity_maps` — colpali-gen-simmaps-size-only

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures
The agent measured `no_inputs`; re-measured `over_limit`.

### `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator._blend_image` — colpali-blend-colormap-bytes

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures
The agent measured `no_inputs`; re-measured `over_limit`.

### `visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.format_q_embs` — vespa-app-format-q-embs-tolist-once

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures
The agent measured `not_equivalent`; re-measured `over_limit`.

### `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.should_filter_token` — colpali-filter-token-compiled

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures
The agent measured `error`; re-measured `over_limit`.

### `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.gen_similarity_maps` — colpali-gen-simmaps-no-copy

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures
The agent measured `no_inputs`; re-measured `over_limit`.

### `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator._prepare_similarity_map_tensor` — colpali-simmap-hoist-seq-length

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures
The agent measured `error`; re-measured `over_limit`.

### `visual-retrieval-colpali/src/backend/stopwords.py::filter` — stopwords-tokenizer-only

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures
The agent measured `not_equivalent`; re-measured `over_limit`.

### `rag-blueprint/eval/train_logistic_regression.py::perform_cross_validation` — logreg-stats-without-describe

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures
The agent measured `not_equivalent`; re-measured `over_limit`.

## Detected, not measured

Accepted findings with no measurement: deferred beyond the repairs chosen for measurement, or blocked.

- `incremental-search/search-suggestions/count_terms.py::process_docs` b: deferred — outside the 20 repairs measured: verify.py reported over_limit for submission 'count-terms-drop-unused-total' once 20 repairs had verdicts
- `incremental-search/search-suggestions/count_terms.py::write_json_file` a: deferred — outside the 20 repairs measured; no inputs requested
- `incremental-search/search-suggestions/accepted_words.py::process_docs` a: deferred — outside the 20 repairs measured: verify.py reported over_limit for submission 'accepted-words-set-update' once 20 repairs had verdicts
- `news/src/python/mind_data.py::MindData.sample_valid_data` b: deferred — outside the 20 repairs measured: verify.py reported over_limit for submission 'mind-valid-sum-once' once 20 repairs had verdicts
- `news/src/python/mind_data.py::MindData.add_impressions` a: deferred — outside the 20 repairs measured; no inputs requested
- `news/src/python/train_cold_start.py::save_embeddings` a: deferred — outside the 20 repairs measured; no inputs requested
- `news/src/python/train_cold_start.py::train_model` a: deferred — outside the 20 repairs measured; no inputs requested
- `news/src/python/train_cold_start.py::read_bert_embeddings_from_file` a: deferred — outside the 20 repairs measured; no inputs requested
- `news/src/python/train_mf.py::write_embeddings` a: deferred — outside the 20 repairs measured; no inputs requested
- `news/src/python/train_mf.py::save_embeddings` a: deferred — outside the 20 repairs measured; no inputs requested
- `news/src/python/create_bert_embeddings.py::create_embeddings` a: deferred — outside the 20 repairs measured; no inputs requested
- `news/src/python/create_bert_embeddings.py::create_embeddings` b: deferred — outside the 20 repairs measured; no inputs requested
- `news/src/python/create_bert_embeddings.py::create_embeddings` c: deferred — outside the 20 repairs measured; no inputs requested
- `news/src/python/convert_embeddings_to_vespa_format.py::convert_news_embeddings` a: deferred — outside the 20 repairs measured; no inputs requested
- `news/src/python/convert_to_vespa_format.py::read_impressions_file` a: deferred — outside the 20 repairs measured; no inputs requested
- `news/src/python/create_category_ctrs.py::read_impressions_file` a: deferred — outside the 20 repairs measured; no inputs requested
- `news/src/python/create_category_ctrs.py::read_content_file` a: deferred — outside the 20 repairs measured; no inputs requested
- `news/src/python/vespa_client.py::query_user_embedding` a: deferred — outside the 20 repairs measured; no inputs requested
- `text-search/python/collect_training_data.py::build_dataset` a: deferred — outside the 20 repairs measured; no inputs requested
- `multilingual-search/ext/evaluate.py::search` a: deferred — outside the 20 repairs measured; no inputs requested
- `rag-blueprint/eval/train_lightgbm.py::perform_cross_validation` b: deferred — outside the 20 repairs measured; no inputs requested
- `rag-blueprint/eval/train_lightgbm.py::perform_cross_validation` c: deferred — outside the 20 repairs measured; no inputs requested
- `rag-blueprint/eval/train_lightgbm.py::perform_cross_validation` d: deferred — outside the 20 repairs measured; no inputs requested
- `rag-blueprint/eval/train_logistic_regression.py::perform_cross_validation` a: deferred — first version ('logreg-stats-without-describe') came back not_equivalent: on 'empty-file' before raised KeyError, after raised ValueError; not re-measured because all 20 places were then used
- `rag-blueprint/eval/train_logistic_regression.py::perform_cross_validation` b: deferred — outside the 20 repairs measured: verify.py reported over_limit for submission 'logreg-predict-from-proba' once 20 repairs had verdicts
- `examples/in-context-learning/categorize_group.py::inference` a: deferred — outside the 20 repairs measured; no inputs requested
- `examples/in-context-learning/categorize_group.py::inference` b: deferred — outside the 20 repairs measured; no inputs requested
- `examples/in-context-learning/categorize_group.py::get_label` a: deferred — outside the 20 repairs measured; no inputs requested
- `examples/workshop-ecommerce/preprocess.py::process_orders` b: deferred — outside the 20 repairs measured: verify.py reported over_limit for submission 'preprocess-orders-no-copy' once 20 repairs had verdicts
- `examples/workshop-ecommerce/preprocess.py::process_products` a: deferred — outside the 20 repairs measured; no inputs requested
- `examples/workshop-ecommerce/preprocess.py::process_products` b: deferred — outside the 20 repairs measured; no inputs requested
- `examples/ecommerce-user-preferences/webapp/app.py::load_system_prompt` a: deferred — outside the 20 repairs measured; no inputs requested
- `examples/ecommerce-user-preferences/webapp/app.py::get_wikipedia_image` a: deferred — outside the 20 repairs measured; no inputs requested
- `commerce-product-ranking/scripts/evaluate.py::main` a: deferred — outside the 20 repairs measured; no inputs requested
- `commerce-product-ranking/scripts/evaluate.py::main` b: deferred — outside the 20 repairs measured; no inputs requested
- `commerce-product-ranking/scripts/evaluate.py::main` c: deferred — outside the 20 repairs measured; no inputs requested
- `use-case-shopping/convert_meta.py::process` a: deferred — outside the 20 repairs measured; no inputs requested
- `use-case-shopping/create_suggestions.py::filter_content` a: deferred — outside the 20 repairs measured: verify.py reported over_limit for submission 'suggestions-filter-content-startswith-tuple' once 20 repairs had verdicts
- `incremental-search/search-as-you-type/feed_to_vespa.py::update_endpoint` a: deferred — outside the 20 repairs measured; no inputs requested
- `incremental-search/search-as-you-type/feed_to_vespa.py::update_endpoint` b: deferred — outside the 20 repairs measured; no inputs requested
- `feed_to_vespa.py::update_endpoint` a: deferred — outside the 20 repairs measured; no inputs requested
- `feed_to_vespa.py::update_endpoint` b: deferred — outside the 20 repairs measured; no inputs requested
- `feed_to_vespa.py::get_feed_docids` a: deferred — outside the 20 repairs measured; no inputs requested
- `feed-split.py::xml_fixup` b: deferred — outside the 20 repairs measured; no inputs requested
- `feed-split.py::what_language` a: deferred — outside the 20 repairs measured: verify.py reported over_limit for submission 'feed-split-what-language-text-once' once 20 repairs had verdicts
- `test/test.py::parse_file` a: deferred — outside the 20 repairs measured; no inputs requested
- `reverse-image-search/script/feed.py::run` a: deferred — outside the 20 repairs measured; no inputs requested
- `reverse-image-search/script/feed.py::run` b: deferred — outside the 20 repairs measured; no inputs requested
- `reverse-image-search/script/search.py::_search` a: deferred — outside the 20 repairs measured; no inputs requested
- `text-video-search/src/python/embedding.py::extract_images` a: deferred — outside the 20 repairs measured; no inputs requested
- `text-video-search/src/python/embedding.py::VideoFeedDataset.__getitem__` b: deferred — outside the 20 repairs measured; no inputs requested
- `text-video-search/src/python/embedding.py::compute_and_send_video_embeddings` a: deferred — outside the 20 repairs measured; no inputs requested
- `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.gen_similarity_maps` a: blocked — inputs.py: it cannot run here: the function under test is a method of `SimMapGenerator`, whose `__init__` calls `load_model()` to download the ColPali model (`vidore/colpali-v1.2`) and processor from the HuggingFace Hub, so the instance the repository's own caller builds cannot be constructed without network access
- `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.gen_similarity_maps` b: blocked — inputs.py: it cannot run here: the function under test is a method of `SimMapGenerator`, whose `__init__` calls `load_model()` to download the ColPali model (`vidore/colpali-v1.2`) and processor from the HuggingFace Hub, so the instance the repository's own caller builds cannot be constructed without network access
- `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator._prepare_similarity_map_tensor` a: blocked — verify.py: the repository's own module does not load here, even skipping the top-level statements that fail: AttributeError: SimMapGenerator is not defined here: loading the module skipped line 19 `class SimMapGenerator:` (TypeError), with stand-ins for colpali_engine (the installed colpali_engine has no `ColPali`)
- `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator._prepare_similarity_map_tensor` b: blocked — verify.py: the repository's own module does not load here, even skipping the top-level statements that fail: AttributeError: SimMapGenerator is not defined here: loading the module skipped line 19 `class SimMapGenerator:` (TypeError), with stand-ins for colpali_engine (the installed colpali_engine has no `ColPali`)
- `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator._blend_image` a: blocked — inputs.py: the unit's module does not load here: AttributeError: SimMapGenerator is not defined here: loading the module skipped line 19 `class SimMapGenerator:` (TypeError), with stand-ins for colpali_engine
- `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.should_filter_token` a: blocked — verify.py: the repository's own module does not load here, even skipping the top-level statements that fail: AttributeError: SimMapGenerator is not defined here: loading the module skipped line 19 `class SimMapGenerator:` (TypeError), with stand-ins for colpali_engine (the installed colpali_engine has no `ColPali`)
- `visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.format_q_embs` a: deferred — first version ('vespa-app-format-q-embs-tolist-once') came back not_equivalent: different return value on 'single-row'; not re-measured because all 20 places were then used
- `visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.format_query_results` a: deferred — outside the 20 repairs measured; no inputs requested
- `visual-retrieval-colpali/src/main.py::message_generator` a: deferred — outside the 20 repairs measured; no inputs requested
- `visual-retrieval-colpali/src/main.py::message_generator` b: deferred — outside the 20 repairs measured; no inputs requested
- `visual-retrieval-colpali/src/main.py::get_and_store_sim_maps` a: deferred — outside the 20 repairs measured; no inputs requested
- `visual-retrieval-colpali/src/main.py::get_and_store_sim_maps` b: deferred — outside the 20 repairs measured; no inputs requested
- `visual-retrieval-colpali/src/backend/stopwords.py::filter` a: deferred — first version ('stopwords-tokenizer-only') came back not_equivalent: on 'none' before raised ValueError, after raised TypeError; not re-measured because all 20 places were then used
- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/vespa_module/vespa_retriever.py::create_conditions` a: deferred — outside the 20 repairs measured: verify.py reported over_limit for submission 'create-conditions-operators-once' once 20 repairs had verdicts
- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::subgraph_GenerateKeywords` a: deferred — outside the 20 repairs measured; no inputs requested
- `examples/google-cloud/cloud-functions/python/main.py::get_blobs` a: deferred — outside the 20 repairs measured; no inputs requested
- `examples/model-exporting/export_hf_model_from_hf.py::export_model` b: deferred — outside the 20 repairs measured; no inputs requested
