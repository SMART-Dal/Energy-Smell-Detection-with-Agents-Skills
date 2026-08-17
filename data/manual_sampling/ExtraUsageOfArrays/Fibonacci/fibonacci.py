def fib(n):
    l = [0, 1]
    for _ in range(n - 1):
        l.append(l[-1] + l[-2])
    return l[-2]


for i in range(10000):
    a = fib(i)
    
