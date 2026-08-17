

def matmul(A, B):
    m = len(A)
    n = len(A[0])
    p = len(B[0])
    C = [[0 for _ in range(p)] for _ in range(m)]
    
    for i in range(m):
        for j in range(p):
            total = 0
            for k in range(n):
                total += A[i][k] * B[k][j]
            C[i][j] = total
    return C
    


import random
m, n, p = 500, 500, 500


A = [[random.random() for _ in range(n)] for _ in range(m)]
B = [[random.random() for _ in range(p)] for _ in range(n)]

if __name__ == "__main__":
    for _ in range(2):
        C = matmul(A, B)

