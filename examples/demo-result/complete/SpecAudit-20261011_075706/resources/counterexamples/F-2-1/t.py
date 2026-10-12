import itertools
def pas(L,a,b):
    for j in range(a,b):
        if L[j-1]>L[j]: L[j-1],L[j]=L[j],L[j-1]
def alg(L,shrink):
    L=list(L);n=len(L)
    for i in range(1,n):
        pas(L,1,n-i+1 if shrink else n)
    return L
c=0
for n in range(0,8):
    for L in itertools.product(range(4),repeat=n):
        A=alg(L,False);B=alg(L,True)
        assert A==sorted(L)==B
        # after pass n-1: positions 2..n hold n-1 largest increasing; pos1 <= pos2
        if n>=2: assert A[0]<=A[1]
        c+=1
print("ok",c)
