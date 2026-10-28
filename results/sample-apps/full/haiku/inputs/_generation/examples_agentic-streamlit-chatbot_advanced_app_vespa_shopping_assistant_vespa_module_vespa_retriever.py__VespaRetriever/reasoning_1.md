The function under test creates a Vespa app and does a query to a server. That requires network access. So it cannot run here.

Wait, let me check. `Vespa(url=VESPA_URL, ...)` then `vespa_app.query(...)`. This is a network request to a Vespa server. So CANNOT RUN.

Yes, reply CANNOT RUN.