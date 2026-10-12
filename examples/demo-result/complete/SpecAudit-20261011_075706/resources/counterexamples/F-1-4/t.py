def run(L, start):
    L = list(L); n = len(L); c = 0
    for i in range(1, n):
        a = start(i)
        for j in range(a, n):
            c += 1
            if L[j-1] > L[j]:
                L[j-1], L[j] = L[j], L[j-1]
    return L, c
print(run((2,3,1), lambda i: 1), run((2,3,1), lambda i: i))
print(run((5,4,3,2,1), lambda i: 1)[1], run((5,4,3,2,1), lambda i: i)[1])
