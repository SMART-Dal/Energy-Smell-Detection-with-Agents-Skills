# What the 92 hand-built sample pairs actually teach

Read from `data/manual_sampling/`. These are the project owner's own before/after
pairs. Several are deliberately *reversed* — the "refactored" side is the hand
loop and the "before" side is the built-in — because the owner was probing where
the received wisdom breaks. Those are the valuable ones.

Measured figures come from the completed sample run (`validation/results/`);
`floor` is the null-canary reading for that run, and anything not clearing its
floor is marked inconclusive and must not be written into a card as fact.

---

## 1. `map` vs comprehension is decided by the callable, not by taste

| Sample | Direction | Measured |
|---|---|---|
| `ChangeListElementsType` | `[float(i) for i in lst]` → `list(map(float, lst))` | **+46.8% ± 4.3** (floor 4.0) |
| `SumMap2` | `sum(map(lambda x: x*2, l))` → `sum([x*2 for x in l])` | inconclusive, same direction as below |
| `SumFilterMap` | `map(lambda …)` inside a comprehension → nested comprehension | **+24.6% ± 1.5** (floor 0.8) |

`map` avoids the interpreter loop only when the callable is C-level. With a
`lambda` or a Python `def`, every element pays a frame push, and `map` loses to
a comprehension whose body is inlined bytecode.

**The rule: `map(f, xs)` beats a comprehension iff `f` is a C builtin.**
`map(float, xs)`, `map(str, xs)`, `map(len, xs)`, `map(operator.itemgetter(0), xs)`
— yes. `map(lambda x: x*2, xs)` — no.

## 2. A list comprehension can beat a generator expression

`SumMap1`: `sum((x*2 for x in l))` → `sum([x*2 for x in l])`, +22.1% ± 0.6 on a
51% floor (inconclusive, but the interval is tight and the direction is
consistent).

For a short pipeline consumed once by a C-level consumer, generator resumption
costs more per element than the allocation saves. The generator wins on memory,
on long pipelines, and when the consumer may stop early — not automatically on
energy.

This contradicts the taxonomy text for C6.S3, which says to prefer a generator
"when the result is consumed exactly once". The card needs the qualification.

## 3. Adding a conversion sometimes helps — and the direction flips per method

Two samples that look like the same edit and go opposite ways:

- `UnnecessaryTypeConversion/FindCommonItems`:
  `set(a).intersection(set(b))` → `set(a).intersection(b)` — **drop** the conversion.
- `ImproperDataStructure/DifferenceOnTwoLists1`:
  `set(a).difference(b)` → `set(a).difference(set(b))` — **add** one.

`set.intersection` iterates its argument and probes the set, so a list argument
is fine and the extra `set()` is pure cost. `set.difference` benefits from a
hashed argument. The *edit* is identical; only the receiving method differs.

This is the best available counter-example for C5.S4: "a conversion whose result
is used as the original would have been" is not the same as "a conversion that
buys nothing".

## 4. A built-in is not automatically the answer — four cases where it loses

- **`OveruseOfLoops/OccurenceOfOddItems1`** (deliberately reversed):
  `Counter(lst)` then filter to odd keys → hand loop that `continue`s on even.
  The data is 100 even values repeated 60 000 times plus a handful of odd ones.
  `Counter` counts all 6 000 000 elements and the filter throws almost all of it
  away. **This is the owner's own point: when only a slice of the data is
  needed, handing the whole thing to a bulk primitive is the waste.**
- **`OveruseOfLoops/SumMaxSubsequence`**: `curr_max = max(curr_max, curr_sum)` →
  `if curr_sum > curr_max: curr_max = curr_sum`. Built-ins win on *bulk*; on two
  scalars per iteration `max` pays a call and a tuple where the comparison is
  one bytecode.
- **`IneffectiveComputation/AreListsEqual`**: `''.join(a) == ''.join(b)` →
  element-wise loop with early return. The join materialises ~1 GB; the loop
  returns at the first mismatch.
- **`BuiltInBehavior/ItemCounts`**: hand-rolled tally → `Counter`, measured
  **−4.5%** (floor 10.0, inconclusive) — the built-in did not obviously win even
  on data where it should.

## 5. `isinstance` is slower than `type(x) == C`

`AddOnSpecificType`, measured **−5.4%** on a clean-ish floor. `isinstance` has
to walk the MRO; `type(x) == C` is a pointer compare.

The style advice is about **semantics** — `isinstance` accepts subclasses, and
that is usually what you want. It is not an energy improvement, and C10.S2 must
not claim it is.

## 6. Deduplicate before filtering, when duplicates are dense

`GreaterThanK2`, `UniqueDivisbleByK2`: `{x for x in lst if x > k}` →
`s = set(lst); {x for x in s if x > k}`.

