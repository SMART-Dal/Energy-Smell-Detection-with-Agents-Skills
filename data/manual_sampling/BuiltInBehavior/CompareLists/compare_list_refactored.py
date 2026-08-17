def compare_list(lst_a: list[int], lst_b: list[int]):
    return lst_a == lst_b


lst_a = [1] * 100_000 + [2]
lst_b = [1] * 100_000 + [3]
for _ in range(30):
    a = compare_list(lst_a, lst_b)
