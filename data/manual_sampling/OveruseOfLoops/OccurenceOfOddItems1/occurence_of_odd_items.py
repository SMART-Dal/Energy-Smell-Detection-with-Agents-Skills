from collections import Counter

def occurence_of_odd_items(lst: list):
    counter = Counter(lst)
    return {key: value for key, value in counter.items() if key % 2 == 1}



lst = [i for i in range(0, 200, 2)] * 60000
lst += [1,3,3,5,7,1,3,9,3]
import random
random.seed(1234)
for _ in range(50):
    a = occurence_of_odd_items(lst)