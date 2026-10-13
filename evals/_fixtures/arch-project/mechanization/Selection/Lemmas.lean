import Selection.Basic

/-- Lemma 3, as the paper states it. -/
theorem P_length (k : Nat) (L : List Int) : (P k L).length = min k L.length := by
  simp [P, List.length_take, List.length_mergeSort]

/-- Proposition 4. -/
theorem P_append (k : Nat) (L M : List Int) : P k (L ++ M) = P k (P k L ++ P k M) := by
  sorry
