


def matrix_multiplication(mat_a: list[list], mat_b: list[list]) -> list[list]:
    mul_res = []
    for row in range(len(mat_a)):
        mul_row = []
        for col in range(len(mat_b[0])):
            tmp_sum = 0
            for k in range(len(mat_b)):
                tmp_sum += mat_a[row][k] * mat_b[k][col]
            mul_row.append(tmp_sum)
        mul_res.append(mul_row)
    return mul_res


import numpy as np
np.random.seed(42)
a = np.random.rand(150, 300).tolist()
b = np.random.rand(300, 450).tolist()
for i in range(10):
    result = matrix_multiplication(a, b)