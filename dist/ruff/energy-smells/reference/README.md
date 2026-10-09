# The taxonomy, in full

Twelve categories, sixty-five root causes.

Two indexes follow, and they are for different moments. The **category table**
is for choosing where to look: open a category card, and it lists its members
with a line each, which is usually enough to drop most of them. The **root
cause table** below it is the whole taxonomy on one page, for the sweep at the
end of step 2 — reading it against code you have already formed a view about,
to catch what you noticed and could not name.

Cards live at `reference/categories/<ID>.md` and
`reference/root-causes/<ID>.<S>.md`.

## Categories

| ID | Category | Covers | Card |
|---|---|---|---|
| **C1** | Redundant Computation | Energy waste from executing work that does not contribute to the program's required output or that leaves program state unchanged | `reference/categories/C1.md` (8) |
| **C2** | Unnecessary Call Overhead | Energy waste from extra layers of function calls, method delegation, or dynamic dispatch that add overhead without proportional benefit | `reference/categories/C2.md` (3) |
| **C3** | Inefficient Iteration Patterns | Energy waste from loops that perform more per-iteration work than necessary, iterate more times than required, use suboptimal loop constructs, or fail to terminate correctly | `reference/categories/C3.md` (7) |
| **C4** | Inefficient Control Flow | Energy waste from branching, conditions, or dispatch logic that performs unnecessary checks, uses suboptimal evaluation order, or employs patterns that prevent interpreter optimization | `reference/categories/C4.md` (8) |
| **C5** | Suboptimal Data Structures | Energy waste from choosing, provisioning, or converting data structures that do not match the workload's access pattern or size requirements | `reference/categories/C5.md` (4) |
| **C6** | Unnecessary Memory Usage | Patterns that allocate, copy, retain, or leak memory beyond what the workload requires, increasing garbage collection overhead, memory-bus traffic, and system energy consumption | `reference/categories/C6.md` (7) |
| **C7** | Suboptimal Algorithmic | Energy waste from choosing an algorithm, decomposition, or computation strategy that explores more of the problem space than necessary or uses higher complexity than the problem requires | `reference/categories/C7.md` (5) |
| **C8** | Missing Reuse | Energy waste from failing to store and reuse results of expensive computations, lookups, or data fetches, causing the same work to be repeated across calls, requests, or access sites | `reference/categories/C8.md` (4) |
| **C9** | Inefficient External Data Access | Energy waste from inefficient interaction with external systems: databases, file systems, network services, and APIs | `reference/categories/C9.md` (4) |
| **C10** | Underused Language Primitives | Energy waste from not using available optimized language features, standard library functions, or runtime-specific constructs that would accomplish the same task more efficiently | `reference/categories/C10.md` (6) |
| **C11** | Inefficient Concurrency Management | Energy waste from thread/task misuse, synchronization overhead, contention, or failure to exploit available parallelism | `reference/categories/C11.md` (5) |
| **C12** | Poor Hardware Locality Usage | Energy waste driven by CPU and memory hierarchy behavior such as cache misses, branch misprediction, and suboptimal memory access patterns | `reference/categories/C12.md` (4) |

## Every root cause, one line each

### C1 — Redundant Computation

| ID | Name | Looks for |
|---|---|---|
| **C1.S1** | Dead Code | a value computed and bound to a name that nothing ever reads |
| **C1.S2** | Redundant Assignment | a store that leaves the program's state exactly as it already was |
| **C1.S3** | Redundant Control Flow | a branch whose outcome is the same whichever way it goes |
| **C1.S4** | Repeated Computation | the same value computed twice in one scope, where one local would serve both |
| **C1.S5** | Resultless Computation | a computation run in full whose result nothing downstream actually needs |
| **C1.S6** | Unnecessary Initialization | setup done unconditionally that only one path actually needs |
| **C1.S7** | Unnecessary Variable | a name bound, read exactly once, and never needed again |
| **C1.S8** | Excessive Runtime-Management Calls | runtime housekeeping invoked far more often than anything needs it |

### C2 — Unnecessary Call Overhead

| ID | Name | Looks for |
|---|---|---|
| **C2.S1** | Unnecessary Method Delegation | a wrapper or property that forwards, adds nothing, and sits on a hot path |
| **C2.S2** | Missing Static Declaration | a method that never touches `self` and still pays to be bound to an instance |
| **C2.S3** | Excessive Modularization in Hot Path | a chain of thin layers whose frames cost more than the work at the bottom |

