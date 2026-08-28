# Looks the same, is not

Thirty-three specimens. Each one matches its root cause on sight, and each one
is code where applying that root cause's repair is **wrong** -- the output
changes, or the function raises.

They are **not** case files and `validation/run.py` must never see them. A
paired energy measurement compares two programs that compute the same answer;
these pairs do not, so there is no number to take. The evidence here is the
behaviour, which is stronger than a percentage anyway.

## What they are for

**1. The `Looks the same, is not` section of each root-cause card.** Every file
carries the pattern, the repair, the input that separates them, and the rule the
reader should apply instead. That prose is the card text.

**2. Negative fixtures for the analyzer rules.** `tests/rules/<rule>/test_cases.py`
already works this way: a unit that is not named in `EXPECTED` must come back
with nothing, so appending one of these `before` functions asserts that the rule
does not fire on it.

Sixteen were tried. **Thirteen passed** -- the rule already tells the difference
and now has a test saying so. They are marked (fixture) below. Three did not,
and that is the more useful half of the result: they are distinctions no rule
can draw from the syntax, so the caveat belongs on the card rather than in the
analyzer.

| specimen | rule that fires | what it cannot see |
|---|---|---|
| `C8S4_lookalike` | `io_call_in_loop` | that another writer appends to the file during the call |
| `C2S2_lookalike` | `method_ignores_self` | that a subclass overrides the method -- though this one *is* visible in the same module, so the rule could be taught it |
| `C8S3_lookalike` | `repeated_lookup_in_loop` | that a method called in the loop writes the attribute the chain reads -- also arguably teachable, by treating a call on the chain's prefix as a write |

The specimens that land on a rule we ship:

| specimen | rule that must stay quiet | why it is not that smell |
|---|---|---|
| `C1S1_lookalike` (fixture) | `dead_initialization` | the discarded value came from `list.pop`, which also mutates |
| `C1S3_lookalike` | `redundant_bool_branch` | the condition is not a bool, so the branch is normalising it |
| `C1S4_lookalike` (fixture) | `repeated_pure_call` | the receiver is appended to between the two calls |
| `C2S1_lookalike` (fixture) | `trivial_delegation` | the property computes and memoises on first access |
| `C2S2_lookalike` | `method_ignores_self` | a subclass overrides it, so it is the dispatch point |
| `C3S2_lookalike` (fixture) | `loop_invariant_expression` | the expression reads the container the loop is filling |
| `C3S5_lookalike` (fixture) | `missing_early_exit` | the loop appends on a match; it is a fold, not a search |
| `C4S1_lookalike` (fixture) | `expensive_operand_first` | the cheap operand is the guard that makes the second safe |
| `C4S4_lookalike` (fixture) | `independent_exclusive_ifs` | the conditions overlap, so `elif` drops arms |
| `C4S5_lookalike` | `expensive_comparison` | `bool` is a subclass of `int`; identity checks lose it |
| `C5S4_lookalike` (fixture) | `redundant_materialisation` | the sequence is consumed twice |
| `C6S1_lookalike` (fixture) | `construction_in_loop` | the per-iteration object is retained by the caller |
| `C6S2_lookalike` (fixture) | `copy_in_loop` | the caller reads the original order after the copy |
| `C6S3_lookalike` (fixture) | `eager_comprehension` | the consumer needs a length as well as a sum |
| `C6S6_lookalike` (fixture) | `unmanaged_resource` | the handle is the return value |
| `C8S2_lookalike` | `loop_invariant_expression` | the parsed document is mutated per request |
| `C8S3_lookalike` | `repeated_lookup_in_loop` | the loop calls something that writes the attribute |
| `C8S4_lookalike` | `io_call_in_loop` | the file is appended to by another writer during the call |
| `C10S5_lookalike` (fixture) | `global_lookup_in_loop` | the loop calls something that rebinds the global |

The remaining fifteen -- `C1S2`, `C1S5`, `C3S6`, `C3S7`, `C4S2`, `C4S8`, `C5S3`,
`C7S5`, `C8S1`, `C9S2`, `C9S4`, `C10S6`, `C12S3`, `C12S4` -- describe traps no
rule we ship looks for. They are card material only.

## What is not here

A specimen where the repair keeps the answer and costs energy anyway is not a
look-alike; it is a measurable adversarial case, and those live in
`validation/taxonomy/` beside the shapes they contradict, so that a number can
be put on them. `C10S1_builtin_counts_everything.py` is the archetype.
