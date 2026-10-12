def alg7(L):
    L=list(L);n=len(L);c=0
    for i in range(1,n):
        for j in range(i,n):
            c+=1
            if L[j-1]>L[j-1+1]: L[j-1],L[j]=L[j],L[j-1]
    return L,c
print(alg7((3,2,1)))