### C3 — Inefficient Iteration Patterns

| ID | Name | Looks for |
|---|---|---|
| **C3.S1** | Inefficient Iteration Construct | a loop written in a form that does more interpreter work per element than it needs to |
| **C3.S2** | Recomputing Loop-Invariant Values | an expression recomputed every iteration whose answer never changes |
| **C3.S3** | Inefficient Per-Iteration Setup | an object or resource created once per iteration that the whole loop could share |
| **C3.S4** | Inefficient Nested Iteration | an inner loop that searches, where a lookup would turn n*m into n+m |
| **C3.S5** | Missing Loop Early Exit | a loop that keeps going after its answer is already settled |
| **C3.S6** | Unfiltered Bulk Iteration | the whole collection processed when only a subset was ever wanted |
| **C3.S7** | Inefficient Array Mutation in Loop | a collection edited while it is being walked |

### C4 — Inefficient Control Flow

| ID | Name | Looks for |
|---|---|---|
| **C4.S1** | Poor Short-Circuit Ordering | a boolean chain that evaluates its expensive operand before the cheap one that usually decides |
| **C4.S2** | Redundant Conditional Evaluation | a test whose answer was already settled before it ran |
| **C4.S3** | Inefficient Conditional Nesting | a nest or chain of branches that tests more than it has to, where a lookup would test once |
| **C4.S4** | Missing Else-If | consecutive `if`s on one subject that are exclusive in fact but not in form |
| **C4.S5** | Expensive Comparison | a type check made per element where the answer never varies or the types could dispatch themselves |
| **C4.S6** | Expensive Exception Control Flow | an exception used as ordinary control flow, on a path where it is raised often |
| **C4.S7** | Missing Edge-Case Guards | a missing cheap test that would let a common trivial input skip the expensive path |
| **C4.S8** | Non-Idiomatic Condition | a condition spelled the long way round, missing the interpreter's fast path |

### C5 — Suboptimal Data Structures

| ID | Name | Looks for |
|---|---|---|
| **C5.S1** | Inefficient Data Structure Choice | a container whose type makes its most frequent operation the expensive one |
| **C5.S2** | Missing Helper Type | a collection searched again and again where one index built beside it would answer every question |
| **C5.S3** | Over-Provisioned Data Type | a representation heavier than the data it holds actually requires |
| **C5.S4** | Unnecessary Representation Change | a conversion between representations that the code on either side did not need |

### C6 — Unnecessary Memory Usage

| ID | Name | Looks for |
|---|---|---|
| **C6.S1** | Unnecessary Object | objects created and thrown away that never needed to exist |
| **C6.S2** | Unnecessary Copying | data duplicated when the original could have been used or changed in place |
| **C6.S3** | Unnecessary Data Materialization | a whole sequence built in memory when the consumer wanted it one element at a time |
| **C6.S4** | Oversized Data Retaining | something long-lived holding far more data than anything later reads |
| **C6.S5** | Over-Allocation | capacity reserved up front for data that never arrives |
| **C6.S6** | Leaked Resource Handles | a file, socket or connection acquired with nothing guaranteeing its release |
| **C6.S7** | Leaking Mutable Default Arguments | a mutable default argument that quietly accumulates across every call |

### C7 — Suboptimal Algorithmic

| ID | Name | Looks for |
|---|---|---|
| **C7.S1** | Suboptimal Algorithm Choice | an algorithm of worse complexity than the problem requires |
| **C7.S2** | Inefficient Problem Decomposition | a search exploring subproblems it could have pruned, reordered or reused |
| **C7.S3** | Avoidable Recursive Implementation | a recursion paying a frame per level where a loop would use one |
| **C7.S4** | Inefficient Operation Ordering | two commuting operations in the order that makes the expensive one see more data |
| **C7.S5** | Unsimplified Operation | an operation doing more work than an algebraic fact about its inputs requires |

### C8 — Missing Reuse

| ID | Name | Looks for |
|---|---|---|
| **C8.S1** | Missing Memoization Cache | a deterministic computation repeated across calls that a cache would answer |
| **C8.S2** | Missing Derived-Value Reuse | an expensive artefact derived again on every use instead of once for the process |
| **C8.S3** | Missing Local Lookup Caching | a name or attribute chain re-resolved every iteration for a value that never moves |
| **C8.S4** | Redundant Data Fetching | the same external data fetched again when the copy in memory was still good |

