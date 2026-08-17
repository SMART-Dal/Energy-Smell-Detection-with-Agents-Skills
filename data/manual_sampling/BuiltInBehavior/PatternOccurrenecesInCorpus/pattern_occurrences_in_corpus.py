def pattern_occurrences_in_corpus(pattern: str, corpus: str) -> list:
    indices = []
    for i in range(len(corpus) - len(pattern) + 1):
        if corpus[i:i+len(pattern)] == pattern:
            indices.append(i)
    return indices


for _ in range(3):
    a = pattern_occurrences_in_corpus("abc", "abc" * int(1e7))

