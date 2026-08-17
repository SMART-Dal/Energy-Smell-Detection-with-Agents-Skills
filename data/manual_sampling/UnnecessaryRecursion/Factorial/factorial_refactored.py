def factorial(n):
    result = 1
    for i in range(1, n+1):
        result *= i
    return result
    

for i in range(10_000):
    a = factorial(800)