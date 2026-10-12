from itertools import permutations
def run(L,grow):
    L=list(L);n=len(L)
    for i in range(1,n):
        a=i if grow else 1
        for j in range(a,n):
            if L[j-1]>L[j]: L[j-1],L[j]=L[j],L[j-1]
    return L
bad=[(p,run(p,0),run(p,1)) for n in range(2,6) for p in permutations(range(n)) if run(p,0)!=run(p,1)]
print(len(bad),bad[:3])
print(run((2,3,1),0),run((2,3,1),1))
