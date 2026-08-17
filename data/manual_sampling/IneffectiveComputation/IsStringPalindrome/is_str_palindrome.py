def is_str_palindrome(string: str) -> bool:
    if len(string) % 2 != 0:
        return False
    return string == string[::-1]



first_half = "a" * 10000 + "b"
second_half = first_half[::-1]
string = first_half + second_half


for _ in range(100_000):
    a = is_str_palindrome(string)