# Energy report — sample-apps @ e2ed22d

116 units listed, 41 with an accepted suspicion · 16 repairs submitted, 2 deferred · 8 confirmed · 4 partial · 1 regressed · 2 negligible · 1 not_equivalent · 8 applied
Noise floor 2.8% (from: session calibration).

## Applied

### `news/src/python/create_bert_embeddings.py::write_embedding` — write-embedding-single-write

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +34.9%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 15 `data_dir = sys.argv[1]` (IndexError); line 18 `train_news_file = os.path.join(data_dir, "train", "news.t...` (NameError); line 19 `train_embedding_file = os.path.join(data_dir, "train", "n...` (NameError); line 20 `dev_news_file = os.path.join(data_dir, "dev", "news.tsv")` (NameError); line 21 `dev_embedding_file = os.path.join(data_dir, "dev", "news_...` (NameError).
Loaded skipping failing top-level statements: line 15 `data_dir = sys.argv[1]` (IndexError); line 18 `train_news_file = os.path.join(data_dir, "train", "news.t...` (NameError); line 19 `train_embedding_file = os.path.join(data_dir, "train", "n...` (NameError); line 20 `dev_news_file = os.path.join(data_dir, "dev", "news.tsv")` (NameError); line 21 `dev_embedding_file = os.path.join(data_dir, "dev", "news_...` (NameError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| normal-16384 | 88.82 | 58.40 | +34.3% | 3.5% | yes |
| normal-32768 | 87.95 | 55.87 | +36.5% | 1.4% | yes |
| normal-50000 | 80.69 | 52.85 | +34.5% | 5.8% | yes |
| mixed-magnitudes-20000 | 82.30 | 53.89 | +34.5% | 1.0% | yes |

### `text-search/python/convert-to-vespa-format.py::main` — convert-main-json-dumps

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +28.2%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 9 `if len(sys.argv) != 5:` (SystemExit); line 13 `source_dir, dest_dir, doc_type, fields = sys.argv[1:5]` (ValueError); line 14 `fields = fields.split(",")` (NameError); line 17 `if not os.path.isdir(source_dir):` (NameError); line 20 `if not os.path.isdir(dest_dir):` (NameError); line 24 `sample_offset_file = os.path.join(source_dir, "test-docs-...` (NameError); line 25 `docs_file = os.path.join(source_dir, "docs.tsv")` (NameError); line 26 `out_file = os.path.join(dest_dir, "documents.jsonl")` (NameError).
Loaded skipping failing top-level statements: line 9 `if len(sys.argv) != 5:` (SystemExit); line 13 `source_dir, dest_dir, doc_type, fields = sys.argv[1:5]` (ValueError); line 14 `fields = fields.split(",")` (NameError); line 17 `if not os.path.isdir(source_dir):` (NameError); line 20 `if not os.path.isdir(dest_dir):` (NameError); line 24 `sample_offset_file = os.path.join(source_dir, "test-docs-...` (NameError); line 25 `docs_file = os.path.join(source_dir, "docs.tsv")` (NameError); line 26 `out_file = os.path.join(dest_dir, "documents.jsonl")` (NameError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large | 87.80 | 62.36 | +29.0% | 2.7% | yes |
| tiny-lines | 107.20 | 76.00 | +29.1% | 0.5% | yes |
| long-titles | 81.17 | 58.26 | +28.2% | 2.7% | yes |
| single-field | 94.72 | 69.64 | +26.5% | 0.9% | yes |

### `examples/workshop-ecommerce/preprocess.py::process_users` — process-users-itertuples

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +48.1%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| full-150-users | 99.63 | 46.29 | +53.5% | 1.8% | yes |
| limit-200 | 64.34 | 55.63 | +13.5% | 1.9% | yes |
| few-users-heavy | 86.65 | 8.83 | +89.8% | 0.1% | yes |
| many-duplicates | 92.25 | 59.46 | +35.5% | 0.9% | yes |

### `news/src/python/mind_data.py::MindData.sample_valid_data` — sample-valid-data-cache-tensors

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +97.8%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| typical-valid | 112.46 | 0.68 | +99.4% | 0.1% | yes |
| many-short-partial | 120.26 | 2.64 | +97.8% | 5.5% | yes |
| train-impressions | 112.73 | 0.70 | +99.4% | 0.0% | yes |
| many-short-low-prob | 118.00 | 6.36 | +94.6% | 17.8% | yes |

### `visual-retrieval-colpali/prepare_feed_deploy.py::float_to_binary_embedding` — float-to-binary-stacked-packbits

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +61.8%.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 65 `from colpali_engine.models import ColPali, ColPaliProcessor` (ImportError); line 129 `VESPA_CLOUD_SECRET_TOKEN = os.getenv("VESPA_CLOUD_SECRET_...` (EOFError); line 138 `GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or input(` (EOFError); line 146 `gemini_client = genai.Client(api_key=GEMINI_API_KEY)` (NameError); line 150 `device = get_torch_device("auto")` (TypeError); line 151 `print(f"Using device: {device}")` (NameError); line 154 `model = ColPali.from_pretrained(` (NameError); line 160 `processor = ColPaliProcessor.from_pretrained(MODEL_NAME)` (NameError); line 360 `print(f"Max text length: {np.max(text_lengths)}")` (ValueError); line 361 `print(f"Min text length: {np.min(text_lengths)}")` (ValueError); line 461 `pdf_pages[46]["image"]` (IndexError); line 463 `pdf_pages[46]["queries"]` (IndexError); line 574 `embeddings = generate_embeddings(images, model, processor)` (NameError); line 576 `embeddings.shape` (NameError); line 596 `for pdf, embedding in zip(pdf_pages, embeddings):` (NameError); line 972 `VESPA_TEAM_API_KEY = os.getenv("VESPA_TEAM_API_KEY") or i...` (EOFError); line 977 `vespa_cloud = VespaCloud(` (NameError); line 985 `vespa_cloud.deploy()` (NameError); line 988 `endpoint_url = vespa_cloud.get_token_endpoint()` (NameError); line 989 `print(f"Application deployed. Token endpoint URL: {endpoi...` (NameError); line 1000 `app = Vespa(url=endpoint_url, vespa_cloud_secret_token=VE...` (NameError); line 1001 `app.get_application_status()` (NameError); line 1013 `app.feed_async_iterable(vespa_feed, schema=VESPA_SCHEMA_N...` (NameError).
Loaded skipping failing top-level statements: line 65 `from colpali_engine.models import ColPali, ColPaliProcessor` (ImportError); line 129 `VESPA_CLOUD_SECRET_TOKEN = os.getenv("VESPA_CLOUD_SECRET_...` (EOFError); line 138 `GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or input(` (EOFError); line 146 `gemini_client = genai.Client(api_key=GEMINI_API_KEY)` (NameError); line 150 `device = get_torch_device("auto")` (TypeError); line 151 `print(f"Using device: {device}")` (NameError); line 154 `model = ColPali.from_pretrained(` (NameError); line 160 `processor = ColPaliProcessor.from_pretrained(MODEL_NAME)` (NameError); line 360 `print(f"Max text length: {np.max(text_lengths)}")` (ValueError); line 361 `print(f"Min text length: {np.min(text_lengths)}")` (ValueError); line 461 `pdf_pages[46]["image"]` (IndexError); line 463 `pdf_pages[46]["queries"]` (IndexError); line 574 `embeddings = generate_embeddings(images, model, processor)` (NameError); line 576 `embeddings.shape` (NameError); line 596 `for pdf, embedding in zip(pdf_pages, embeddings):` (NameError); line 972 `VESPA_TEAM_API_KEY = os.getenv("VESPA_TEAM_API_KEY") or i...` (EOFError); line 977 `vespa_cloud = VespaCloud(` (NameError); line 985 `vespa_cloud.deploy()` (NameError); line 988 `endpoint_url = vespa_cloud.get_token_endpoint()` (NameError); line 989 `print(f"Application deployed. Token endpoint URL: {endpoi...` (NameError); line 1000 `app = Vespa(url=endpoint_url, vespa_cloud_secret_token=VE...` (NameError); line 1001 `app.get_application_status()` (NameError); line 1013 `app.feed_async_iterable(vespa_feed, schema=VESPA_SCHEMA_N...` (NameError).

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| colpali-large-2048x128 | 117.97 | 37.32 | +68.4% | 10.0% | yes |
| dim-64-3000-patches | 107.08 | 22.72 | +78.8% | 0.1% | yes |
| dim-1024-900-patches | 86.01 | 57.54 | +33.1% | 0.6% | yes |
| many-patches-4096x128 | 104.28 | 34.58 | +66.8% | 0.2% | yes |

### `news/src/python/convert_embeddings_to_vespa_format.py::convert_user_embeddings` — convert-user-embeddings-tolist

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +18.7%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| wide-128d | 70.78 | 57.57 | +18.7% | 0.7% | yes |
| narrow-32d | 77.39 | 61.55 | +20.5% | 2.6% | yes |
| deep-300d | 79.15 | 64.96 | +17.9% | 1.8% | yes |
| bert-768d | 68.94 | 56.85 | +17.5% | 2.2% | yes |

### `news/src/python/convert_embeddings_to_vespa_format.py::convert_news_embeddings` — convert-news-embeddings-tolist

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +23.3%.
Measured twice: the first measurement came out `partial` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| wide | 72.66 | 56.02 | +22.9% | 0.5% | yes |
| long | 79.09 | 57.93 | +26.7% | 0.3% | yes |
| large_values | 72.65 | 57.80 | +20.4% | 1.4% | yes |
| small_values | 75.51 | 58.12 | +23.0% | 1.0% | yes |

### `examples/workshop-ecommerce/preprocess.py::process_orders` — process-orders-sample-subset

**confirmed** — applied: the largest mean saving among this function's confirmed repairs
Mean saving across its cases: +83.2%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| prior-limit-10 | 101.74 | 8.19 | +91.9% | 0.7% | yes |
| prior-and-train | 90.87 | 7.72 | +91.5% | 0.1% | yes |
| mixed-three-sets | 113.54 | 33.07 | +70.9% | 0.2% | yes |
| orphan-orders | 110.02 | 23.55 | +78.6% | 0.5% | yes |

## Measured, not confirmed

### `news/src/python/mind_data.py::MindData.add_impressions` — add-impressions-bind-content

**partial** — saves energy on 3 of 4 inputs ('large-positives', 'heavy-sampling', 'medium'; best 6.3% +-0.2% on 'medium'), and no saving that can be told from noise on the rest: 'many-positives-few-negatives' +0.5% +-1.4% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +4.1%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large-positives | 62.56 | 59.44 | +5.0% | 2.1% | yes |
| many-positives-few-negatives | 59.20 | 58.90 | +0.5% | 1.4% | no: pairs disagree |
| heavy-sampling | 65.26 | 62.24 | +4.6% | 1.6% | yes |
| medium | 63.82 | 59.83 | +6.3% | 0.2% | yes |

### `news/src/python/train_cold_start.py::write_embeddings` — write-embeddings-tolist-once

**partial** — saves energy on 3 of 4 inputs ('large', 'narrow', 'many'; best 7.8% +-1.4% on 'narrow'), and no saving that can be told from noise on the rest: 'wide' +1.7% +-2.3% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +4.6%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large | 60.90 | 58.75 | +3.5% | 2.7% | yes |
| wide | 60.68 | 59.65 | +1.7% | 2.3% | no: pairs disagree |
| narrow | 64.56 | 59.53 | +7.8% | 1.4% | yes |
| many | 64.76 | 61.40 | +5.2% | 2.3% | yes |

### `feed-split.py::split_text` — split-text-join-lines

**negligible** — no case moved more than the noise: the largest reading was +0.6% +-0.6% on 'lists-and-links', against a clean 2.8% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: +0.2%.
Behaviour compared under a relaxed rule: loaded with these uninstalled packages stood in for: tiktoken.
Loaded with uninstalled packages stood in for: tiktoken.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| lists-and-links | 67.16 | 66.78 | +0.6% | 0.6% | no: pairs disagree |
| top-level-tables | 62.29 | 62.12 | +0.3% | 0.7% | no: pairs disagree |
| tables-inside-divs | 61.14 | 61.32 | -0.3% | 1.4% | no: pairs disagree |
| mixed-large | 59.51 | 59.24 | +0.4% | 1.1% | no: pairs disagree |

### `text-search/python/extract-msmarco.py::extract_documents` — extract-documents-track-offset

**partial** — saves energy on 2 of 4 inputs ('unicode-1500', 'mixed-3000'; best 4.8% +-3.0% on 'unicode-1500'), and no saving that can be told from noise on the rest: 'long-800' +0.7% +-5.4% (its pairs disagree too much to tell); 'long-1200' +0.3% +-0.7% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +2.2%.
Measured twice: the first measurement came out `partial` with an input too noisy to read, and this is the second.
The agent measured `negligible`; re-measured `partial`.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| unicode-1500 | 64.45 | 61.36 | +4.8% | 3.0% | yes |
| long-800 | 64.17 | 63.68 | +0.8% | 5.4% | no: pairs disagree |
| mixed-3000 | 62.25 | 60.32 | +3.1% | 0.8% | yes |
| long-1200 | 61.54 | 61.36 | +0.3% | 0.7% | no: pairs disagree |

### `news/src/python/create_category_ctrs.py::write_news_category_ctr_update` — category-tensor-once-per-category

**regressed** — the repair costs more than the code it replaces: 14.7% lost on 'large-simple', above the 2.8% noise floor, and no case improved. Worse on 4 of 4 cases ('large-very-long', 'large-diverse-chars', 'large-mixed', 'large-simple').
Mean saving across its cases: -13.8%.
Measured twice: the first measurement came out `regressed` with an input too noisy to read, and this is the second.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| large-very-long | 56.61 | 63.54 | -12.3% | 2.1% | yes |
| large-diverse-chars | 56.77 | 64.78 | -14.1% | 0.7% | yes |
| large-mixed | 57.67 | 65.75 | -14.0% | 5.4% | yes |
| large-simple | 57.77 | 66.24 | -14.7% | 1.2% | yes |

### `examples/workshop-ecommerce/preprocess.py::process_orders` — process-orders-itertuples

**partial** — saves energy on 1 of 4 inputs ('mixed-three-sets'; best 6.3% +-0.6% on 'mixed-three-sets'), and no saving that can be told from noise on the rest: 'prior-limit-10' +0.8% +-1.9% (its pairs disagree too much to tell); 'prior-and-train' +0.1% +-2.4% (its pairs disagree too much to tell); 'orphan-orders' +0.8% +-1.1% (its pairs disagree too much to tell). A confirmed repair saves on every input; this one pays only on some of the work the unit does.
Mean saving across its cases: +2.0%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| prior-limit-10 | 65.82 | 65.30 | +0.8% | 1.9% | no: pairs disagree |
| prior-and-train | 89.44 | 89.32 | +0.1% | 2.4% | no: pairs disagree |
| mixed-three-sets | 63.13 | 59.13 | +6.3% | 0.6% | yes |
| orphan-orders | 61.20 | 60.72 | +0.8% | 1.1% | no: pairs disagree |

### `hypencoder/encode_query.py::main` — encode-query-float-lists

**negligible** — no case moved more than the noise: the largest reading was +1.8% +-1.4% on 'default-huge-small', against a clean 2.8% floor across 4 cases. The pattern is here and removing it saves nothing measurable, so it is not worth repairing in this code.
Mean saving across its cases: +0.5%.

| case | before J | after J | saved | +- (95%) | counted |
|---|---:|---:|---:|---:|---|
| default-long-large | 62.02 | 61.38 | +1.0% | 6.5% | no: pairs disagree |
| default-huge-small | 58.43 | 57.35 | +1.9% | 1.4% | no: within the floor |
| default-mixed-hits100 | 66.48 | 66.76 | -0.4% | 7.3% | no: pairs disagree |
| rerank-medium | 67.23 | 67.54 | -0.5% | 1.5% | no: pairs disagree |

## Not measured

### `visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.format_q_embs` — format-q-embs-bulk-tolist

**not_equivalent** — the repair behaves differently on 'single-row': different return value: before -> {"dict":[[0,{"list":[-0.024371426552534103,0.40486377477645874,0.08679717779159546,-0.23891858756542206]}]]}, after -> {"dict":[[0,{"list":[0.6712610125541687,0.5885852575302124,1.004227638244629,-1.106109619140625]}]]}. The repair is wrong; fix it and re-run. Do not report this candidate either way.
Behaviour compared under a relaxed rule: the module fails on import, so it was loaded one top-level statement at a time, skipping: line 10 `from .colpali import SimMapGenerator` (ImportError).
Loaded skipping failing top-level statements: line 10 `from .colpali import SimMapGenerator` (ImportError).

## Detected, not measured

Accepted findings with no measurement: deferred beyond the repairs chosen for measurement, or blocked.

- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::EvaluateResults` a: blocked — inputs.py: it cannot run here: `EvaluateResults` invokes a `ChatOpenAI` chain (`chain.invoke(...)`), which performs a network request to the OpenAI API and needs credentials; no input can avoid that.
- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::subgraph_EvaluateCategory` a: blocked — inputs.py: it cannot run here: the function invokes a ChatOpenAI model (`chain.invoke(...)`), which performs a network request to the OpenAI API requiring credentials and connectivity; no input can avoid that.
- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::subgraph_EvaluateFilters` a: blocked — inputs.py: it cannot run here: subgraph_EvaluateFilters constructs a ChatOpenAI model and invokes a LangChain chain against the OpenAI API, which requires network access and API credentials that are unavailable here.
- `examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::subgraph_GenerateKeywords` a: blocked — inputs.py: it cannot run here: the function builds a `ChatOpenAI` model and calls `chain.invoke(...)`, which performs a request to the OpenAI API (network access and credentials required); this happens unconditionally inside the timed call and cannot be avoided by any input.
- `examples/ecommerce-user-preferences/webapp/app.py::get_wikipedia_image` a: blocked — inputs.py: it cannot run here: `get_wikipedia_image` fetches data from the Wikipedia API via `requests.get` (search, images, imageinfo endpoints); its real work is network I/O to a remote server, which is unavailable here and cannot be avoided without mocking the HTTP client (forbidden), and forcing cache hits would bypass the function's actual work entirely.
- `examples/ecommerce-user-preferences/webapp/app.py::get_wikipedia_image` c: blocked — inputs.py: it cannot run here: `get_wikipedia_image` fetches data from the Wikipedia API via `requests.get` (search, images, imageinfo endpoints); its real work is network I/O to a remote server, which is unavailable here and cannot be avoided without mocking the HTTP client (forbidden), and forcing cache hits would bypass the function's actual work entirely.
- `examples/google-cloud/cloud-functions/python/main.py::get_blobs` a: blocked — inputs.py: it cannot run here: `get_blobs` creates a `google.cloud.storage.Client()` and calls `list_blobs(bucket)`, which performs an authenticated network request to the Google Cloud Storage API; no input can avoid that.
- `examples/in-context-learning/categorize_group.py::inference` a: blocked — inputs.py: it cannot run here: `inference` begins by posting a query to a Vespa search server at `http://localhost:8080/search/`; it needs a running Vespa instance (with configured embedders/rank profiles) and network access, so no input can make it run here.
- `feed_to_vespa.py::update_endpoint` a: blocked — inputs.py: it cannot run here: `update_endpoint` unconditionally calls `get_indexed_docids` → `vespa_visit`, which performs an HTTP request to the Vespa endpoint, and its feed path runs the `vespa` subprocess; no input can avoid network access and subprocesses.
- `feed_to_vespa.py::update_endpoint` c: blocked — inputs.py: it cannot run here: `update_endpoint` unconditionally calls `get_indexed_docids` → `vespa_visit`, which performs an HTTP request to the Vespa endpoint, and its feed path runs the `vespa` subprocess; no input can avoid network access and subprocesses.
- `feed_to_vespa.py::update_endpoint` d: blocked — inputs.py: it cannot run here: `update_endpoint` unconditionally calls `get_indexed_docids` → `vespa_visit`, which performs an HTTP request to the Vespa endpoint, and its feed path runs the `vespa` subprocess; no input can avoid network access and subprocesses.
- `incremental-search/search-as-you-type/feed_to_vespa.py::update_endpoint` c: blocked — inputs.py: it cannot run here: `update_endpoint` unconditionally calls `get_indexed_docids` → `vespa_visit` → `call(...)`, which issues HTTP requests (curl subprocess) to a live Vespa endpoint; it needs a running remote service and network access, and no input can avoid that.
- `text-search/python/collect_training_data.py::build_dataset` a: blocked — inputs.py: it cannot run here: `build_dataset` performs its work by calling `get_features`, which issues `requests.post(url, ...)` to a Vespa search server (default `http://localhost:8080/search/`) — a network request to a remote service is required for every unprocessed query, and no input can make the function do its real work without that server being available.
- `text-search/python/collect_training_data.py::build_dataset` b: blocked — inputs.py: it cannot run here: `build_dataset` performs its work by calling `get_features`, which issues `requests.post(url, ...)` to a Vespa search server (default `http://localhost:8080/search/`) — a network request to a remote service is required for every unprocessed query, and no input can make the function do its real work without that server being available.
- `text-search/python/collect_training_data.py::get_features` a: blocked — inputs.py: it cannot run here: `get_features` performs an HTTP POST to a server via `requests.post(url, json=body)` as its first action; there is no input that avoids network access, and mocking the request is not allowed.
- `news/src/python/create_bert_embeddings.py::create_embeddings` a: blocked — inputs.py: it cannot run here: `create_embeddings` calls `BertTokenizer.from_pretrained('bert-base-uncased')` and `BertModel.from_pretrained('google/bert_uncased_L-8_H-512_A-8')`, which require downloading pretrained models from the Hugging Face Hub (network access) or a pre-populated local model cache, neither of which is available here.
- `news/src/python/create_bert_embeddings.py::create_embeddings` b: blocked — inputs.py: it cannot run here: `create_embeddings` calls `BertTokenizer.from_pretrained('bert-base-uncased')` and `BertModel.from_pretrained('google/bert_uncased_L-8_H-512_A-8')`, which require downloading pretrained models from the Hugging Face Hub (network access) or a pre-populated local model cache, neither of which is available here.
- `news/src/python/evaluate.py::calc_impression` a: blocked — inputs.py: it cannot run here: `calc_impression` begins by calling `query_user_embedding(user_id, url, cert)` and then `query_news(...)`, both of which issue HTTP requests to a Vespa server (the `url`/`cert` come from `connect()` for a live CLI target); there is no input that avoids the network, and mocking those calls is not permitted.
- `news/src/python/train_cold_start.py::train_model` a: deferred — accepted in step 2 but not asked for inputs: training run too long to measure within the session budget
- `news/src/python/train_mf.py::main` a: deferred — accepted in step 2 but not asked for inputs: training run too long to measure within the session budget
- `news/src/python/vespa_client.py::query_news` a: blocked — inputs.py: it cannot run here: `query_news` performs a live HTTP POST to the Vespa search endpoint via `requests.post(f'{url}/search/', ...)`; its work begins with a network request to a remote service (and needs a client certificate), which cannot be satisfied here (no network access, no stand-in servers).
- `news/src/python/vespa_client.py::query_user_embedding` a: blocked — inputs.py: it cannot run here: `query_user_embedding` performs `requests.get(url, cert=cert)` against a Vespa search endpoint; it requires network access to a remote service, and no input can avoid that.
- `multilingual-search/ext/evaluate.py::search` a: blocked — inputs.py: it cannot run here: `search` begins its work with `session.post(args.endpoint, ...)`, an HTTP request to a remote Vespa endpoint, which needs network access that is unavailable here.
- `visual-retrieval-colpali/prepare_feed_deploy.py::download_pdf` a: blocked — inputs.py: it cannot run here: `download_pdf` begins its work by awaiting an HTTP request (`await session.get(url)`) on the session it is given, so it needs a live server / network access; providing a session that answers without a real request would be a mock, which is not allowed.
- `visual-retrieval-colpali/prepare_feed_deploy.py::generate_embeddings` a: blocked — inputs.py: it cannot run here: `generate_embeddings` needs a real `ColPali` model and `ColPaliProcessor` (built via `ColPali.from_pretrained(MODEL_NAME)` / `ColPaliProcessor.from_pretrained(MODEL_NAME)`), which download the ColPali checkpoint from Hugging Face, plus the `colpali_engine` library. There is no way to obtain these inputs here without network access, and supplying stand-in model/processor objects would be mocking the very objects whose inference is the function's work.
- `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator._prepare_similarity_map_tensor` a: blocked — inputs.py: the unit's module does not load here: AttributeError: SimMapGenerator is not defined here: loading the module skipped line 19 `class SimMapGenerator:` (TypeError), with stand-ins for colpali_engine
- `visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.should_filter_token` a: blocked — inputs.py: the unit's module does not load here: AttributeError: SimMapGenerator is not defined here: loading the module skipped line 19 `class SimMapGenerator:` (TypeError), with stand-ins for colpali_engine
- `visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.query_vespa_bm25` b: blocked — inputs.py: it cannot run here: the method opens a Vespa session and issues a live HTTP query (`session.query(...)`) to a Vespa application; `VespaQueryClient.__init__` also requires Vespa credentials/URLs and calls `wait_for_application_up()`, so no input can avoid network access.
- `visual-retrieval-colpali/src/main.py::full_image` a: blocked — inputs.py: the inputs that run here reach only 0% of the function (lines 327-329, 331-333, 335-337 never ran), so they would not measure its real work
- `visual-retrieval-colpali/src/main.py::message_generator` b: blocked — inputs.py: it cannot run here: for any input that does real work (non-empty `doc_ids` with images present, which is what the repository's `/get-message` route always passes) the generator awaits `gemini_client.aio.models.generate_content_stream(...)`, i.e. a live network call to the Gemini API requiring credentials; the module itself builds `genai.Client(api_key=os.getenv("GEMINI_API_KEY"))` at import time. The only path that avoids the request is `doc_ids == []` (or waiting out the 10 s `max_wait`), which either does no meaningful work or exceeds the per-call time budget, so no valid measurable input exists.
- `visual-retrieval-colpali/tests/huggingface_smoke.py::main` a: blocked — inputs.py: it cannot run here: `main` unconditionally imports `dotenv`, `gradio`, `starlette.testclient`, `torch` and the `visual-retrieval-colpali` application module (which itself needs the full ColPali/transformers stack) and patches `vespa.application.Vespa.wait_for_application_up`; these heavy third-party ML/web packages are not available in this environment, and no input can avoid them.
