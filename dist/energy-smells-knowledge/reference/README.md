# The taxonomy, in full

Twelve categories, sixty-five root causes. This index exists so that a category
can be chosen deliberately rather than recalled.

Read a category card before its root-cause cards. The category card says what
kind of waste the group is about and lists its members with a line each, which
is usually enough to drop most of them.

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

Cards live at `reference/categories/<ID>.md` and
`reference/root-causes/<ID>.<S>.md`.

## Using this well

**Any category may apply to any code.** Nothing about a repository rules a
category in or out in advance. Work from what the code actually does.

**Read the card, not the name.** These names are three or four words long and
several of them cover something narrower — or wider — than they sound like.
The name is an index entry; the card is the claim.

**The taxonomy is a vocabulary, not a checklist.** Its job is to let you say
precisely what is wrong and what would fix it, once you have found something.
It is not a list of things to go looking for one by one, and finding nothing in
a category is a perfectly ordinary outcome.

**Cards overlap, and neighbours are listed for that reason.** When two root
causes both seem to fit, open both and pick the one whose repair is the edit
you would actually make. If you are stuck — the code is clearly wasteful and no
card quite describes it — the neighbour lists are the fastest way to the ones
worth trying next.

## What tools can and cannot contribute

Any static rule, in any tool, recognises a syntactic shape that somebody
described in advance. That makes rules dependable about the shapes they know
and completely blind to everything else. Two consequences, and they point in
opposite directions:

- **A rule firing has observed a pattern, not diagnosed a problem.** Every
  pattern in this taxonomy is the right thing to write somewhere, which is what
  each card's `NOT a smell when` and `Looks the same, is not` sections record.
- **A rule staying quiet has observed nothing.** Waste that lives in the
  arrangement of a program — work computed and discarded, a data shape that
  forces every later step to compensate, a query issued once per row — has no
  fixed syntactic shape at all, and is usually the expensive kind.

Reading the code is the primary method here. Anything a tool tells you is a
second opinion to reconcile with what you already worked out.
