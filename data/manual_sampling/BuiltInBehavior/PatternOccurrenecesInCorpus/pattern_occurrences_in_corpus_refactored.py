def pattern_occurrences_in_corpus(pattern: str, corpus: str) -> list:
    curr_idx = corpus.find(pattern)
    result = []
    while curr_idx != -1:
        result.append(curr_idx)
        curr_idx = corpus.find(pattern, curr_idx + 1)
    return result


for _ in range(3):
    a = pattern_occurrences_in_corpus("abc", "abc" * int(1e7))