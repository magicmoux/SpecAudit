/-- Definition 2: the first `min k L.length` elements of the sorted list. -/
def P (k : Nat) (L : List Int) : List Int :=
  (L.mergeSort (· ≤ ·)).take k
