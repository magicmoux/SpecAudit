def pas(L,a,b):
    L=list(L)
    for j in range(a,b):
        if L[j-1]>L[j]: L[j-1],L[j]=L[j],L[j-1]
    return L
def alg(L,start):
    L=list(L);n=len(L)
    for i in range(1,n):
        L=pas(L,start(i),n)
    return L
print(pas((2,3,1),1,3))
print(alg((2,3,1),lambda i:1), alg((2,3,1),lambda i:i))
import itertools
bad=[p for p in itertools.permutations(range(4)) if alg(p,lambda i:i)!=sorted(p)]
print(len(bad),bad[:3])
