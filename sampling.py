import time

l = list(range(10_000_000))
runs = 10

# Test Generator Expression: sum(x for x in l)
start = time.perf_counter()
for _ in range(runs):
    sum(2 * x for x in l)
gen_time = time.perf_counter() - start

# Test List Comprehension: sum([x for x in l])
start = time.perf_counter()
for _ in range(runs):
    sum([2 * x for x in l])
list_time = time.perf_counter() - start

print(f"Generator expression : {gen_time:.4f} s (total for {runs} runs)")
print(f"List comprehension   : {list_time:.4f} s (total for {runs} runs)")