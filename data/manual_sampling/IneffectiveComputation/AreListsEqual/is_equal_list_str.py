def is_equal_list_str(list_str1: list[str], list_str2: list[str]) -> bool:
    return ''.join(list_str1) == ''.join(list_str2)
lst1 = ["aaa" * 10_000] * 100_000
lst2 = ["aaa" * 10_000] * 100_000
for _ in range(3):
    a = is_equal_list_str(lst1, lst2)