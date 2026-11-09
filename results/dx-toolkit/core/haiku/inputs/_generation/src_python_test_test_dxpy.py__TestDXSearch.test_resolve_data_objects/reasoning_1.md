This function is a test method that requires network access / a running DNAnexus platform. It creates records via `dxpy.new_dxrecord`, uses `testutil.temporary_project`, etc. That's all server calls. It cannot run here.

The task says: "A function whose work starts with a request to a server (an HTTP client's get, a database query) cannot run here". This test method makes API calls to the DNAnexus platform.

Reply with CANNOT RUN.