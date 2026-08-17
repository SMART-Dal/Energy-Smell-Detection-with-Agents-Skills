def is_str_palindrome(string: str) -> bool:
    if len(string) % 2 != 0:
        return False
    start = 0
    end = len(string) - 1
    while start < end:
        if string[start] != string[end]:
            return False 
        start += 1
        end -= 1
    return True



first_half = "a" * 1000 + "b"
second_half = first_half[::-1]
string = first_half + second_half


for _ in range(100_000):
    a = is_str_palindrome(string)