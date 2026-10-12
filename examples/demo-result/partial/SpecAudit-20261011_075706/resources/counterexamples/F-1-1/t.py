from itertools import permutations
def p(L,a):
    L=list(L)
    for j in range(a-1,len(L)-1):
        if L[j]>L[j+1]: L[j],L[j+1]=L[j+1],L[j]
    return L
print(p((2,3,1),1))
bad=0
for n in range(3,6):
    for L in permutations(range(1,n+1)):
        if p(L,1)[:1]!=[1]: bad+=1
print("violations i=1:",bad)
# Corollary 5 check: Alg 7 vs Alg 2
def a2(L,s):
    L=list(L)
    for i in range(1,len(L)):
        L=p(L,i if s else 1)
    return L
print([L for L in permutations(range(1,5)) if a2(L,0)!=a2(L,1)][:3])
print(a2((2,3,1),0), a2((3,1,2),1))
