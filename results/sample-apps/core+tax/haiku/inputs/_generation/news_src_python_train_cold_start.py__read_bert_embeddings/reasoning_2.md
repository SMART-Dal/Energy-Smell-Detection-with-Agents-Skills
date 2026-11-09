The issue: `read_bert_embeddings_from_file` does `print("Reading data from " + embeddings_file)` — concatenating str with PosixPath. So paths must be strings, not pathlib.Path.

Fix: convert to str.