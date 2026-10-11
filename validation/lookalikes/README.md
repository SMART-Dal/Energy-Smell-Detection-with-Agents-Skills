# Looks the same, is not

Thirty-three specimens. Each one matches its root cause on sight, and each one
is code where applying that root cause's repair is **wrong** -- the output
changes, or the function raises.

They are **not** case files and `validation/run.py` must never see them. A
paired energy measurement compares two programs that compute the same answer;
these pairs do not, so there is no number to take. The evidence here is the
behaviour, which is stronger than a percentage anyway.

## What they are for

**1. The `Looks like it, but is not` section of each root-cause card.** Every
file carries the pattern, the repair, the input that separates them, and the
rule the reader should apply instead. The build reads the title, `before` and
`after` from the file; the card's one-line `why` summarises the docstring.

**2. Negative fixtures for the analyzer rules.** `tests/rules/<rule>/test_cases.py`
already works this way: a unit that is not named in `EXPECTED` must come back
with nothing, so appending one of these `before` functions asserts that the rule
does not fire on it.

Sixteen were tried. **Thirteen became fixtures** and the rules stay quiet on
them; they are marked (fixture) below. Twelve remain: `C10S5_lookalike` outlived
its rule (see below). The rest are the more useful half of
the result.

`C2S2_lookalike` found a real gap. `method_ignores_self` fired on a method that a
subclass in the same module overrides -- the decorator alone would be harmless,
but the repair that pays for it pins the call site to a class and skips the
override. The rule now consults `collect_overridden_methods`, and the specimen is
a fixture.

`C8S3_lookalike` did **not** find a gap, and it is worth writing down why. The
rule reported the chain `context.limiter` -- it has since stopped reporting
one-dot chains at all -- and hoisting *that* is safe: a local
bound to the object still sees every later write. What is unsafe is hoisting
`context.limiter.threshold`, the value -- which is what the specimen's `after`
does and what the rule never suggested. The caveat belongs on the card, and the
distinction it has to draw is object against value.

`C6S1_lookalike` outlived its rule. `construction_in_loop` reported every
container, lambda or constructor call built inside a loop, and it could not
tell the throwaway buffer from the object the caller keeps -- which is the
whole of C6.S1's own first counter-example. Most of what it did catch that was
real was a loop-invariant expression, which `loop_invariant_expression` already
reports. The rule is withdrawn; the specimen stays as card text.

`C10S5_lookalike` outlived its rule too. `global_lookup_in_loop` was withdrawn
in October 2026: the C10.S5 samples whose loop does any real work saved 2-9%,
on ten real repositories it reported loggers and helper functions called in a
loop, and it did not fire on its own measured samples. The specimen stays as
card text.

`C8S4_lookalike` is card-only for a reason nothing can fix: whether another
process appends to the file during the call is not in the syntax. `io_call_in_loop`
is right to raise it and the agent is the one who has to answer it.

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
| `C6S2_lookalike` (fixture) | `copy_in_loop` | the caller reads the original order after the copy |
| `C6S3_lookalike` (fixture) | `eager_comprehension` | the consumer needs a length as well as a sum |
| `C6S6_lookalike` (fixture) | `unmanaged_resource` | the handle is the return value |
| `C8S2_lookalike` | `loop_invariant_expression` | the parsed document is mutated per request |
| `C8S3_lookalike` | `repeated_lookup_in_loop` | the loop calls something that writes the attribute |
| `C8S4_lookalike` | `io_call_in_loop` | the file is appended to by another writer during the call |

The remaining fifteen -- `C1S2`, `C1S5`, `C3S6`, `C3S7`, `C4S2`, `C4S8`, `C5S3`,
`C6S1`, `C7S5`, `C8S1`, `C9S2`, `C9S4`, `C10S6`, `C12S3`, `C12S4` -- describe
traps no rule we ship looks for. They are card material only.

## What is not here

A specimen where the repair keeps the answer and costs energy anyway is not a
look-alike; it is a measurable adversarial case, and those live in
`validation/taxonomy/` beside the shapes they contradict, so that a number can
be put on them. `C10S1_builtin_counts_everything.py` is the archetype.
