def build_string(addition_pattern: str, num_range: int) -> str:
    result = ""
    for x in range(num_range):
        if x % 7 == 0:
            result += addition_pattern
    return result

add_pattern = "abcde" * 1000
for _ in range(3):
    a = build_string(add_pattern, int(1.5e4))