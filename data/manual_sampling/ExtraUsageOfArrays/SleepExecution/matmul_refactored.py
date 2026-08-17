import time


def tmp_func():
    for _ in range(4):
        time.sleep(1)


import numpy as np

np.random.seed(42)
a = np.random.rand(150, 300).tolist()
b = np.random.rand(300, 450).tolist()
for i in range(2):
    result = tmp_func()
