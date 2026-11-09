The function builds a YQL query string. It's pure string building. Very fast. But we need 8 cases with substantial work... The function itself is trivial. We need realistic inputs: query_text strings, top_k. But work is tiny — 1ms to 200ms is required roughly but not strictly? "One call should take roughly 1 ms to 200 ms on the original." Hmm, this function will take microseconds. We can't do much. But we should still provide cases; the measurement picks the 4 that do most work.

We can make query_text large to increase work — str formatting of the query text. Building a large query text with lots of characters. But the function just embeds query_text in dict. Large strings would make it slower. Let's make query_text large-ish, e.g., thousands of characters, but avoid huge output (output dict includes query text, under 100k values, fine).

Actually the YQL string is built each call by qb.select... .where(...) | ... — that's the actual work. That's fixed regardless of input. So all cases similar work. We can vary query_text length and top_k (top_k unused actually).

Let's write realistic cases: different query texts, various lengths, unicode, etc.

checks(): edge cases — empty string, None-ish? query_text must be str. Odd type maybe int. Empty string, one char, None (would produce "embed(None)"? Actually f"embed({None})" works fine, no raise). Let's include empty, single char, and a non-str int.

We need at least 8 cases. Let's build query texts of varying sizes.

Let me create:

def _text(n, seed): generate random words joined.

Cases:
- short query (typical)
- long document-ish query 5k chars
- unicode query
- very long 50k chars
- query with special characters / quotes
- numeric-heavy query
- multi-sentence
- top_k variations (top_k unused but pass different values)

Keep each under 100MB and output small. The output includes query text, so keep < 100_000 values — a string counts as one value probably. Fine.

Let's write it.

Module-level build the strings once.

I'll use random.Random(0).

Simple.

Note top_k is unused by function but include realistic values.

Let me write code.

def _rand_text(n, seed, vocab):
    rng = random.Random(seed)
    words = [rng.choice(vocab) for _ in range(n)]
    return " ".join(words)

vocab = list of words maybe built from a word list.

Cases with different sizes: 3 words, 20, 200, 1000, 5000, 10000 words; unicode; special chars.

That's 8.

Ensure each call ~ small time. Fine.

Write the final block.