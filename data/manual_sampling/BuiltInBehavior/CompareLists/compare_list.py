def compare_list(lst_a: list[int], lst_b: list[int]):
    for a, b in zip(lst_a, lst_b):
        if a != b:
            return False
    return True


lst_a = [1] * 100_000 + [2]
lst_b = [1] * 100_000 + [3]
for _ in range(300):
    a = compare_list(lst_a, lst_b)
