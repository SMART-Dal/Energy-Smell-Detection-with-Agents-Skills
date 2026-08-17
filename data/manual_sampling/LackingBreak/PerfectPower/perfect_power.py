def perfect_power(x):
    c = 1
    for b in range(1, x):
        for p in range(2, x):
            if b**p <= x:
                c = max(c, b**p)
    return c


b = perfect_power(int(1.2e3))
a = perfect_power(int(1.1e3))
