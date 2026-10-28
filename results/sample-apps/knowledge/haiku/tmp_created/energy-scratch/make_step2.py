import sys, json, importlib
sys.path.insert(0, "/tmp/energy-scratch")
import dec_part1
for m in ["dec_part2","dec_part3","dec_part4","dec_part5","dec_part6","dec_part7","dec_fix"]:
    importlib.import_module(m)
D = dec_part1.D
# step-2 decisions must use the unit's real label set; old junk labels are dropped by the lookup below
WHAT = {
"feed-split.py::split_text": "splits a BeautifulSoup page into markdown sections, growing each section's text line by line with string concatenation",
"feed-split.py::what_language": "returns the language name for a code block by calling get_text() on it and testing a few substrings",
"colbert-long/scripts/convert.py::remove_control_characters": "returns the string with every Unicode control/format character removed, one character at a time",
"use-case-shopping/create_suggestions.py::filter_content": "returns True when a noun phrase starts with one of eight stop prefixes",
"use-case-shopping/create_suggestions.py::filter": "returns True when a candidate title is too short or long, or contains a banned character",
"use-case-shopping/convert_meta.py::main": "reads product metadata, converts it and writes it as indented JSON to the output file",
"use-case-shopping/convert_reviews.py::main": "reads reviews, converts them and writes them as indented JSON to the output file",
"incremental-search/search-suggestions/count_terms.py::process_docs": "counts term occurrences across documents and sums the per-term document counts",
"incremental-search/search-suggestions/count_terms.py::write_json_file": "builds the feed list of term documents and writes it as indented JSON to a file",
"incremental-search/search-suggestions/count_terms.py::count_terms": "counts all n-gram windows of a token list that contain no common word",
"incremental-search/search-suggestions/accepted_words.py::process_docs": "collects the set of distinct words from the titles and contents of all documents",
"incremental-search/search-as-you-type/feed_to_vespa.py::vespa_feed": "feeds each document to Vespa by spawning a curl process per document",
"incremental-search/search-as-you-type/feed_to_vespa.py::vespa_remove": "deletes each given document id from Vespa by spawning a curl process per id",
"incremental-search/search-as-you-type/feed_to_vespa.py::update_endpoint": "lists the indexed ids, removes stale ones, and feeds the feed files to one endpoint",
"incremental-search/search-as-you-type/feed_to_vespa.py::get_docs": "loads a feed file's JSON documents from disk",
"feed_to_vespa.py::vespa_remove": "deletes each stale document id from Vespa with one HTTP request per id",
"feed_to_vespa.py::update_endpoint": "reads the indexed and feed document ids for one endpoint and removes stale ids and feeds the files",
"text-search/python/collect_training_data.py::build_dataset": "for each unprocessed query, queries Vespa and appends its feature rows to the training CSV and the processed-queries file",
"text-search/python/extract-msmarco.py::extract_documents": "writes the MS MARCO document bodies and their offset index, one document at a time",
"text-search/python/extract-msmarco.py::load_msmarco_queries": "reads every MS MARCO query, normalises its text, and returns a dict keyed by query id",
"text-search/python/extract-msmarco.py::getcontent": "returns the normalised TSV line of one document by seeking to its offset",
"text-search/python/sample-queries-and-documents.py::select_documents": "returns the set of document ids for the sampled queries plus random extra documents",
"text-video-search/src/python/embedding.py::sample_images": "returns equally spaced frames sampled from a list of decoded video frames",
"text-video-search/src/python/embedding.py::extract_images": "decodes every one-frame-per-second frame of a video and returns the sampled frames",
"text-video-search/src/python/embedding.py::VideoFeedDataset.__getitem__": "decodes one video, encodes each sampled frame with CLIP, and returns the Vespa feed documents",
"text-video-search/src/python/embedding.py::search_video_file_names": "queries Vespa for a text and returns the file name and relevance of each hit",
"multilingual-search/ext/evaluate.py::search": "queries the search endpoint for one query group and appends each hit to the run results",
"news/src/python/evaluate.py::read_impressions_file": "parses every impression line of the behaviours file into user, news ids and labels",
"news/src/python/evaluate.py::predictions": "returns the relevance score of each news id, found by a linear scan of the hit children",
"news/src/python/evaluate.py::calc_impression": "fetches the user's embedding from Vespa and returns the predicted scores and labels for one impression",
"news/src/python/convert_embeddings_to_vespa_format.py::read_embeddings": "reads an embeddings file into a dict of float32 arrays keyed by id",
"news/src/python/create_bert_embeddings.py::create_embeddings": "loads BERT, embeds each document's title and abstract one at a time, and writes the first-token vectors",
"news/src/python/create_bert_embeddings.py::write_embedding": "writes one embedding as tab-separated, comma-joined floats with four decimals",
"news/src/python/create_category_ctrs.py::write_news_category_ctr_update": "writes the Vespa update JSON for every news item's category",
"news/src/python/mind_data.py::MindData.read_news": "reads the news file into the news-content table of category, subcategory and entity indices",
"news/src/python/mind_data.py::MindData.read_data": "reads the impressions file into a list of user, time, news and label records",
"news/src/python/mind_data.py::MindData.sample_training_data": "builds a shuffled DataLoader of positive and sampled negative training examples",
"news/src/python/mind_data.py::MindData.add_impressions": "adds the positive and sampled negative training rows of one impression to six lists",
"news/src/python/mind_data.py::MindData.sample_valid_data": "builds validation tensors for each impression that has mixed labels",
"news/src/python/train_cold_start.py::save_embeddings": "writes the user and news embeddings produced by the model to TSV files",
"news/src/python/train_cold_start.py::train_epoch": "runs one training epoch and prints the total loss",
"news/src/python/train_mf.py::train_epoch": "runs one matrix-factorisation training epoch and prints the total loss",
"news/src/python/train_cold_start.py::read_bert_embeddings": "builds a float tensor of BERT embeddings for all news from the train and valid files",
"news/src/python/train_cold_start.py::read_bert_embeddings_from_file": "fills the embedding rows for the news ids in one embeddings file",
"news/src/python/vespa_client.py::query_user_embedding": "fetches a user's embedding from Vespa over HTTP",
"billion-scale-vector-search/app/src/main/python/recall.py::main": "runs the recall evaluation over the queries and prints the recall figures",
"commerce-product-ranking/scripts/evaluate.py::main": "reads the example parquet file and computes the ranking metrics for each query group",
"hypencoder/encode_query.py::main": "tokenises a query and prints its ids and attention mask as lists",
"hypencoder/model2onnx.py::QueryEncoderWrapper.forward": "runs the query encoder's layers on the input, applying each block's weights after a transpose",
"hypencoder/model2onnx.py::_get_weights_and_biases_static": "returns the weights and biases of the static layers, transposed for export",
"examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::subgraph_GenerateKeywords": "builds an LLM chain with a fresh parser and prompt and returns the search keywords",
"examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::subgraph_EvaluateCategory": "builds an LLM chain with a fresh parser and prompt and sets the categories in the state",
"examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::subgraph_EvaluateFilters": "builds an LLM chain with a fresh schema, parser and prompt and sets the price and rating filters",
"examples/agentic-streamlit-chatbot/advanced_app/vespa_shopping_assistant/langgraph_modules/subgraph.py::EvaluateResults": "builds an LLM chain with a fresh parser and prompt and keeps up to five relevant results",
"examples/book-search/frontend/app.py::feed_catalog": "feeds every line of the catalogue JSONL file to Vespa, one document per request",
"examples/ecommerce-user-preferences/webapp/app.py::chat": "sends the chat turn to the LLM, updates the session preferences, and queries Vespa for results and facets",
"examples/ecommerce-user-preferences/webapp/app.py::update_preferences": "stores the preferences in the session and queries Vespa for results and facets",
"examples/ecommerce-user-preferences/webapp/app.py::get_wikipedia_image": "finds an image URL for a make and model by calling the Wikipedia API, with a cache of hits",
"examples/google-cloud/cloud-functions/python/main.py::get_blobs": "creates a storage client and lists the blobs of a bucket",
"examples/google-cloud/cloud-functions/python/main.py::listfiles": "returns the names of the bucket's blobs that contain the file filter",
"examples/google-cloud/cloud-functions/python/main.py::getlogs": "downloads and decompresses matching zstd log files and returns the JSON lines whose uri matches",
"examples/in-context-learning/categorize_group.py::inference": "builds twelve Vespa query bodies and sends one (the bm25 no-group one) to the search endpoint",
"examples/embedder-auto-training-evaluation/training-evaluation/evaluate.py::main": "runs one search per query sequentially and writes the run file",
"examples/embedder-auto-training-evaluation/training-evaluation/positives-negatives.py::main": "runs one search per query sequentially, collects training records, and writes them to a JSONL file",
"examples/embedder-auto-training-evaluation/training-evaluation/train.py::TrainDataset.__init__": "loads the documents and queries JSONL files into dicts keyed by id",
"examples/embedder-auto-training-evaluation/training-evaluation/train.py::TrainDataset.__getitem__": "returns one training example made of a query, a positive and a negative document, rotating the id lists",
"examples/mcp-server-app/script/generate_data.py::generate_job": "generates one random job posting with skills, a salary range and a description from a random template",
"examples/mcp-server-app/script/generate_data.py::save_vespa_feed": "writes the documents as Vespa JSONL to a file",
"examples/workshop-ecommerce/preprocess.py::process_orders": "writes the orders for each eval set as Vespa JSONL, with the product ids aggregated per order",
"examples/workshop-ecommerce/preprocess.py::process_users": "builds one Vespa user document per user from the order-product history and writes users.jsonl",
"examples/workshop-ecommerce/preprocess.py::process_products": "writes the product documents, with aisle and department names, as Vespa JSONL",
"rag-blueprint/eval/collect_pyvespa.py::feature_collection_first_phase_query_fn": "builds the Vespa query body for the first phase of feature collection",
"rag-blueprint/eval/collect_pyvespa.py::feature_collection_second_phase_query_fn": "builds the Vespa query body for the second phase of feature collection",
"rag-blueprint/eval/evaluate_ranking.py::rank_first_phase_query_fn": "builds the Vespa query body for the first ranking phase",
"rag-blueprint/eval/evaluate_ranking.py::rank_second_phase_query_fn": "builds the Vespa query body for the second ranking phase",
"rag-blueprint/eval/evaluate_match_phase.py::match_weakand_query_fn": "builds the Vespa query body for the weakAnd match-only evaluation",
"rag-blueprint/eval/train_lightgbm.py::perform_cross_validation": "trains LightGBM over cross-validation folds, renames features, and writes the model",
"rag-blueprint/eval/train_logistic_regression.py::perform_cross_validation": "prints feature statistics, runs five-fold logistic regression, and writes the coefficients",
"visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.gen_similarity_maps": "loads the images, builds the similarity tensor, and yields one blended heatmap per image and token",
"visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator._prepare_similarity_map_tensor": "fills a patch-by-token tensor from the Vespa similarity cells",
"visual-retrieval-colpali/src/backend/colpali.py::SimMapGenerator.should_filter_token": "returns True for tokens that are special, whitespace, punctuation, or underscore-prefixed",
"visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.format_query_results": "logs a one-line summary of a Vespa response and returns its JSON",
"visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.get_result_from_query": "runs the ColPali or hybrid query for a ranking and returns the formatted results",
"visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.query_vespa_colpali": "converts the query embedding to float and binary forms and sends the ColPali nearest-neighbour query to Vespa",
"visual-retrieval-colpali/src/backend/vespa_app.py::VespaQueryClient.get_suggestions": "queries Vespa for questions matching a prefix and returns the distinct ones",
"visual-retrieval-colpali/prepare_feed_deploy.py::generate_embeddings": "runs the ColPali model over the images and returns one embedding array",
"visual-retrieval-colpali/prepare_feed_deploy.py::float_to_binary_embedding": "converts each float query vector to packed binary form",
"visual-retrieval-colpali/vespa_feed_to_hf_dataset.py::save_image": "decodes a base64 image and saves it to a file",
"visual-retrieval-colpali/src/main.py::get_and_store_sim_maps": "queries the similarity maps, waits for the images, and writes one PNG per image and token",
"visual-retrieval-colpali/src/main.py::fetch_results": "route handler ('/fetch_results') that computes the ColPali query embeddings for the query and runs the search",
"visual-retrieval-colpali/src/main.py::get_suggestions": "route handler that returns query suggestions from Vespa for a prefix",
"visual-retrieval-colpali/src/main.py::message_generator": "streams the Gemini answer as server-sent events after waiting for the result images",
"visual-retrieval-colpali/src/main.py::get_sim_map": "returns a ready similarity-map button or a polling button for one token",
"visual-retrieval-colpali/src/main.py::full_image": "returns a full-resolution image for a document, from disk or from Vespa",
"visual-retrieval-colpali/src/frontend/app.py::SearchResult": "builds the result cards, with a similarity-map button per token, for a list of hits",
"visual-retrieval-colpali/src/frontend/app.py::ChatResult": "builds the chat panel, which streams the answer only when there are document ids",
"visual-retrieval-colpali/src/frontend/app.py::SimMapButtonPoll": "builds a disabled spinner button that polls for its similarity map every half second",
"reverse-image-search/script/feed.py::run": "embeds each image of a split with the model and feeds the documents to Vespa in batches",
}
step1 = [json.loads(l) for l in open("/home/javad/energy-run/sample-apps/step1.jsonl")]
missing_what = [r["unit"] for r in step1 if r["unit"] not in WHAT]
print("units:", len(step1), "missing what_it_does:", missing_what)
out = []
problems = []
for r in step1:
    decs = []
    for s in r["suspicions"]:
        key = (r["unit"], s["label"])
        if key not in D:
            problems.append(key); continue
        verdict, why = D[key]
        decs.append({"label": s["label"], "root_cause": s["root_cause"], "lines": s["lines"],
                     "verdict": verdict, "why": why})
    out.append({"step": 2, "unit": r["unit"], "what_it_does": WHAT.get(r["unit"], ""), "decisions": decs})
print("problems:", problems)
if not missing_what and not problems:
    with open("/home/javad/energy-run/sample-apps/step2.jsonl", "w") as f:
        for rec in out: f.write(json.dumps(rec) + "\n")
    print("written", len(out))
