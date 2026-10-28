The function under test calls network APIs: `resolve_validate_record_path` calls `dxpy.DXHTTPRequest`, `DXDataset(...).get_descriptor()` fetches a file, `raw_api_call` etc. These require network access to a DNAnexus server. There's no way to avoid that.

The task says: "A function whose work starts with a request to a server ... cannot run here". The function's core work is entirely network-based API calls to DNAnexus. We cannot run it.

So reply with `CANNOT RUN: ...`.