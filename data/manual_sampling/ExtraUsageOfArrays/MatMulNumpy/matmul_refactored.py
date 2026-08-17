import numpy as np



def matrix_multiplication(mat_a: list[list], mat_b: list[list]) -> list[list]:
    return np.array(mat_a) @ np.array(mat_b)


np.random.seed(42)
a = np.random.rand(150, 300).tolist()
b = np.random.rand(300, 450).tolist()
for i in range(10):
    result = matrix_multiplication(a, b)