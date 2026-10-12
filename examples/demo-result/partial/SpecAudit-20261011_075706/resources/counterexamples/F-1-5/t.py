L=[3,1,2]; n=3
for j in range(1,n):
    if L[j-1]>L[j]: L[j-1],L[j]=L[j],L[j-1]
    print("after comparison at j=",j,L)
