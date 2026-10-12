def run(L, start):
    L = list(L); n = len(L)
    for i in range(1, n):
        a = i if start else 1
        for j in range(a, n):
            if L[j-1] > L[j]: L[j-1], L[j] = L[j], L[j-1]
    return L
print(run([3,2,1], False), run([3,2,1], True))
import itertools
ok = True
for n in range(1, 6):
    for L in itertools.permutations(range(n)):
        L = list(L); M = list(L)
        for i in range(1, n):
            for j in range(1, n):
                if M[j-1] > M[j]: M[j-1], M[j] = M[j], M[j-1]
            if M[n-i:] != sorted(L)[n-i:]: ok = False
print("lemma3 holds", ok)
