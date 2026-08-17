

def matrix_multiplication(mat_a: list[list], mat_b: list[list]) -> list[list]:
    mul_res = []
    for row in range(len(mat_a)):
        tmp_res = []
        for col in range(len(mat_b[0])):
            nums = []
            for k in range(len(mat_b)):
                nums.append(mat_a[row][k] * mat_b[k][col])
            tmp_res.append(sum(nums))
        mul_res.append(tmp_res)
    return mul_res


import numpy as np
np.random.seed(42)
a = np.random.rand(150, 300).tolist()
b = np.random.rand(300, 450).tolist()
for i in range(10):
    result = matrix_multiplication(a, b)


