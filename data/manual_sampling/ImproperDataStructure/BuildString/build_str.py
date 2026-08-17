def build_str(repetition_count, string):
    return "".join([string for _ in range(repetition_count)])


for _ in range(3):
    a = build_str(int(1e8), "a")