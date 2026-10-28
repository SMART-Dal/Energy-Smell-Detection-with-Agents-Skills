# Energy report — sample-apps @ e2ed22d

54 units listed, 39 with an accepted suspicion · 30 repairs submitted, 23 deferred · 10 confirmed · 3 partial · 1 regressed · 6 negligible · 10 over_limit · 10 applied
Noise floor 2.7% (from: session calibration).

## Applied

### `news/src/python/evaluate.py::predictions` — predictions-dict

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +99.1%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 19 `url, cert = connect()` (FileNotFoundError); line 103 `train_metrics = calc_metrics(train_impressions_file)` (SystemExit); line 104 `valid_metrics = calc_metrics(valid_impressions_file)` (SystemExit); line 106 `print("Train: " + str(train_metrics))` (NameError); line 107 `print("Valid: " + str(valid_metrics))` (NameError).
Loaded skipping failing top-level statements: line 19 `url, cert = connect()` (FileNotFoundError); line 103 `train_metrics = calc_metrics(train_impressions_file)` (SystemExit); line 104 `valid_metrics = calc_metrics(valid_impressions_file)` (SystemExit); line 106 `print("Train: " + str(train_metrics))` (NameError); line 107 `print("Valid: " + str(valid_metrics))` (NameError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| wide-children | 108.13 | 0.76 | +99.3% | 0.0% | yes |
| tail-matches | 111.29 | 0.61 | +99.5% | 0.0% | yes |
| float-relevance | 111.59 | 1.02 | +99.1% | 0.0% | yes |
| many-children | 113.64 | 1.56 | +98.6% | 0.1% | yes |

### `colbert-long/scripts/convert.py::remove_control_characters` — ctrl-translate

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +92.4%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 17 `documents = load_dataset('Shitao/MLDR', "corpus-en", spli...` (RuntimeError); line 19 `with open(feed_file, "w") as f:` (NameError).
Loaded skipping failing top-level statements: line 17 `documents = load_dataset('Shitao/MLDR', "corpus-en", spli...` (RuntimeError); line 19 `with open(feed_file, "w") as f:` (NameError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| ascii-prose | 110.16 | 0.74 | +99.3% | 0.1% | yes |
| unicode-mix | 105.32 | 29.79 | +71.7% | 0.3% | yes |
| long-line | 100.38 | 0.67 | +99.3% | 0.0% | yes |
| log-multiline | 102.67 | 0.87 | +99.2% | 0.1% | yes |

### `incremental-search/search-suggestions/count_terms.py::count_terms` — terms-window-flags

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +52.3%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| trigrams-long | 103.48 | 54.54 | +47.3% | 0.8% | yes |
| fourgrams | 105.63 | 48.88 | +53.7% | 0.4% | yes |
| fivegrams | 106.03 | 39.16 | +63.1% | 0.7% | yes |
| all-unique-trigrams | 99.65 | 54.87 | +44.9% | 0.6% | yes |

### `news/src/python/create_bert_embeddings.py::write_embedding` — bert-write-join

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +40.7%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 15 `data_dir = sys.argv[1]` (IndexError); line 18 `train_news_file = os.path.join(data_dir, "train", "news.t...` (NameError); line 19 `train_embedding_file = os.path.join(data_dir, "train", "n...` (NameError); line 20 `dev_news_file = os.path.join(data_dir, "dev", "news.tsv")` (NameError); line 21 `dev_embedding_file = os.path.join(data_dir, "dev", "news_...` (NameError).
Loaded skipping failing top-level statements: line 15 `data_dir = sys.argv[1]` (IndexError); line 18 `train_news_file = os.path.join(data_dir, "train", "news.t...` (NameError); line 19 `train_embedding_file = os.path.join(data_dir, "train", "n...` (NameError); line 20 `dev_news_file = os.path.join(data_dir, "dev", "news.tsv")` (NameError); line 21 `dev_embedding_file = os.path.join(data_dir, "dev", "news_...` (NameError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| normal-16384 | 94.28 | 55.07 | +41.6% | 3.7% | yes |
| normal-32768 | 94.44 | 55.61 | +41.1% | 0.6% | yes |
| normal-50000 | 89.82 | 54.48 | +39.3% | 1.2% | yes |
| mixed-magnitudes-20000 | 90.90 | 53.68 | +41.0% | 2.3% | yes |

### `news/src/python/convert_to_vespa_format.py::convert_file` — convert-file-dumps

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +26.6%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large-8k | 109.59 | 73.94 | +32.5% | 4.2% | yes |
| long-text | 73.73 | 60.67 | +17.7% | 1.6% | yes |
| short-text-8k | 100.18 | 64.35 | +35.8% | 0.8% | yes |
| entity-heavy | 79.14 | 62.96 | +20.4% | 1.4% | yes |

### `news/src/python/convert_embeddings_to_vespa_format.py::convert_user_embeddings` — user-emb-tolist

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +13.4%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| wide-128d | 68.10 | 58.76 | +13.7% | 1.2% | yes |
| narrow-32d | 74.71 | 62.41 | +16.5% | 1.3% | yes |
| deep-300d | 75.82 | 66.76 | +12.0% | 2.7% | yes |
| bert-768d | 65.70 | 58.27 | +11.3% | 1.2% | yes |

### `text-video-search/src/python/embedding.py::sample_images` — sample-images-select

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +72.9%.
Behaviour compared under a relaxed rule: loaded with these uninstalled packages stood in for: clip.
Loaded with uninstalled packages stood in for: clip.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| sample-8-of-80-uint8 | 112.92 | 38.06 | +66.3% | 0.3% | yes |
| sample-30-of-320-mid | 114.41 | 28.48 | +75.1% | 0.2% | yes |
| sample-20-of-200-gray | 112.35 | 34.06 | +69.7% | 0.3% | yes |
| sample-8-of-80-float32 | 113.77 | 21.98 | +80.7% | 0.1% | yes |

### `billion-scale-vector-search/app/src/main/python/recall.py::compute_recall_with_distance_ties` — recall-vectorised

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +70.9%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| count-100-tie-5k | 112.38 | 35.66 | +68.3% | 1.7% | yes |
| tie-to-end-20k | 109.75 | 34.05 | +69.0% | 0.3% | yes |
| tie-to-end-50k | 109.53 | 28.75 | +73.8% | 0.4% | yes |
| partial-tie-100k | 103.09 | 28.04 | +72.8% | 0.1% | yes |

### `visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.float_to_binary_embedding` — vespa-packbits-bool

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +18.8%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 10 `from .colpali import SimMapGenerator` (ImportError).
Loaded skipping failing top-level statements: line 10 `from .colpali import SimMapGenerator` (ImportError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| all-positive-1024 | 67.22 | 54.40 | +19.1% | 4.3% | yes |
| all-negative-1024 | 68.63 | 54.85 | +20.1% | 1.1% | yes |
| zeros-mixed-2048 | 68.13 | 55.79 | +18.1% | 5.4% | yes |
| wide-8192 | 69.67 | 57.31 | +17.7% | 0.8% | yes |

### `visual-retrieval-colpali/prepare_feed_deploy.py::float_to_binary_embedding` — feed-packbits-bool

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +27.7%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 65 `from colpali_engine.models import ColPali, ColPaliProcessor` (ImportError); line 129 `VESPA_CLOUD_SECRET_TOKEN = os.getenv("VESPA_CLOUD_SECRET_...` (EOFError); line 138 `GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or input(` (EOFError); line 146 `gemini_client = genai.Client(api_key=GEMINI_API_KEY)` (NameError); line 150 `device = get_torch_device("auto")` (TypeError); line 151 `print(f"Using device: {device}")` (NameError); line 154 `model = ColPali.from_pretrained(` (NameError); line 160 `processor = ColPaliProcessor.from_pretrained(MODEL_NAME)` (NameError); line 360 `print(f"Max text length: {np.max(text_lengths)}")` (ValueError); line 361 `print(f"Min text length: {np.min(text_lengths)}")` (ValueError); line 461 `pdf_pages[46]["image"]` (IndexError); line 463 `pdf_pages[46]["queries"]` (IndexError); line 574 `embeddings = generate_embeddings(images, model, processor)` (NameError); line 576 `embeddings.shape` (NameError); line 596 `for pdf, embedding in zip(pdf_pages, embeddings):` (NameError); line 972 `VESPA_TEAM_API_KEY = os.getenv("VESPA_TEAM_API_KEY") or i...` (EOFError); line 977 `vespa_cloud = VespaCloud(` (NameError); line 985 `vespa_cloud.deploy()` (NameError); line 988 `endpoint_url = vespa_cloud.get_token_endpoint()` (NameError); line 989 `print(f"Application deployed. Token endpoint URL: {endpoi...` (NameError); line 1000 `app = Vespa(url=endpoint_url, vespa_cloud_secret_token=VE...` (NameError); line 1001 `app.get_application_status()` (NameError); line 1013 `app.feed_async_iterable(vespa_feed, schema=VESPA_SCHEMA_N...` (NameError).
Loaded skipping failing top-level statements: line 65 `from colpali_engine.models import ColPali, ColPaliProcessor` (ImportError); line 129 `VESPA_CLOUD_SECRET_TOKEN = os.getenv("VESPA_CLOUD_SECRET_...` (EOFError); line 138 `GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or input(` (EOFError); line 146 `gemini_client = genai.Client(api_key=GEMINI_API_KEY)` (NameError); line 150 `device = get_torch_device("auto")` (TypeError); line 151 `print(f"Using device: {device}")` (NameError); line 154 `model = ColPali.from_pretrained(` (NameError); line 160 `processor = ColPaliProcessor.from_pretrained(MODEL_NAME)` (NameError); line 360 `print(f"Max text length: {np.max(text_lengths)}")` (ValueError); line 361 `print(f"Min text length: {np.min(text_lengths)}")` (ValueError); line 461 `pdf_pages[46]["image"]` (IndexError); line 463 `pdf_pages[46]["queries"]` (IndexError); line 574 `embeddings = generate_embeddings(images, model, processor)` (NameError); line 576 `embeddings.shape` (NameError); line 596 `for pdf, embedding in zip(pdf_pages, embeddings):` (NameError); line 972 `VESPA_TEAM_API_KEY = os.getenv("VESPA_TEAM_API_KEY") or i...` (EOFError); line 977 `vespa_cloud = VespaCloud(` (NameError); line 985 `vespa_cloud.deploy()` (NameError); line 988 `endpoint_url = vespa_cloud.get_token_endpoint()` (NameError); line 989 `print(f"Application deployed. Token endpoint URL: {endpoi...` (NameError); line 1000 `app = Vespa(url=endpoint_url, vespa_cloud_secret_token=VE...` (NameError); line 1001 `app.get_application_status()` (NameError); line 1013 `app.feed_async_iterable(vespa_feed, schema=VESPA_SCHEMA_N...` (NameError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| colpali-large-2048x128 | 77.44 | 54.71 | +29.3% | 0.9% | yes |
| dim-64-3000-patches | 78.92 | 53.70 | +32.0% | 0.7% | yes |
| dim-1024-900-patches | 71.94 | 57.10 | +20.6% | 0.8% | yes |
| many-patches-4096x128 | 75.79 | 54.03 | +28.7% | 0.4% | yes |

## Measured, not confirmed

### `incremental-search/search-suggestions/count_terms.py::process_docs` — terms-docs-count

**partial** — saves energy on 3 of 4 inputs ('many-docs', 'bigrams', 'trigrams'; best 57.3% +-2.6% on 'many-docs'), and no saving that can be told from noise on the rest: 'high-duplicates' -0.0% +-0.8% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +38.6%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| many-docs | 105.62 | 45.03 | +57.4% | 2.6% | yes |
| bigrams | 99.32 | 55.37 | +44.3% | 1.8% | yes |
| trigrams | 106.42 | 50.07 | +52.9% | 0.9% | yes |
| high-duplicates | 56.21 | 56.21 | -0.0% | 0.8% | no: pairs disagree |

### `text-search/python/extract-msmarco.py::extract_documents` — msmarco-tell

**partial** — saves energy on 2 of 4 inputs ('unicode-1500', 'mixed-3000'; best 6.8% +-2.6% on 'unicode-1500'), and no saving that can be told from noise on the rest: 'long-800' -0.0% +-2.0% (its pairs disagree too much to tell); 'long-1200' +0.3% +-0.4% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +2.6%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| unicode-1500 | 63.09 | 58.81 | +6.8% | 2.6% | yes |
| long-800 | 63.52 | 63.55 | -0.0% | 2.0% | no: pairs disagree |
| mixed-3000 | 62.97 | 60.85 | +3.4% | 1.2% | yes |
| long-1200 | 61.86 | 61.68 | +0.3% | 0.4% | no: pairs disagree |

### `news/src/python/mind_data.py::MindData.sample_valid_data` — valid-filter-first

**negligible** — no case moved more than the noise: the largest reading was +0.2% +-0.6% on 'many-short-low-prob', against a clean 2.7% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: +0.1%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| typical-valid | 58.55 | 58.60 | -0.1% | 2.9% | no: pairs disagree |
| many-short-partial | 59.21 | 59.13 | +0.1% | 0.3% | no: pairs disagree |
| train-impressions | 60.11 | 60.08 | +0.1% | 0.1% | no: pairs disagree |
| many-short-low-prob | 60.63 | 60.52 | +0.2% | 0.6% | no: pairs disagree |

### `news/src/python/train_cold_start.py::write_embeddings` — write-emb-tolist

**partial** — saves energy on 3 of 4 inputs ('large', 'narrow', 'many'; best 6.2% +-1.6% on 'narrow'), and no saving that can be told from noise on the rest: 'wide' +1.7% +-1.2% (within the 2.7% noise floor). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +4.2%.
Measured twice: the first measurement came out `partial` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large | 60.59 | 58.64 | +3.2% | 2.2% | yes |
| wide | 60.90 | 59.89 | +1.7% | 1.2% | no: within the floor |
| narrow | 61.40 | 57.59 | +6.2% | 1.6% | yes |
| many | 67.04 | 63.24 | +5.7% | 1.4% | yes |

### `feed-split.py::split_text` — split-text-join

**negligible** — no case moved more than the noise: the largest reading was +0.7% +-1.7% on 'mixed-large', against a clean 2.7% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: +0.3%.
Behaviour compared under a relaxed rule: loaded with these uninstalled packages stood in for: tiktoken.
Loaded with uninstalled packages stood in for: tiktoken.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| lists-and-links | 66.90 | 66.75 | +0.2% | 0.8% | no: pairs disagree |
| top-level-tables | 62.64 | 62.41 | +0.4% | 1.1% | no: pairs disagree |
| tables-inside-divs | 61.28 | 61.34 | -0.1% | 1.6% | no: pairs disagree |
| mixed-large | 59.73 | 59.34 | +0.7% | 1.7% | no: pairs disagree |

### `incremental-search/search-suggestions/count_terms.py::process_doc` — terms-merge-counts

**negligible** — no case moved more than the noise: the largest reading was +2.8% +-3.6% on 'tl4-huge', against a clean 2.7% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: +1.2%.
The agent measured `partial`; re-measured `negligible`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| tl3-large | 61.72 | 60.00 | +2.8% | 3.8% | no: pairs disagree |
| tl4-huge | 62.38 | 60.61 | +2.8% | 3.6% | no: pairs disagree |
| common-words | 60.03 | 59.95 | +0.1% | 1.7% | no: pairs disagree |
| repetitive | 54.49 | 55.10 | -1.1% | 3.5% | no: pairs disagree |

### `use-case-shopping/create_suggestions.py::filter` — suggest-filter-any

**regressed** — the repair costs more than the code it replaces: 36.3% lost on 'clean-40-full-scan', above the 2.7% noise floor, and no case improved. Worse on 4 of 4 cases ('clean-64-full-scan', 'clean-40-full-scan', 'hit-late-filter', 'numeric-191').
Mean saving across its cases: -33.7%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 10 `nlp = spacy.load("en_core_web_sm")` (OSError); line 79 `with open(sys.argv[1]) as fp:` (IndexError); line 97 `with open(sys.argv[1]) as fp:` (IndexError).
Loaded skipping failing top-level statements: line 10 `nlp = spacy.load("en_core_web_sm")` (OSError); line 79 `with open(sys.argv[1]) as fp:` (IndexError); line 97 `with open(sys.argv[1]) as fp:` (IndexError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| clean-64-full-scan | 44.79 | 59.19 | -32.2% | 13.2% | yes |
| clean-40-full-scan | 44.07 | 60.07 | -36.3% | 2.4% | yes |
| hit-late-filter | 44.25 | 58.62 | -32.5% | 2.6% | yes |
| numeric-191 | 41.50 | 55.63 | -34.0% | 1.7% | yes |

### `test/test.py::process_liquid` — liquid-early-return

**negligible** — no case moved more than the noise: the largest reading was +0.6% +-1.0% on 'large-mixed', against a clean 2.7% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: +0.2%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| mixed-dense | 58.90 | 58.91 | -0.0% | 2.3% | no: pairs disagree |
| duplicate-tags | 62.67 | 62.56 | +0.2% | 0.9% | no: pairs disagree |
| filters | 58.91 | 58.78 | +0.2% | 0.6% | no: pairs disagree |
| large-mixed | 59.07 | 58.74 | +0.6% | 1.0% | no: pairs disagree |

### `test/test.py::parse_page` — parse-page-find-all

**negligible** — no case moved more than the noise: the largest reading was -2.4% +-1.3% on 'files', against a clean 2.7% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: -2.0%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| many-exec | 60.42 | 61.68 | -2.1% | 2.3% | no: pairs disagree |
| files | 58.68 | 60.08 | -2.4% | 1.3% | no: within the floor |
| run-macro | 59.03 | 60.03 | -1.7% | 2.3% | no: pairs disagree |
| large-few-match | 83.15 | 84.56 | -1.7% | 7.2% | no: pairs disagree |

### `examples/workshop-ecommerce/preprocess.py::process_orders` — orders-agg-list

**negligible** — no case moved more than the noise: the largest reading was +2.5% +-7.9% on 'prior-and-train', against a clean 2.7% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: +0.9%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| prior-limit-10 | 72.67 | 72.46 | +0.3% | 0.6% | no: pairs disagree |
| prior-and-train | 95.17 | 92.90 | +2.4% | 7.9% | no: pairs disagree |
| mixed-three-sets | 58.94 | 58.77 | +0.3% | 0.9% | no: pairs disagree |
| orphan-orders | 56.99 | 56.74 | +0.5% | 0.8% | no: pairs disagree |

## Not measured

### `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.gen_similarity_maps` — simmap-filter-once

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures
The agent measured `no_inputs`; re-measured `over_limit`.

### `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator._prepare_similarity_map_tensor` — simmap-seqlen-hoist

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures
The agent measured `no_inputs`; re-measured `over_limit`.

### `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.gen_similarity_maps` — simmap-dead-copy

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures
The agent measured `no_inputs`; re-measured `over_limit`.

### `feed-split.py::what_language` — lang-text-once

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures

### `use-case-shopping/create_suggestions.py::filter_content` — suggest-content-any

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures

### `use-case-shopping/create_suggestions.py::filter` — suggest-filter-dead

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures

### `test/test.py::parse_file` — parse-file-typename

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures

### `news/src/python/mind_data.py::MindData.add_impressions` — add-impr-lookup

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures

### `incremental-search/search-suggestions/count_terms.py::write_json_file` — terms-replace-slash

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures

### `incremental-search/search-suggestions/count_terms.py::process_docs` — terms-total-count

**over_limit** — not counted: 20 other repairs have a verdict, the most a session measures

## Detected, not measured

Accepted findings with no measurement: deferred beyond the repairs chosen for measurement, or blocked.

- `feed-split.py::what_language` a: deferred — verify.py over_limit: 20 repairs already had a verdict, so this line was not measured
- `incremental-search/search-suggestions/count_terms.py::process_docs` b: deferred — verify.py over_limit: 20 repairs already had a verdict, so this line was not measured
- `incremental-search/search-suggestions/count_terms.py::write_json_file` a: deferred — verify.py over_limit: 20 repairs already had a verdict, so this line was not measured
- `news/src/python/mind_data.py::MindData.add_impressions` a: deferred — verify.py over_limit: 20 repairs already had a verdict, so this line was not measured
- `news/src/python/train_cold_start.py::save_embeddings` a: deferred — accepted but not measured: outside the 20 repairs and the units asked for inputs, or its unit needs a network service or model download
- `news/src/python/train_cold_start.py::train_model` a: deferred — accepted but not measured: outside the 20 repairs and the units asked for inputs, or its unit needs a network service or model download
- `news/src/python/create_bert_embeddings.py::create_embeddings` a: deferred — accepted but not measured: outside the 20 repairs and the units asked for inputs, or its unit needs a network service or model download
- `news/src/python/convert_embeddings_to_vespa_format.py::convert_news_embeddings` a: deferred — accepted but not measured: outside the 20 repairs and the units asked for inputs, or its unit needs a network service or model download
- `test/test.py::parse_file` b: deferred — verify.py over_limit: 20 repairs already had a verdict, so this line was not measured
- `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.gen_similarity_maps` a: blocked — inputs.py: the unit's module does not load here: AttributeError: SimMapGenerator is not defined here: loading the module skipped line 19 `class SimMapGenerator:` (TypeError), with stand-ins for colpali_engine
- `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.gen_similarity_maps` b: blocked — inputs.py: the unit's module does not load here: AttributeError: SimMapGenerator is not defined here: loading the module skipped line 19 `class SimMapGenerator:` (TypeError), with stand-ins for colpali_engine
- `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator._prepare_similarity_map_tensor` a: blocked — inputs.py: the unit's module does not load here: AttributeError: SimMapGenerator is not defined here: loading the module skipped line 19 `class SimMapGenerator:` (TypeError), with stand-ins for colpali_engine
- `visual-retrieval-colpali/src/main.py::get_and_store_sim_maps` a: deferred — accepted but not measured: outside the 20 repairs and the units asked for inputs, or its unit needs a network service or model download
- `visual-retrieval-colpali/src/main.py::get_and_store_sim_maps` b: deferred — accepted but not measured: outside the 20 repairs and the units asked for inputs, or its unit needs a network service or model download
- `visual-retrieval-colpali/src/main.py::message_generator` a: deferred — accepted but not measured: outside the 20 repairs and the units asked for inputs, or its unit needs a network service or model download
- `visual-retrieval-colpali/src/main.py::message_generator` b: deferred — accepted but not measured: outside the 20 repairs and the units asked for inputs, or its unit needs a network service or model download
- `use-case-shopping/create_suggestions.py::filter` b: deferred — verify.py over_limit: 20 repairs already had a verdict, so this line was not measured
- `use-case-shopping/create_suggestions.py::filter_content` a: deferred — verify.py over_limit: 20 repairs already had a verdict, so this line was not measured
- `text-search/python/collect_training_data.py::build_dataset` a: deferred — accepted but not measured: outside the 20 repairs and the units asked for inputs, or its unit needs a network service or model download
- `examples/embedder-auto-training-evaluation/training-evaluation/train.py::TrainDataset.__init__` a: deferred — accepted but not measured: outside the 20 repairs and the units asked for inputs, or its unit needs a network service or model download
- `examples/ecommerce-user-preferences/webapp/app.py::load_system_prompt` a: deferred — accepted but not measured: outside the 20 repairs and the units asked for inputs, or its unit needs a network service or model download
- `examples/workshop-ecommerce/preprocess.py::process_products` a: deferred — accepted but not measured: outside the 20 repairs and the units asked for inputs, or its unit needs a network service or model download
- `examples/workshop-ecommerce/preprocess.py::process_users` a: deferred — accepted but not measured: outside the 20 repairs and the units asked for inputs, or its unit needs a network service or model download
- `examples/workshop-ecommerce/preprocess.py::process_users` c: deferred — accepted but not measured: outside the 20 repairs and the units asked for inputs, or its unit needs a network service or model download
- `examples/workshop-ecommerce/preprocess.py::process_orders` b: deferred — accepted but not measured: outside the 20 repairs and the units asked for inputs, or its unit needs a network service or model download
- `rag-blueprint/eval/train_lightgbm.py::perform_cross_validation` b: deferred — accepted but not measured: outside the 20 repairs and the units asked for inputs, or its unit needs a network service or model download
