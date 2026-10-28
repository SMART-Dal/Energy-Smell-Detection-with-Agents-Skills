The function builds a Vespa query using qb (querybuilder). It doesn't need network. Just builds a dict. Let's write cases.

We need to import from collect_pyvespa. The module imports vespa. Assume available.

The function is cheap - builds a string. It takes query_text, top_k, query_id. Realistic query texts. Need 8 cases with varied query text lengths, special characters, top_k variations, query_id.

Work per call is small (string building). But that's fine—the function is what it is. We can make query texts long to increase work.

Note: query_text is embedded in the yql string. Long text increases work.

Let's make checks: empty string, None query_id, top_k=0 or negative? Just edge cases that may raise... probably won't raise.

Let's write.

Note that qb.nearestNeighbor might raise on certain characters? Probably fine. Let's use realistic text.

Let's generate random query texts with a seed. Include special chars like quotes, parentheses which might break the query builder? The userQuery embeds query text into YQL. Quotes might cause issues... The builder probably just concatenates. Let's be safe with varied but reasonable text — include punctuation.

Let me be careful: userQuery with quotes inside - if the builder escapes, fine. If not, still produces a string. Shouldn't raise. Let's test mentally—qb is vespa.querybuilder. userQuery likely wraps in a template. Hmm, risk. Let's include a case with quotes but be prepared... Actually we can't test. Safer to include punctuation that's common in queries: commas, apostrophes, hyphens. Let's avoid double quotes maybe. Actually including them tests different paths. Let's include a moderate case with an apostrophe.

I'll keep it simple and robust.

Cases (8):
1. short simple query, default top_k
2. long multi-sentence query, top_k=50
3. query with numbers and special chars, top_k=100
4. very long query (5000 chars), top_k=1000
5. unicode query, top_k=1
6. query_id set, top_k=10
7. query with newlines/tabs
8. long random words query, top_k=500

Make them varied.

Let me write module-level helper to build query strings.

For checks: empty string; query_id=None explicit; top_k=0.

Actually checks should be small edge inputs. Fine.

Write code.