### C9 — Inefficient External Data Access

| ID | Name | Looks for |
|---|---|---|
| **C9.S1** | Fragmented I/O Calls | many small independent external operations where one bulk operation would do |
| **C9.S2** | Oversized Data Retrieval | more data pulled across a process boundary than the program ever consults |
| **C9.S3** | Inefficient Retrieval Paths | one fetch per row of an earlier fetch, where a join would have taken one trip |
| **C9.S4** | Expensive Query Pattern | a query whose shape makes the engine do far more work than the answer needs |

### C10 — Underused Language Primitives

| ID | Name | Looks for |
|---|---|---|
| **C10.S1** | Skipping Optimized Built-ins | a hand-written loop doing bulk work a C-level primitive already does |
| **C10.S2** | Inefficient Built-in Choice | one primitive used where a cheaper primitive computes the same answer |
| **C10.S3** | Missing Bulk Primitive Usage | a per-element call inside a loop that a single batched call would replace |
| **C10.S4** | Inefficient String Concatenation | a string grown with `+=` in a loop, where the target is aliased or the parts are many |
| **C10.S5** | Inefficient Scope Lookup | a global or builtin re-resolved through the module namespace on every iteration |
| **C10.S6** | Expensive Operator Overloads | an operator on a user-defined type dispatching and allocating once per element |

### C11 — Inefficient Concurrency Management

| ID | Name | Looks for |
|---|---|---|
| **C11.S1** | Excessive Lock Contention | a lock held across work that shares nothing, serialising what could overlap |
| **C11.S2** | Forced Serial Bottleneck | concurrency paid for in full while one shared resource serialises all of it |
| **C11.S3** | Leaked Background Threads | workers started and never stopped, accumulating for the life of the process |
| **C11.S4** | Blocking The Main Thread | a synchronous blocking call inside a coroutine, stopping every other task |
| **C11.S5** | Missed Parallelism Opportunities | independent work run one item at a time when the waits could have overlapped |

### C12 — Poor Hardware Locality Usage

| ID | Name | Looks for |
|---|---|---|
| **C12.S1** | Inefficient Large-Stride Traversal | a contiguous buffer traversed against the direction its memory is laid out in |
| **C12.S2** | Sparse Element Access | scattered reads into a large buffer, using one element of every cache line fetched |
| **C12.S3** | Unpredictable Branches | a data-dependent branch in a compiled hot loop that the CPU cannot predict |
| **C12.S4** | Inefficient Array Declaration Order | a declared struct whose field order puts cold data in front of hot data |

## Using this well

**Any category may apply to any code.** Nothing about a repository rules a
category in or out in advance. Work from what the code actually does.

**Read the card, not the name, and not the line above.** These names are three
or four words long and several of them cover something narrower — or wider —
than they sound like. The one-line summaries here are index entries, precise
enough to recognise something by and not enough to decide anything from. The
card is the claim.

**The taxonomy is a vocabulary, not a checklist.** Its job is to let you say
precisely what is wrong and what would fix it, once you have found something.
Finding nothing in a category is a perfectly ordinary outcome.

**Cards overlap, and each one lists similar cards for that reason.** When two
root causes both describe what you repaired, either attribution is fine — say
which you chose. The similar lists matter most in the other case: the code is
clearly wasteful, the card you opened does not quite say why, and they are the
fastest route to the ones worth trying next.

## What tools can and cannot contribute

Any static rule, in any tool, recognises a syntactic shape that somebody
described in advance. That makes rules dependable about the shapes they know
and completely blind to everything else. Two consequences, and they point in
opposite directions:

- **A rule firing has observed a pattern, not diagnosed a problem.** Every
  pattern in this taxonomy is the right thing to write somewhere, which is what
  each card's `Looks like it, but is not` section records.
  Some of what any rule reports is therefore wrong here, and saying which is
  part of the job.
- **A rule staying quiet has observed nothing.** Waste that lives in the
  arrangement of a program — work computed and discarded, a data shape that
  forces every later step to compensate, a query issued once per row — has no
  fixed syntactic shape at all, and is usually the expensive kind.

Reading the code is the primary method here. Anything a tool tells you is a
second opinion to reconcile with what you already worked out.
