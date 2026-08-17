def is_str_palindrome(string: str) -> bool:
    if len(string) % 2 != 0:
        return False
    half = len(string) // 2
    first_half = string[:half]
    reversed_second_half = string[half:][::-1]
    return first_half == reversed_second_half



first_half = "a" * 1000 + "b"
second_half = first_half[::-1]
string = first_half + second_half


for _ in range(100_000):
    a = is_str_palindrome(string)