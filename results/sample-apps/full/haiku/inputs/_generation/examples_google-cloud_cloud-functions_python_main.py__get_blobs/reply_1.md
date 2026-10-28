```python
CANNOT RUN: get_blobs calls google.cloud.storage.Client() and list_blobs(bucket), which performs an authenticated network request to Google Cloud Storage; no input can avoid it.
```