1 000 000 elements drawn from 101 distinct values: one hashing pass replaces
999 899 redundant comparisons. **Only** a win when the duplicate ratio is high;
on unique data it is a pure extra pass. Good `NOT a smell when` material.

## 7. Triangular iteration is not automatically better

`PrimeToEachOther` and `DifferenceBetweenNumbers3` halve the work with
`for j in range(i+1, n)` plus a symmetric write — the case the C3.S4 description
explicitly mentions.

But `DifferenceBetweenNumbers4` is the **reverse**: triangular-with-append →
full n² with pre-sized rows. Two appends per pair onto n separately-growing
lists costs more than n² contiguous writes. Halving the *comparisons* while
doubling the *allocations* is not a win.

## 8. Algebraic guards — the interesting form of "redundant conditional"

- `IneffectiveComputation/CountAbsLessThanZero`: `abs(x) + k > 0` is
  unconditionally true when `k > 0`, so `if k > 0: return len(lst)` skips the
  whole scan.
- `UnnecessaryConditionals/DifferenceWithMax`: `abs(k - lst1[i])` where
  `k = max(lst1[i], lst2[i])`, so the difference is never negative and `abs` is
  dead weight on every element.
- `UnnecessaryConditionals/FloorCeil`: `if ceil < k and floor < k` — `floor <=
  ceil` always, so the second test cannot fail when the first passes.
- `UnnecessaryConditionals/InsideRange`: four branches collapsing to
  `return low <= x <= high`.

None of these is syntactic duplication. Each needs a fact about the domain,
which is exactly why a static rule cannot find them and an agent can. Use these
for C4.S2 and C7.S5 rather than `if items: if items:`.

## 9. Work whose result is discarded

`IneffectiveComputation/LogitsClassifier`: computes a full softmax over
1 000 000 logits, then returns only `argmax`. Softmax is monotonic, so
`argmax(softmax(x)) == argmax(x)` and the entire softmax is dead. The whole
helper disappears.

This is what C1.S5 should be showing — not `expensive_format(data)` with the
result unassigned.

## 10. Two independent `if`s → `elif` needs a proof

`LessAndGreaterThanBound` only permits the `elif` because the function opens
with `assert upper_bound > lower_bound`. Without that assertion the branches are
not exclusive and the edit changes behaviour. C4.S4's `How to tell` has to make
that the load-bearing step.

## 11. Memoisation, when the key space is much smaller than the input

- `IdentifyListPrimes`: 1 000 000 values drawn from 0-500, `is_prime` per
  element → dict cache. Measured **+95%**.
- `PrimesToEachTwoList`: same shape, plus normalising `(x, y)` to `(min, max)`
  so the cache key is order-independent — a detail that doubles the hit rate.
- `IsCyclic`: adds a third node state so a subtree is not re-explored. Same idea
  expressed as an algorithm change rather than a cache.

## 12. Other confirmed, high-effect pairs (use as examples freely)

`[0]*n` over `[0 for _ in range(n)]`; `s*n` over `"".join([s]*n)` (+98.7%);
`lst[::2]` over an index comprehension; `lst[::-1]` over `list(reversed(lst))`;
`min(l)`/`max(l)` over a hand scan (+48%); `sum(l)` over a `+=` loop;
`corpus.find` over a sliced-window scan; `res.extend(lst2)` over an append loop;
`zip(a, b)` over `range(len(a))` indexing; `d.items()` over `k in d` + `d[k]`;
iterative factorial over recursion (+39.5%); hoisting a set literal out of a
loop; one buffered `write` over 1 000 000 line writes; `x * 3` over `x * 3.0`
on integer data (**+39.0% ± 0.5**, floor 1.2).

## 13. Pairs that are not behaviour-preserving

Split by *why*, because the two halves need different treatment:

**Same answer, different side effect** — legitimate with `EQUIVALENCE =
"returns_only"` and a note about the call sites:
`SumTopK` (`lst.sort()` mutates the caller's list), `MergeLists`
(`lst1.extend`), `OperatingOnList2` (rewrites the input in place).

**Different answer** — genuinely not equivalent, and must stay rejected:
`DifferenceBetweenNumbers` (dict of lists vs list of lists),
`GreaterThanK` (set vs list), `FindMultipleItems` (indices vs values),
`OccurenceOfOddItems2`/`3` (off-by-one in the seeded counts),
`MatMulNumpy` (numpy float array vs list of ints).

## 14. Two samples that are not smell pairs

`SleepExecution` replaces a matmul with `time.sleep(4)` — a probe of whether the
meter charges for idle time, not a refactoring. `MatMulParallel` sends a 500×500
matrix to every worker task, so pickling dominates; useful as a C11.S5
counter-example, not as a positive one.
