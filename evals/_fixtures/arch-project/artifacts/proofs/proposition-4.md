# Proof of Proposition 4

**Proposition 4.** For every integer k ≥ 0 and all lists L and M, P_k(L ++ M) = P_k(P_k(L) ++ P_k(M)).

*Proof.* Let x be an element of P_k(L ++ M) that comes from L. At most k − 1 elements of L precede x in
sort(L ++ M), so x is among the first k elements of sort(L), that is, in P_k(L). The same holds for M. Thus
P_k(L ++ M) is a sublist of P_k(L) ++ P_k(M), itself a sublist of L ++ M, and contains its smallest elements. ∎
