# Archived catalog fields

Written by hand into `catalog/*.yaml` and rendered on the level-2 cards
until 2026-08-18, when three sections were withdrawn:

- `mechanism` and `how_to_tell` were merged into a single, shorter
  `what_to_look_for`. The numbered steps read as a gate -- every one had
  to hold -- which taught an agent to match the shapes somebody had
  enumerated and reject the rest.
- `discriminators` were replaced by a bare `similar` list. Their prose
  defended distinctions the project does not need: two agents that repair
  the same waste under two overlapping root causes have both done the job.

Kept because the operational facts inside them are real, and because a
later experiment may want the stricter version back. Nothing reads this
file; it is not part of the build.

## C1.S1

### mechanism

A computation whose result is never read still runs in full: the call is made, the objects are allocated, the reference counts are adjusted, and the value is stored into a local that nothing loads.  The waste is therefore not the assignment -- that is one instruction -- but everything on the right-hand side, which may be a scan of a collection or a network round trip. Unreachable code after a `return` costs nothing at run time and is a maintenance finding rather than an energy one; say which of the two you have.

### how_to_tell

1. Point at the binding and establish nothing reads it: not later in the function, not through a closure, not by `locals()`, not by a debugger hook or an `except` block that inspects it.
2. Say what the right-hand side costs. This is what decides whether the finding matters: `x = 1` unread is a bytecode, `rows = fetch_all()` unread is a query.
3. Establish the expression has no side effect that is the actual point. A call whose return value is ignored may be there for what it does, not for what it returns -- see C1.S5, which is the case where the call itself is pure.
4. For unreachable code, say so explicitly and report it as a maintenance finding. It costs nothing to execute because it never executes.
5. Check for a deliberate discard. `_ = f()`, or a binding kept to hold a reference alive so an object is not collected, are both intentional.

### discriminators

- **vs C1.S5** — C1.S1 is a result *bound to a name* that nothing reads.  C1.S5 is a computation whose result is *not even bound* -- a bare expression statement, or a loop whose accumulation leaves the scope unused.  Same waste, and the repair is the same deletion; pick by whether there is an assignment.
- **vs C1.S7** — C1.S7's binding *is* read, exactly once, and the repair inlines it. C1.S1's binding is never read, and the repair deletes the whole statement.
- **vs C1.S2** — C1.S2 is a store that is *overwritten* before being read.  C1.S1 is a store that is never read at all.

## C1.S2

### mechanism

An assignment costs a `STORE_FAST` for a local -- an index into the frame's array -- plus a reference count increment on the new value and a decrement on whatever the name held before.  For a global or a class attribute it is a dict write instead.  That is one to three instructions, and no input size makes it more, because the redundancy is in the *store* and not in what produced the value.  Where the value being stored was expensive to compute, the finding is C1.S1 or C1.S4 and the saving is much larger.

### how_to_tell

1. Point at the store and say why it leaves state unchanged: the name is reassigned before being read, the value is the name's current value (`x = x`), or the operation is idempotent on this value (`int()` on an int, `str()` on a str, `.strip()` on stripped text).
2. Establish nothing between the two stores reads the name, including through a call that could reach it as a global or an attribute.
3. Say what the right-hand side costs. If it is a call, the finding is not this one -- it is C1.S1 for a discarded result or C1.S4 for a repeat.
4. Confirm the store has no observable effect. A property setter, an attribute on an object with `__setattr__`, or a name a closure captures all make the assignment do work.
5. Accept that the answer is advisory. This is one to three instructions; report it as such and do not build a case file.

### discriminators

- **vs C1.S1** — C1.S2's store is overwritten before it is read.  C1.S1's is never read at all.  If deleting the statement removes a computation as well as a binding, it is C1.S1.
- **vs C1.S4** — C1.S4 repeats a *computation*.  C1.S2 repeats a *store*.  If the right-hand side is a call, it is C1.S4.

## C1.S3

### mechanism

A branch that cannot change what the program does still costs the evaluation of its condition and the dispatch of its jump: two to four instructions. `if cond: pass`, a `match` whose arms are identical, a `try` whose body cannot raise the exception caught -- all of them execute and none of them affects the outcome.  This is a constant cost per evaluation with nothing behind it, which is why it stays advisory unless the condition itself is expensive to compute.

### how_to_tell

1. Establish that the outcome is the same whichever way the branch goes: the bodies are identical, one is empty, or every arm returns the same value.
2. Distinguish this from a branch whose *test* was already decided. If the bodies differ and only the condition is redundant, the finding is C4.S2.
3. Say what the condition costs. A bare name test is advisory; a condition that calls something is C1.S5 territory, because the call is the waste and the branch is incidental.
4. Check for a deliberate placeholder. `if x: pass` is sometimes a documented not-yet-implemented case or a deliberate no-op with a comment, and deleting it removes the record of a decision.
5. For a `try` that cannot raise what it catches, confirm that by reading the body's callees rather than by inspection of the body alone.

### discriminators

- **vs C4.S2** — C1.S3 is a branch that makes no difference *whichever way it goes* -- the bodies are equivalent.  C4.S2 is a branch whose *test* could only ever answer one way, with bodies that do differ.
- **vs C4.S4** — C4.S4 is separate `if`s that should be chained, where each still does something distinct.  C1.S3 is arms that do the same thing.
- **vs C1.S5** — If the condition itself performs the expensive work, report C1.S5 -- the waste is the call, not the branch.

## C1.S4

### mechanism

Computing the same value twice in one scope pays for it twice.  How much that matters is entirely the cost of the expression: `len(x)` twice is two C calls and a few nanoseconds, while a parse or a query twice is the whole thing twice.  The repair binds the value once and reads a local afterwards, which is a `LOAD_FAST` -- so the saving is one full evaluation minus one array index.  The condition that makes it valid is that nothing between the two evaluations can change the answer, which for anything but a pure function of immutable arguments means reading the code in between.

### how_to_tell

1. Point at both evaluations and confirm the expression is textually or semantically identical, including its arguments.
2. Establish the expression is pure. A call that logs, mutates, advances an iterator, or reads a clock must run both times.
3. Establish nothing between the two changes the result: no rebinding of any operand, no mutation of any container they read, no call that could reach either.
4. Say what one evaluation costs. This decides whether the finding is worth reporting: two `len()` calls is advisory, two parses is not.
5. Check the two are in the same scope. Repetition across calls or call sites is C8, and needs a cache rather than a local.

### discriminators

- **vs C3.S2** — C1.S4 is the same computation twice in straight-line code, and the repair binds it above both uses.  C3.S2 is the same computation N times because it sits in a loop, and the repair hoists it above the loop.
- **vs C8.S1** — The boundary that defines C1 against C8.  C1.S4 is redundancy *within one scope*, repaired with a local.  C8.S1 is redundancy *across invocations*, repaired with a cache.  If a local fixes it, it is C1.S4.
- **vs C1.S2** — C1.S4 repeats a computation.  C1.S2 repeats a store.

## C1.S5

### mechanism

A computation whose result no subsequent code consumes runs in full for nothing: every allocation, every pass, every call.  Unlike a dead binding (C1.S1) there is often no assignment to notice -- the waste is a stage of a pipeline whose output the next stage does not actually need, and finding it means understanding what the answer depends on rather than tracking a name. That makes it one of the largest effects available and one of the hardest to see, because every individual line looks purposeful.

### how_to_tell

1. Name the computation and trace its result forwards. Say precisely what consumes it, or that nothing does.
2. Establish the computation is pure. A call whose return value is ignored may exist for its side effect, and deleting it removes that.
3. For a loop, establish whether all iterations matter or only the last. A loop that overwrites a variable each pass and is read once afterwards did n-1 iterations for nothing -- unless the earlier ones had side effects.
4. For a pipeline stage, ask whether the *next* stage is invariant under it. This is the form that hides: a normalisation before a case-insensitive compare, a sort before a `sum`, a softmax before an `argmax`. Establish the invariance and the whole stage goes.
5. Say what the deleted work costs, so the report states the consequence.

### discriminators

- **vs C1.S1** — C1.S1's result is bound to a name that nothing reads.  C1.S5's result is not bound at all, or is bound and then made irrelevant by what the consumer actually needs.  Same deletion; pick by whether there is an assignment.
- **vs C7.S5** — The closest neighbour, and the softmax example sits on the line.  C1.S5 is work whose result is *not consumed*.  C7.S5 is work whose result *is* consumed but whose cost was unnecessary to produce the answer.  If deleting the statement leaves the code correct with no other change, it is C1.S5; if the operation has to be rewritten rather than removed, it is C7.S5.
- **vs C3.S5** — C3.S5 is a loop that should stop once the answer is known.  C1.S5 is a loop whose earlier iterations were never going to contribute.

## C1.S6

### mechanism

Setup performed unconditionally on a path that may not need it pays its full cost on every call, and returns value only on the fraction of calls that reach the code using it.  An empty list at the top of a function is one allocation, which is advisory.  A configuration load, a connection, a compiled pattern or a large buffer created before the check that decides whether it is wanted is a real cost paid on every call that then discards it.  The repair moves the setup inside the branch that needs it, so the expected cost becomes the setup times the probability of taking that branch.

### how_to_tell

1. Point at the initialisation and the code that uses it, and establish they are on different paths -- the value is only read inside a branch, or after an early return that often fires.
2. Say how often the using path is taken. That fraction is the whole finding: setup needed on 95% of calls is not worth moving.
3. Say what the setup costs. An allocation is advisory; an I/O operation or a compile is not.
4. Establish that moving it does not duplicate it. If three branches each need it, moving it into all three is worse than leaving it at the top.
5. Check the setup has no side effect that the current unconditional positioning guarantees -- a lock taken, a directory created, a counter registered.

### discriminators

- **vs C1.S1** — C1.S6's value *is* used, on some paths.  C1.S1's is used on none.  If the repair is a deletion it is C1.S1; if it is a move, C1.S6.
- **vs C4.S7** — C4.S7 adds a guard that skips expensive work.  C1.S6 moves existing work behind a guard that is already there.  Ask whether you wrote a new branch.
- **vs C6.S1** — If the finding is about the object being unnecessary rather than unnecessarily *early*, it is C6.S1.

## C1.S7

### mechanism

A binding costs a `STORE_FAST`, a reference count increment on the value and a decrement on whatever the name held, and each later read costs a `LOAD_FAST`. For a name used exactly once, inlining removes the store and the load: two to three instructions per execution, and no input size makes it more.  This is the smallest repair in the taxonomy.  It is worth reporting where a hot loop executes it millions of times and it is worth reporting as advisory everywhere else -- and it is worth *not* reporting when the name is what makes the expression readable.

### how_to_tell

1. Establish the name is read exactly once, and that the read immediately follows the store with nothing in between.
2. Establish the name carries no explanatory weight. A binding that gives a name to a complicated subexpression is doing a job, and this repair destroys it. This is the step that should reject most candidates.
3. Say how often the statement executes. Inside a million-iteration loop this is measurable; anywhere else it is advisory.
4. Check that inlining does not change evaluation order or lifetime. Moving an expression into a `return` changes when its value is released, which matters if it holds a resource.
5. Confirm the result is not needed for a debugger, a traceback, or an exception message that reads the local.

### discriminators

- **vs C1.S1** — C1.S7's binding is read once.  C1.S1's is never read.  Read once means inline; never read means delete the statement.
- **vs C3.S1** — When the temporary lives in a loop that becomes a comprehension, the comprehension is the finding and this is subsumed.  Report the larger one.

## C1.S8

### mechanism

Runtime housekeeping is expensive and mostly unnecessary.  `gc.collect()` performs a full traversal of every tracked object in the process, so calling it in a loop turns a per-iteration cost into something proportional to the whole heap -- and CPython's automatic collector is already tuned to do this at sensible intervals.  Logging has a subtler version of the same problem: the arguments to a log call are evaluated before the logger decides whether the level is enabled, so an expensive f-string or a `json.dumps` inside a `debug()` call is computed in full and then discarded in production.  In both cases the work is real and the benefit is zero.

### how_to_tell

1. Point at the housekeeping call: `gc.collect`, `gc.freeze`, an explicit `__del__` trigger, `sys.settrace`, a profiler start, or a log call.
2. For `gc.collect`, establish there is no specific reason for it. There are legitimate ones -- before forking, before a memory measurement, after releasing a large graph in a long-running process -- and each is a deliberate decision rather than a habit.
3. For a log call, establish that its arguments are expensive to build and that the level is usually disabled. A plain `%s` of a small value costs nothing; an f-string that formats a whole record costs the formatting on every call.
4. Say how often it happens. `gc.collect()` once at start-up is fine; per-iteration is the finding.
5. Confirm the repair keeps the diagnostic available when it is wanted -- guarding with `isEnabledFor` rather than deleting the log line.

### discriminators

- **vs C1.S5** — An expensive log argument that is discarded is C1.S5 in substance -- work whose result nothing consumes.  Report C1.S8 when the framing is *housekeeping being invoked too often*, and C1.S5 when it is a computed value nobody reads.
- **vs C3.S3** — If the repair moves the call out of the loop rather than deleting it, the finding is C3.S3.
- **vs C6.S4** — `gc.collect()` in a loop is sometimes a symptom: someone added it because memory was growing.  If the real problem is retention, report C6.S4 and note that the collection call was masking it.

## C2.S1

### mechanism

A Python call allocates a frame object of roughly two to four hundred bytes, binds the arguments into it, executes, and tears it down.  A wrapper that only forwards pays all of that to accomplish nothing -- the callee would have done the same work reached directly.  A `@property` that only returns an attribute is the same cost in a different guise: attribute access on the instance triggers the descriptor protocol, which builds a bound method and calls it, where a plain attribute read is a dict lookup.  In both cases the waste is one call's overhead per access, which is tens to hundreds of nanoseconds -- real inside a loop over a million elements and invisible anywhere else.

### how_to_tell

1. Establish the wrapper adds nothing: it forwards the same arguments in the same order, does not validate, transform, log, or default anything, and returns the callee's result unchanged.
2. Establish it is on a hot path, and say how you know -- a loop over a large collection, a per-element call, a request handler measured to be hot. This is the load-bearing step and it should reject most candidates.
3. Establish it is not public API. A named alias, a documented method, an override satisfying an interface, or anything outside the module's private surface exists for callers you cannot see. Removing or bypassing it is a breaking change rather than a repair.
4. For a `@property`, check it really is a bare attribute return. A property that computes, caches, validates or has a matching setter is doing work the attribute read would not.
5. Say which side of the call you are changing. Bypassing the wrapper at its hot call sites keeps the wrapper for everyone else; deleting it changes the class's surface. The first is usually the right repair.

### discriminators

- **vs C2.S3** — C2.S1 is *one* redundant layer, and the repair removes it.  C2.S3 is a *chain* of thin layers whose combined overhead rivals the work, and the repair merges them.  Count the frames the repair removes: one, or several.
- **vs C2.S2** — C2.S1 removes a call.  C2.S2 keeps the call and changes how the method is declared, so the bound-method object is not built.
- **vs C10.S6** — C10.S6 is the same overhead reached through *operator syntax*, where the call is hidden by a `+` or a `==`.  C2.S1 is a named method.
- **vs C8.S3** — If the repair caches the *result* of the wrapped call in a local before a loop, rather than removing the wrapper, the finding is C8.S3.

## C2.S2

### mechanism

Accessing a function through an instance invokes the function's descriptor protocol: `__get__` runs and returns a bound method object wrapping the function together with `self`, which is then called and discarded.  A `@staticmethod` skips the wrapper, and a module-level function skips the class namespace lookup as well.  The saving is one small allocation and one extra layer of dispatch per call -- and recent CPython versions have specialised much of this away, which is why the *direction* of the effect is less certain than the mechanism suggests.  See the notes.

### how_to_tell

1. Establish the method never touches `self`: no attribute read, no attribute write, no other method call on it, and no use in a nested function or comprehension inside the body.
2. Establish no subclass overrides it in a way that depends on the instance, and that nothing calls it through `super()`. A `@staticmethod` cannot be overridden polymorphically in the same way.
3. Establish it is called often enough for one allocation per call to matter -- which for this root cause means millions of calls.
4. Check what the call sites look like. `self.helper(x)` inside the class keeps working under `@staticmethod`; `Class.helper(x)` from outside changes meaning if the method previously took `self`.
5. Decide between `@staticmethod` and a module-level function, and say why. The first keeps the namespace and the discoverability; the second removes the class lookup as well and is the larger change.

### discriminators

- **vs C2.S1** — C2.S2 keeps every call and changes the declaration.  C2.S1 removes a call because it forwarded to another one.
- **vs C5.S3** — Both make an object cheaper.  C5.S3 changes the instance's *storage* (`__slots__`, a namedtuple); C2.S2 changes how a *method* on it is bound.

## C2.S3

### mechanism

Frame cost is per call, so a chain of thin layers multiplies it: three one-line wrappers between a loop and the work mean three frames per iteration on top of whatever the work costs.  When each layer does something substantial the overhead is a rounding error; when each layer is a single expression, the ceremony can exceed the computation.  This root cause is therefore about a *ratio* rather than about a count of layers -- and it is the only entry in this category that cannot be seen from one function, because the finding is the depth of the path rather than anything about its members.

### how_to_tell

1. Trace one path from the hot loop down to the work, and count the frames per iteration. Say the number.
2. Say what each layer contributes. A layer that validates, transforms, dispatches or handles an error is earning its frame; a layer that computes one expression and returns is not.
3. Compare the ceremony to the work. Three frames around a dict lookup is the finding; three frames around a regex match is not, because the match dominates.
4. Establish the layers are private to this path. Inlining something other code calls is a breaking change, and the repair then has to keep the layer and bypass it only here.
5. Say what the inlined version costs in comprehension, and be honest about it. This repair trades structure for speed, and it is only worth proposing where the hotness is established and substantial.

### discriminators

- **vs C2.S1** — Count the frames the repair removes.  One: C2.S1.  Several, because the path was layered: C2.S3.
- **vs C7.S3** — C2.S3 is a chain of *different* functions.  C7.S3 is a function calling *itself*.
- **vs C3.S1** — If the frames disappear because the loop became a comprehension rather than because the layers merged, the finding is C3.S1.

## C3.S1

### mechanism

Iteration forms differ in how much interpreter work they do per element. `for i in range(len(xs))` with `xs[i]` builds an index object, does a bounds-checked subscript and rebinds a name each time; `for x in xs` asks the iterator for the next pointer.  A comprehension goes further: it uses a dedicated `LIST_APPEND` bytecode with no attribute lookup and no call, where an explicit `.append()` loop resolves the method on every iteration.  None of this changes what the loop computes; it changes how much ceremony surrounds each element, which is why the effect is a per-element constant factor rather than a complexity change.

### how_to_tell

1. Name the construct and the alternative, and say what work the alternative stops doing -- an index object not built, an attribute not resolved, a subscript not bounds-checked.
2. Check the index is genuinely unused. `for i in range(len(xs))` is only replaceable by `for x in xs` if `i` is used for nothing but `xs[i]`; if it is also used to index a second list, `zip` is the repair, and if it is used arithmetically, `enumerate` is.
3. For an `append` loop becoming a comprehension, establish the body does nothing else. A `continue`, a side effect, an early `break`, or two appends to different lists all block the repair.
4. Establish the result type is unchanged. A slice returns the input's type where a comprehension always returns a list, and `map` returns an iterator rather than a list.
5. Count the elements. This is a per-element constant factor of tens of nanoseconds, so it needs thousands before it is measurable.

### discriminators

- **vs C10.S3** — Turning an `append` loop into a comprehension fits both.  C3.S1 frames it as the *iteration construct* being wrong; C10.S3 frames it as a *per-element call* that should be batched.  Pick one, say which, and do not report both.
- **vs C10.S1** — C3.S1 keeps a loop and changes how it is written.  C10.S1 removes the loop entirely in favour of a primitive that returns the answer.
- **vs C3.S2** — C3.S1 is about the loop's *form*.  C3.S2 is about a *computation in the body* that did not need repeating.

## C3.S2

### mechanism

An expression whose operands do not change inside the loop produces the same value every iteration, so the loop pays N times for one answer.  The repair computes it once above the loop and reads a local afterwards.  What makes this worth more than it looks is that the invariant is often not a cheap expression: a `len()` in a `while` condition, an attribute chain, a dictionary lookup, a call that builds a set.  The saving is (N-1) times whatever that expression costs, so a heavy invariant in a long loop is one of the larger effects available.

### how_to_tell

1. Point at the expression and name every operand it reads.
2. Establish that none of those operands is rebound or mutated inside the loop, including by any function the loop calls. This is where candidates die: a method call on an object the loop also mutates is not invariant.
3. Establish the expression is pure. A call that logs, increments a counter, or advances an iterator must run each time even if its value never changes.
4. Check it is actually evaluated per iteration. A `for` loop's iterable is evaluated exactly once when the loop starts, so `for i in range(len(xs))` does *not* recompute `len(xs)` -- but `while i < len(xs)` does.
5. Say what the expression costs and how many iterations there are. Hoisting an attribute read from a ten-iteration loop is not a finding.

### discriminators

- **vs C3.S3** — Both hoist something out of a loop, and the split is what kind of thing. C3.S2 hoists a *computed value* that turns out to be constant.  C3.S3 hoists the *creation of an object or resource* -- a compiled pattern, a connection, a container -- where the point is the allocation rather than the arithmetic.
- **vs C8.S2** — C3.S2 hoists to just above the loop, so the value is recomputed on the next call.  C8.S2 hoists to module or instance scope so it survives *across* calls.  Ask where the repair puts it.
- **vs C1.S4** — C1.S4 is the same computation done twice in straight-line code.  C3.S2 is the same computation done N times because it sits in a loop.

## C3.S3

### mechanism

Creating an object costs an allocation, an `__init__`, and eventually a collection; creating an expensive one -- a compiled regular expression, a connection, a `Decimal` context, a lambda -- costs considerably more.  Doing it inside a loop pays that per iteration for something the loop could have shared.  For resources it is worse than arithmetic waste: opening a file or a connection per iteration adds a syscall and a handshake to every pass, and can exhaust a pool.  The repair moves the creation above the loop, which is available exactly when the object does not carry per-iteration state.

### how_to_tell

1. Point at the creation inside the loop: a literal container, a class instantiation, `re.compile`, `open`, a lambda or a nested `def`, a `Decimal` or `datetime` format object.
2. Establish that it does not depend on the loop variable. A `re.compile` on a fixed pattern is hoistable; one built from the current row is not.
3. Establish that the object carries no state across the iteration boundary that must be fresh. A list accumulated into and then reset each iteration can be hoisted *and cleared*; one that is stored or returned cannot, because every iteration would share the same object.
4. For a resource, establish the lifetime is safe to extend. One connection held across the whole loop is usually right, but not if the loop is long enough for a timeout, or if the resource is not reentrant.
5. Say what the creation costs and how many iterations. A bare `[]` per iteration is cheap; `re.compile` is not.

### discriminators

- **vs C3.S2** — C3.S3 hoists the *creation of an object or resource*.  C3.S2 hoists a *computed value*.  If the repair moves an allocation, it is C3.S3.
- **vs C6.S1** — These overlap when the object is cheap.  C3.S3 is about the creation being *per iteration* when it need not be; C6.S1 is about objects being created that are not needed at all.  If the loop is incidental, it is C6.S1.
- **vs C8.S2** — Same repair, different destination.  Above the loop: C3.S3.  At module or instance scope so it survives across calls: C8.S2.

## C3.S4

### mechanism

Nested loops multiply: an outer loop of n and an inner of m run n*m times, so anything in the inner body is paid n*m times.  The repair replaces the inner *search* with a constant-time lookup, turning n*m into n+m -- which is a complexity change rather than a constant-factor one, and therefore the largest class of effect in the taxonomy.  A related but distinct form applies when the two loops range over the same collection and the relation is symmetric: iterating only the upper triangle halves the comparisons.  That one is a constant factor, not a complexity change, and it is not free -- see the counter-example.

### how_to_tell

1. Establish that the inner loop is a *search* -- it scans looking for matching elements -- rather than work that genuinely has to touch every pair.
2. Say what the index would be keyed on, and confirm the key is hashable and is what the inner loop actually compares.
3. Establish neither collection is mutated inside the loops, so the index stays valid.
4. For the triangular form, establish the relation is symmetric and that the loop's writes can be mirrored. Then check what the mirroring costs: halving the comparisons while doubling the appends is not a win.
5. Say the sizes. n*m against n+m only matters when both are large; two nested loops over ten items each is a hundred iterations and no finding.

### discriminators

- **vs C5.S2** — These co-occur constantly, because adding an index is *how* a nested loop becomes a single pass.  Report C3.S4 when the repair removes a level of loop nesting, and C5.S2 when the loops stay and only the search inside them changes.
- **vs C7.S1** — C3.S4 keeps the same approach and removes a level of iteration.  C7.S1 replaces the approach with a different algorithm.  If the repair's name is an algorithm -- binary search, Timsort, a sieve -- it is C7.S1.
- **vs C7.S2** — C7.S2 is about the *decomposition* -- exploring subproblems that could have been pruned or reused.  C3.S4 is about two literal loops.

## C3.S5

### mechanism

A loop that has already determined its answer and keeps going pays for every remaining iteration.  How much that is worth depends entirely on where the answer arrives: a search that finds its target in the first percent of a million-element list wastes 99% of the traversal, while one that usually finds it at the end wastes nothing.  So the saving is not a property of the code but of the data, and the expected value is the loop's cost multiplied by the expected fraction remaining when the answer is settled.

### how_to_tell

1. Identify the point at which the outcome is decided -- a target found, a validation failed, an accumulator reaching a conclusive state.
2. Prove that no later iteration can change it. This is the step that matters. A loop that assigns a *constant* and keeps going is a genuine missing exit; a loop that assigns a *value derived from the element* is not, because a later iteration may overwrite it with something different, and breaking changes the answer.
3. Check for work after the loop that depends on it having run to completion -- a counter, a side effect on every element, a variable the following code reads.
4. Estimate where the answer typically arrives. Early on most inputs means a large saving; late means almost none, and the honest report is that the pattern is present and not worth repairing.
5. Prefer the primitive that already short-circuits. `any`, `all`, `next`, `in` and `str.find` all stop at the answer, and using one is usually the better repair than adding a `break`.

### discriminators

- **vs C3.S6** — C3.S5 stops a traversal *once the answer is known*.  C3.S6 avoids touching elements that were never relevant.  Break added: C3.S5.  Filter or slice moved earlier: C3.S6.
- **vs C4.S7** — C3.S5 stops work that has already started.  C4.S7 stops it before it starts, with a guard.
- **vs C10.S1** — Replacing the loop with `any`/`all`/`next` is both.  Report C3.S5 when the point is the early exit and C10.S1 when the point is that a primitive does the whole job in C.

## C3.S6

### mechanism

Processing the whole collection when a subset is wanted pays for every element that never reaches the result.  The repair moves the reduction earlier -- filtering before transforming, taking before sorting, selecting at the source rather than in Python -- so that the expensive step sees only the elements that matter.  The saving is the expensive step's per-element cost multiplied by the elements removed, which makes it one of the larger effects when the selectivity is high and nothing at all when it is low.

### how_to_tell

1. Say what fraction of the processed elements reach the result. If it is most of them, there is nothing to save.
2. Establish the reduction can move earlier without changing the answer. Filtering before a transform is only equivalent if the predicate does not depend on the transform's output.
3. Name the reduction. `heapq.nlargest` instead of a full sort; `itertools.islice` instead of building and slicing; a `WHERE` clause instead of filtering in Python; `set()` before a per-element test when duplicates are dense.
4. For the deduplicate-first form, establish the duplicate ratio. It pays when a large collection has few distinct values and is a pure extra pass when the values are unique.
5. Check the reduction is not itself the expensive step. Deduplicating a million unique elements to run a cheap test on them costs more than the test did.

### discriminators

- **vs C7.S4** — These are nearly the same idea and the split is scope.  C3.S6 is about a *loop or comprehension* touching more elements than it needs.  C7.S4 is about the *order of two operations* in a pipeline, where both are already bulk steps.  Filter moved into a loop: C3.S6.  Two statements swapped: C7.S4.
- **vs C3.S5** — C3.S6 never touches the irrelevant elements.  C3.S5 touches them until the answer is known and then stops.
- **vs C9.S2** — When the reduction moves across a process boundary -- into a query, into an API call -- report C9.S2, because the saving is transfer rather than iteration.

## C3.S7

### mechanism

Mutating a collection while iterating it is primarily a correctness problem: removing from a list shifts the remaining elements down, so the iterator's index skips one; appending during iteration can extend the loop indefinitely; a dict or set raises `RuntimeError` outright.  The energy consequence follows from the correctness one.  Each `list.remove` or `del lst[i]` moves every subsequent element, so a filtering loop written this way is quadratic where a rebuild is linear -- and an unbounded loop consumes energy without ever finishing.

### how_to_tell

1. Confirm the collection being mutated is the one being iterated, and not a different one with a similar name or a copy.
2. Say which mutation it is: removal, insertion, append, or a reorder. Each has a different consequence -- removal skips, append may not terminate, reorder gives an undefined visit sequence.
3. Establish whether the behaviour is currently wrong. This is a correctness finding first: if elements are being skipped, the repair fixes a bug and the energy saving is secondary. Say which you are claiming.
4. Name the repair -- iterate a copy, build a new collection, or collect the indices and apply afterwards -- and check it preserves what the code actually does today, including any accidental behaviour callers depend on.
5. For a `while` loop, check the termination condition is updated on every path. A `continue` that skips the increment is the classic unbounded loop.

### discriminators

- **vs C7.S1** — If the loop is correct and the cost is repeated linear `remove` or `del`, the finding is C7.S1 -- a quadratic approach where a linear one exists.  C3.S7 is specifically about mutating the collection *being iterated*.
- **vs C6.S2** — Rebuilding rather than editing in place trades a copy for correctness. If a reviewer would call the new allocation the problem, that is C6.S2 -- and the two point in opposite directions, so say which cost you are choosing to pay.

## C4.S1

### mechanism

`and` stops at the first false operand and `or` at the first true one, so every operand after the deciding one is never evaluated.  Ordering therefore decides what a condition costs on average: a chain that puts the expensive test first pays it on every evaluation, where the same chain reordered pays it only on the fraction of inputs the cheap test lets through.  The saving is the expensive operand's cost multiplied by how often the cheap test would have short-circuited -- which is why an operand that is almost never decisive is worth nothing to move.

### how_to_tell

1. Find an `and`/`or` chain where an earlier operand calls something and a later operand does not. A cheap operand is a comparison, an attribute read, a `len`, an `isinstance`; an expensive one is a call that does work.
2. Establish that the operands are independent, so reordering cannot change the result. This is the step that matters: `if x is not None and x.ready()` must stay in that order for correctness, and swapping it is a bug rather than a repair.
3. Estimate how often the cheap test would decide the result. If it is false on most inputs, moving it first skips the call on most calls; if it is almost always true, reordering adds a test and saves nothing.
4. Confirm the chain runs often enough for a skipped call to matter. One evaluation on a cold path saves one call.

### discriminators

- **vs C4.S2** — C4.S1 keeps every test and changes their order.  C4.S2 *deletes* a test because its outcome was already determined.  If the repair removes an operand rather than moving it, it is C4.S2.
- **vs C4.S7** — C4.S1 reorders tests that already exist.  C4.S7 *adds* one that did not.
- **vs C7.S4** — The same idea at a different scale.  C4.S1 orders operands inside one boolean expression; C7.S4 orders whole operations in a pipeline, such as filtering before sorting.  Decide by what the patch moves -- an operand or a statement.

## C4.S2

### mechanism

A test whose outcome is already fixed still costs the full evaluation: loading the operands, the comparison, the branch.  When that is one comparison on a straight-line path it is worth a bytecode and nothing more. What makes this root cause worth reporting is the case where the determined test *guards work* -- the second half of an `and` that can never fail, an `elif` whose condition is the negation of the `if` above it, or a check standing between the caller and a scan the code did not need to perform. Then what the repair deletes is not the comparison but everything behind it.

### how_to_tell

1. Point at a condition and say what makes its outcome already known. There are three sources and you must name which one applies. A prior test on the same path has settled it. A domain fact makes it unconditional -- `math.floor(x) <= math.ceil(x)` always, `abs(x) >= 0` always, an `assert` at the top of the function. Or the value was assigned a known constant with nothing able to change it in between.
2. Establish that nothing between the two points can change the answer: no assignment, no call that could mutate the operands, no `await` or lock release that lets another thread in.
3. Say what the test is guarding. A determined test in front of one cheap statement is worth a bytecode. A determined test in front of a loop, a sort or a call is worth all of it, and that difference decides whether the finding is worth reporting at all.
4. Check that the redundancy is not deliberate. A re-check documenting an invariant, or one that exists because a maintainer cannot see the callers, is defensive code; deleting it is a change in kind rather than a repair.

### discriminators

- **vs C4.S7** — C4.S2 *removes* a test that was always going to answer the same way. C4.S7 *adds* a test that was not there.  When one edit does both -- recognising an invariant and using it to install a fast path -- either label is defensible; say which you picked and why.
- **vs C7.S5** — C4.S2 deletes a *test*.  C7.S5 changes the *operation*: replacing `abs(k - x)` with `k - x` because `k >= x` always holds is C7.S5, since no branch is removed and the arithmetic itself got cheaper.
- **vs C1.S3** — C1.S3 is control flow with no observable effect whichever way it goes -- an `if` with an empty body, a `match` whose arms are identical.  C4.S2 is a branch that does something, reached by a test that could only ever answer one way.
- **vs C1.S4** — C1.S4 is the same *computation* performed twice.  C4.S2 is the same *condition* tested twice, or one whose answer was already implied.  If the repair caches a value, it is C1.S4.

## C4.S3

### mechanism

Nesting itself costs nothing beyond the tests it contains -- reaching depth four evaluates four conditions whether they are nested or chained.  Two things make deep nesting expensive rather than merely ugly.  Overlapping tests get re-evaluated on paths where an earlier branch already settled them. And a long chain of `elif` comparisons is a linear search: with N arms the average case evaluates about N/2, where a dict lookup or an index is one probe regardless of N.

### how_to_tell

1. Count the depth, then check what the nesting is made of. `if` inside `if` is a candidate; depth that comes from `try`, `with` or `for` is not this root cause.
2. Find the actual waste. Either the same subexpression is tested on more than one path, or a run of arms all compare the same subject against different constants. If neither holds, the nesting is a readability matter and out of scope here.
3. For a comparison chain, count the arms and check they are exhaustive and dense enough to index. Four arms keyed on `n % 4` become a tuple index; four arms on unrelated predicates do not.
4. Confirm the flattening does not duplicate the conditions it removed. Guard clauses only help when they let you stop testing, not when they restate the same tests in a different order.
5. Say how often the branch runs. Removing two comparisons from a function called twice is not a finding.

### discriminators

- **vs C4.S4** — C4.S4 is about tests written as *separate statements*, where every one is evaluated even after an earlier one matched.  C4.S3 is about tests that are already chained or nested and still cost more than they need to.
- **vs C10.S1** — Replacing a comparison chain with a dict dispatch can be read either way. Prefer C4.S3 when what changed is the *branch structure*, and C10.S1 when the repair hands the whole job to a standard-library primitive that already implements it.

## C4.S4

### mechanism

Separate `if` statements each evaluate their condition unconditionally, so N of them cost N tests on every pass.  An `if`/`elif` chain stops at the first match: one test in the best case, N in the worst, around N/2 on average for a uniformly distributed subject.  The saving is the difference, paid per evaluation -- proportional to how many arms there are and how early the matching one usually sits.

### how_to_tell

1. Find two or more consecutive `if` statements testing the same subject.
2. Prove the branches are mutually exclusive, and say what makes them so. This is the load-bearing step and it is where the repair usually dies. A set of `==` tests against distinct constants is exclusive by construction. Range tests are only exclusive if the ranges cannot overlap, and that often depends on a precondition -- an `assert`, a validated argument, a documented invariant. Name it.
3. Establish that no branch body changes the subject or anything the later tests read. A body that mutates the subject makes the later tests genuinely different questions.
4. Establish that no branch is meant to fall through. If two conditions can both hold and both bodies are supposed to run, chaining them removes behaviour.
5. Count the arms and say how often the last one matches. Two arms save half a test; eight arms with a late match save several.

### discriminators

- **vs C4.S3** — C4.S4 turns *separate statements* into a chain.  C4.S3 improves a chain or nest that already exists, usually by replacing it with a lookup.
- **vs C1.S3** — If the branches are not merely unchained but have no observable effect at all -- identical bodies, empty bodies -- the finding is C1.S3.

## C4.S5

### mechanism

A type check is cheap once and expensive per element.  `isinstance` walks the class's MRO looking for a match; `type(x) == C` is a pointer comparison; `str(type(x)) == "..."` builds a string.  None of them is slow in isolation, and all of them are pure overhead when the answer is the same for every element of a collection -- the loop is asking a question it could have settled once.  The repair moves the decision off the per-element path, either by hoisting it or by letting attribute lookup dispatch instead.

### how_to_tell

1. Find runtime type introspection on the per-element path: `isinstance`, `type(x) ==`, `hasattr` used as a type probe, a comparison against `type(x).__name__`.
2. Establish that the answer is stable across elements, or that the elements can be grouped so it is. If the collection is genuinely heterogeneous and the branches do different things, the check is doing real work.
3. Say what replaces it. Hoisting needs a cheap way to settle the type once. Polymorphic dispatch needs the types to share a method name. `functools.singledispatch` needs the dispatch to be on the first argument.
4. Check the replacement is not more expensive. Scanning the whole collection with `all(isinstance(...))` to hoist a decision costs a full extra pass, which only pays if the loop body is heavier than the check.
5. Confirm the loop is long enough. A per-element `isinstance` over ten items is nothing.

### discriminators

- **vs C10.S2** — C10.S2 swaps one construct for a cheaper construct that does the same thing, leaving the loop alone.  C4.S5 removes the check from the per-element path altogether.  If the loop still asks the question once per element, it is C10.S2 at best.
- **vs C3.S2** — Hoisting a type decision out of a loop is a special case of hoisting an invariant.  Report C4.S5 when what was hoisted is *type introspection* and C3.S2 when it is any other loop-invariant expression.

## C4.S6

### mechanism

Entering a `try` block costs nothing measurable in modern CPython -- the handler is recorded in a table rather than pushed at run time.  Raising is what costs: instantiating the exception, capturing a traceback frame by frame, unwinding, and matching the handler.  So the price of this pattern is the raise rate multiplied by the cost of a raise, which makes it idiomatic and fast when the exception is rare.  It becomes waste only when the exception is the common case, at which point the code is using an error mechanism as its main control flow.

### how_to_tell

1. Confirm the `try` is on the per-iteration path rather than wrapped around the whole loop. A `try` outside the loop raises at most once.
2. Establish the raise *rate*, and say how you know. This is a property of the data, not of the code: `table[key]` inside a `try` is excellent when keys are usually present and poor when they usually are not. Read the callers, the fixtures, the documentation -- or say you could not establish it and reject.
3. Name the check that would replace the raise, and confirm it is cheaper than the raise it avoids. `dict.get` and `key in table` are; a second full lookup, or a `try` inside the check, is not.
4. Confirm the check is exact. `except (KeyError, TypeError)` covers two cases where a `.get()` covers one, and a repair that silently changes which failures are tolerated is not behaviour-preserving.

### discriminators

- **vs C3.S3** — Both fire on the same syntax.  C4.S6 is about the *raise* being frequent; C3.S3 is about per-iteration *setup* that should be hoisted.  If the repair moves the `try` out of the loop it is C3.S3; if it replaces the raise with a test it is C4.S6.
- **vs C4.S7** — C4.S6 replaces an exception-driven decision with a test.  C4.S7 adds a test in front of work that would otherwise succeed expensively.  Nothing raises in a C4.S7 case.

## C4.S7

### mechanism

A guard is a cheap test that lets the function skip an expensive path entirely.  Its value is the cost of that path multiplied by how often the degenerate input actually arrives, minus the cost of the test on every other call.  So it is worth adding exactly when the skipped work is large and the trivial case is common, and it is a net loss when the trivial case is rare -- then every call pays the test and almost none benefit.  The other side of the ledger matters too: many library functions already short-circuit internally, and a guard in front of one of those buys nothing at all.

### how_to_tell

1. Name the class of input that reaches the expensive path without needing it. Empty, one element, already sorted, already normalised, a value the arithmetic makes irrelevant, a type with a trivial answer.
2. Establish that the general path really does the full work on that input. `sorted()` on an empty list is already cheap; `re.compile` on a fixed string is already cached. Check before claiming, because this is where most candidates die.
3. Say how often the trivial input arrives and how you know. A guard is a bet on the input distribution, and if you cannot describe the distribution you cannot say whether the bet pays.
4. Write the guard and confirm it returns exactly what the general path would have returned for that input, including the type and the edge behaviour. A fast path that is subtly different is a bug, not a repair.
5. Check the guard itself is cheap. A guard that scans the collection to decide whether to scan the collection has saved nothing.

### discriminators

- **vs C4.S2** — C4.S7 *adds* a test that was not there.  C4.S2 *removes* one whose answer was already determined.  One edit sometimes does both -- notice an invariant, then use it to install a fast path -- and either label is defensible; say which you chose.
- **vs C7.S5** — C4.S7 keeps the expensive operation and skips it for some inputs.  C7.S5 makes the operation itself cheaper for *all* inputs by simplifying it. Branch added: C4.S7.  Arithmetic changed: C7.S5.
- **vs C3.S5** — C3.S5 stops a loop that is already running, once the answer is known. C4.S7 stops the work before it starts.  If the repair adds a `break`, it is C3.S5.

## C4.S8

### mechanism

CPython's compiler and its built-in types have fast paths for the idiomatic spellings, and the verbose equivalents miss them.  `if not x` asks the object for its truth value directly; `if len(x) == 0` calls `len`, builds an int and compares two objects.  `key in mapping` probes the hash table; `key in mapping.keys()` first builds a view.  `a < b < c` evaluates `b` once; `a < b and b < c` evaluates it twice.  Each difference is a handful of bytecodes -- small, uniform, and only visible in aggregate.

### how_to_tell

1. Point at the verbose form and name the idiom that replaces it.
2. Establish that the two are equivalent *for this data*. This is the whole difficulty: `len(x) == 0` and `not x` differ for an object with a custom `__bool__` or `__len__`, and for a numpy array or a pandas frame the idiom raises rather than answering.
3. Check that the explicit form is not deliberately exact. Comparing floats with `==` is sometimes precisely what was meant, and replacing it with `math.isclose` changes the answer.
4. Say how often it runs. This is worth a few bytecodes per evaluation, so it is a finding only inside something hot -- and it is often more honest to report it as advisory.

### discriminators

- **vs C10.S2** — These overlap almost completely, and the split is by *what* the alternative is.  C4.S8 is about the spelling of a **condition**, where CPython has a fast path for the idiom.  C10.S2 is about choosing a cheaper **function or method** for a task -- `str.startswith` over `re.match`, `& 1` over `% 2`.  If the repair rewrites a boolean test it is C4.S8; if it swaps a callable it is C10.S2.
- **vs C4.S2** — C4.S8 rewrites a test into a cheaper equivalent that asks the same question.  C4.S2 deletes a test because its answer was already known.

## C5.S1

### mechanism

A container's cost is paid per operation, and the same operation has a very different price depending on the type holding the data.  `x in lst` compares `x` with each element until one matches, so N lookups over an M-element list cost N*M comparisons; the same lookups against a set cost N hash probes. The repair removes no work from the program's logic -- every step it performed still happens -- it changes what one of those steps costs.  That is why the saving grows with the collection size *and* with the number of operations, and why it vanishes when either one is small.

### how_to_tell

1. Name the operation this container is used for most often on the hot path: membership, positional access, ordered traversal, keyed lookup, insertion or removal at the front. Say roughly how many times it happens per call.
2. Check whether that operation is the expensive one for this type. `in` is a linear scan over `list`, `tuple` and `str`, and a hash probe on `set`, `dict` and `frozenset`. Indexing is constant on a list and unavailable on a set. Inserting at the front is linear on a list and constant on a `collections.deque`. `.count()` and `.index()` are always a full scan.
3. Find where the container is built. The repair changes that line, so if it is built somewhere you cannot edit -- a caller's argument, a library return value -- the repair is either a conversion at the boundary (which has its own cost, see the neighbours) or nothing.
4. Check the sizes actually involved. A set only repays its construction when the collection has more than roughly a dozen elements and is searched more than once. `if method in ("GET", "POST")` is correct as written.
5. Confirm the replacement can hold this data: set and dict keys must be hashable, and a set discards both order and duplicates.

### discriminators

- **vs C5.S2** — C5.S1 changes an existing container's *type*, and everything that used it keeps using it.  C5.S2 *adds* a second structure beside the original, because the original is still needed as it is -- for its order, its duplicates, or because it is what the function returns.
- **vs C5.S3** — C5.S1 is about the cost of an *operation* on the container.  C5.S3 is about the container's *footprint*, when nothing is wrong with the operations at all.
- **vs C3.S4** — If the repair also removes a level of loop nesting, prefer C3.S4: the finding is then about the shape of the iteration, and the container change is how it was achieved.  C5.S1 alone leaves the loops as they are.

## C5.S2

### mechanism

An index turns repeated search into arithmetic.  Scanning an n-element collection to answer each of m questions costs n*m comparisons; building a dict from it costs n hashes once and then answers each question in constant time, for n + m in total.  The saving is the difference, so it appears when m is more than a small handful and disappears entirely when m is one -- building an index to answer a single question is strictly more work than the scan it replaces.

### how_to_tell

1. Find a collection that is searched more than once with a different key each time. The search may be a loop, a `next(... for ...)`, an `in`, a `.index()` or a `.count()`.
2. Establish that the collection does not change between those searches. If it is appended to or filtered inside the same loop, the index would have to be rebuilt and the repair does not apply.
3. Say what the index would be keyed on, and confirm that key is hashable and is what every search actually looks up.
4. Count the lookups. A few dozen against a small collection and the index costs more than it saves; say so and reject.
5. Check that the original collection is still needed as it is. If nothing relies on its order, its duplicates or its type, this is C5.S1 -- change it rather than add beside it.

### discriminators

- **vs C5.S1** — Ask what exists after the repair.  Two structures, because the original is still needed for its order, its duplicates or its type: C5.S2.  One structure of a different type: C5.S1.
- **vs C8.S1** — C5.S2 indexes *data already in hand*, and the index lives for one invocation.  C8.S1 caches *the result of a computation* so a later call does not repeat it.  If the stored thing had to be computed rather than merely located, it is C8.S1.
- **vs C3.S4** — These co-occur: adding an index is usually how a nested loop becomes a single pass.  Report C3.S4 when the repair removes a loop level, and C5.S2 when the loops stay and only the search inside them changes.

## C5.S3

### mechanism

A heavier representation costs on three axes at once: bytes per instance, the allocation and collection of those bytes, and the work the interpreter does to operate on them.  A float multiply is not a slower integer multiply -- it converts the operand, takes a different execution path and allocates a new float for the result.  An instance with a `__dict__` is a second heap object per instance and a dict lookup per attribute read.  A list literal inside a function is built element by element on every call, where a tuple of the same constants is stored once in the code object and merely loaded.

### how_to_tell

1. Name the capability the heavier type provides: fractional values, mutability, arbitrary attributes, ordering, named fields.
2. Establish that this code does not use it. Not "does not need it in principle" -- find the uses and check.
3. Establish that no *other* code uses it either. A tuple returned to a caller that appends to it is not a repair, it is a bug.
4. Say how many instances or operations exist on the hot path. The saving is a small fixed amount each time, so it needs volume before it is measurable at all.
5. Check the value's history. A number that arrives as a float is already a float, and changing a literal beside it changes nothing.

### discriminators

- **vs C6.S1** — C5.S3 keeps the same number of objects and makes each one lighter. C6.S1 keeps the weight and creates fewer of them.  If the repair changes a *count*, it is C6.S1.
- **vs C5.S1** — C5.S3 is about footprint and per-operation constant factors, with the access pattern unchanged.  C5.S1 is about an operation whose complexity is wrong for the container.

## C5.S4

### mechanism

A conversion walks the whole source and allocates a whole new container. That is worth paying for when the new form makes later work cheaper -- hashing for repeated lookup, indexing for repeated access, a snapshot that survives a mutation.  It is pure loss when the consumer would have accepted the original.  So the tell is never the conversion itself; it is what happens next, and which of the two forms that code actually needs.

### how_to_tell

1. Point at the conversion and name what consumes its result.
2. Establish that the consumer accepts the unconverted form. Most builtins taking an iterable do: `sum`, `any`, `all`, `min`, `max`, `str.join`, a `for` loop, `in`.
3. Establish that the result is consumed exactly once, and never indexed, sliced, measured with `len()` or iterated twice. Any of those needs a sequence, and the conversion is doing real work.
4. Check that the conversion is not a snapshot. If the source is mutated, closed or exhausted before the result is read, removing it changes behaviour.
5. Check whether the *receiving operation* has a fast path for the converted type. This is the step that gets skipped, and it is where the answer most often flips -- see the first counter-example.

### discriminators

- **vs C6.S3** — The published examples for these two overlap, so decide by what the patch touches.  C5.S4 *deletes a conversion* and leaves the producer alone (`sum(list(g))` becomes `sum(g)`).  C6.S3 *changes the producer* from eager to lazy (`[f(x) for x in xs]` becomes `(f(x) for x in xs)`).
- **vs C1.S4** — C5.S4 is one conversion whose output is used as its input would have been.  C1.S4 is the *same* computation performed twice.  Converting the same value in two separate places is C1.S4; converting it once and never needing it converted is C5.S4.

## C6.S1

### mechanism

Every Python object costs an allocation, a header, and eventually the collector's attention: a bare `[]` is 56 bytes and a `malloc`, a small class instance is two allocations (the object and its `__dict__`).  Creating them inside a loop pays that per iteration for objects the program discards immediately.  The cost is dominated by the allocator and the reference counting rather than by the bytes, which is why the effect tracks the *number* of objects rather than their size -- and why a million tiny throwaway objects cost more than one large one.

### how_to_tell

1. Point at the creation and say how many times it happens: per iteration, per call, per element.
2. Establish the object is discarded rather than kept. An object created per iteration and appended to a result is needed; one created per iteration, read, and dropped is not.
3. Say what replaces it -- a single instance reused, a literal instead of a constructor call, a shared immutable, or nothing at all.
4. For the reuse form, establish that no iteration's version of the object escapes. If they are collected, or stored, or captured by a closure, they must be distinct and reuse is a bug.
5. Check the object is genuinely redundant rather than cheap. `dict()` versus `{}` is one avoided global lookup and a call; that is real and small, and the honest report for a cold path is advisory.

### discriminators

- **vs C5.S3** — C6.S1 changes how *many* objects exist.  C5.S3 keeps the count and makes each one lighter -- `__slots__`, a namedtuple, a tuple instead of a dict.  If the repair changes a count, it is C6.S1.
- **vs C3.S3** — C3.S3 is about a creation being *per iteration* when it could be hoisted; C6.S1 is about objects that need not exist at all.  If the loop is incidental to the finding, it is C6.S1.
- **vs C6.S3** — C6.S3 is specifically about *materialising a sequence* that could be produced lazily.  C6.S1 is about object count generally.

## C6.S2

### mechanism

A copy walks the source and allocates a container of the same size, so it costs a full pass plus an allocation.  `sorted(xs)` builds a new list where `xs.sort()` reorders in place; `a + b` allocates where `a.extend(b)` grows the existing buffer; a defensive `list(xs)` before a read-only traversal allocates for nothing.  The saving is that pass and that allocation -- and the reason the repair is so often unavailable is that the copy was buying something: isolation from a caller who must not see the mutation.

### how_to_tell

1. Point at the copy: `sorted()`, `list()`, `.copy()`, `dict(other)`, a full slice `xs[:]`, or an element-by-element transfer loop.
2. Establish that nothing needs the original afterwards in its original form. This is the whole question, and it usually requires reading the callers, not just the function.
3. Say who owns the data. Mutating a caller's argument in place is a behaviour change even when the return value is identical, and whether it is safe is a fact about the call sites.
4. Check for aliases. If the object was already shared -- stored on `self`, registered somewhere, captured -- an in-place mutation is visible in places you have not read.
5. Size it. The saving is one pass and one allocation, so it needs a large container or a hot loop.

### discriminators

- **vs C5.S4** — C6.S2 removes a *copy of the same representation*.  C5.S4 removes a *conversion between representations*.  `list(xs)` where `xs` is already a list is C6.S2; `list(generator)` is C5.S4.
- **vs C6.S3** — C6.S2 is about duplicating data that already exists.  C6.S3 is about materialising data that has not been produced yet.
- **vs C10.S3** — An element-by-element copy loop replaced by `extend` or a slice fits both.  Report C6.S2 when the point is the redundant duplication and C10.S3 when the point is the unbatched per-element call.

## C6.S3

### mechanism

A list comprehension runs to completion and allocates a container holding every result; a generator expression produces one element per request and holds only the current one.  For a large sequence that difference is the whole result set in memory against a constant -- and if the consumer stops early, it is also all the elements after the stopping point never being computed.
What the generator costs is not free, and this is where the received advice overreaches.  Each element requires resuming a suspended frame and suspending it again, which is more per-element interpreter work than a comprehension's dedicated append bytecode.  So the trade is *allocation and peak memory* against *per-element resumption*, and which side wins depends on how many elements there are, how large they are, and whether the consumer runs to the end.

### how_to_tell

1. Say what consumes the materialised sequence, and whether it consumes it exactly once. Anything indexed, sliced, `len()`-ed, iterated twice or returned needs a sequence, and a generator would be wrong rather than merely different.
2. Establish that the source is large enough for peak memory to matter, or unbounded. Streaming a file line by line instead of `.read()` is the clearest case, because the alternative is bounded only by the file.
3. Establish whether the consumer can stop early. `any`, `all`, `next`, `in` and a `break` all mean the elements after the stopping point are never computed, which is a real saving on top of the memory one.
4. If none of the above holds -- a short sequence, consumed fully, by a C-level function -- then say so and expect the generator to be *slower*. Measured on this project's host, `sum([x*2 for x in values])` came out 22% ahead of the generator form for a hundred thousand elements.
5. Check the source is not something a lazy consumer would keep alive too long: a cursor, an open file, a lock held for the duration.

### discriminators

- **vs C5.S4** — Decide by what the patch touches.  C6.S3 *changes the producer* from eager to lazy: `[f(x) for x in xs]` becomes `(f(x) for x in xs)`.  C5.S4 *deletes a conversion* and leaves the producer alone: `sum(list(g))` becomes `sum(g)`.
- **vs C6.S1** — C6.S3 is about one container holding every result.  C6.S1 is about the number of objects created generally.
- **vs C3.S5** — When the saving comes from the consumer stopping early rather than from the allocation, the finding is C3.S5.

## C6.S4

### mechanism

Retaining more than the use case needs keeps memory resident that could have been released, which costs in three ways: the allocator's footprint, the garbage collector's traversal of a larger live set on every collection cycle, and -- once the working set exceeds physical memory -- paging.  The first two are modest and continuous; the third is a cliff.  Retention is unusual in this taxonomy because its cost is not paid at the point of the code that causes it: a cache holding whole objects rather than identifiers costs nothing where it is written and slows every collection cycle for the life of the process.

### how_to_tell

1. Find something long-lived that holds data: a cache, a module-level registry, an instance attribute, a closure, a queue.
2. Say what the retained data is used for later, by reading the code that reads it. If only an identifier, a count or a hash is ever consulted, the rest is retained for nothing.
3. Establish the lifetime is genuinely long. A local that dies at the end of the function retains nothing; this root cause needs the reference to outlive the work.
4. Say roughly how much is retained and for how long. "A dict of ten thousand user objects for the life of the process" is a finding; "a list of ten strings" is not.
5. Check that re-fetching what you dropped is cheaper than keeping it. Storing identifiers and looking the objects up again trades memory for I/O, and that is a bad trade if the lookup is a network call.

### discriminators

- **vs C5.S3** — C6.S4 keeps fewer *things*.  C5.S3 keeps the same things in a lighter *representation*.  Dropping fields is C6.S4; `__slots__` is C5.S3.
- **vs C6.S5** — C6.S4 is about data that was genuinely produced and did not need keeping. C6.S5 is about capacity reserved for data that never arrived.
- **vs C8.S1** — These pull in opposite directions and both can be right about the same cache.  C8.S1 says to store more so work is not repeated; C6.S4 says to store less so memory is not held.  Say which cost you are choosing.

## C6.S5

### mechanism

A pre-allocated buffer larger than the workload needs costs its full size in resident memory and in the zeroing or filling that created it, for capacity that is never used.  Python's own containers grow geometrically and need no hint, so this root cause is mostly reachable through explicit sizing: a list multiplied out to a fixed length, a `bytearray` of a fixed size, a NumPy array allocated at a worst-case shape, a pool or queue configured with a maximum far above the observed load.  The cost is a one-off per allocation rather than per element, so it matters when the buffer is large or allocated repeatedly.

### how_to_tell

1. Find an explicit size: a multiplication, a `maxsize`, a shape argument, a capacity hint.
2. Establish what the typical workload actually uses, and say how you know -- from the callers, the fixtures, the documentation, or a measurement.
3. Compare the two. This root cause needs a gap of an order of magnitude, not a factor of two.
4. Establish that the size is not a hard requirement. A buffer matching a protocol's maximum frame, or a pool sized for a burst that does occur, is correctly sized for its worst case rather than its average.
5. Check that shrinking it does not simply move the cost. A buffer that grows dynamically reallocates and copies, and doing that repeatedly can cost more than the over-allocation did.

### discriminators

- **vs C6.S4** — C6.S5 reserves capacity for data that never arrives.  C6.S4 keeps data that did arrive and was not needed afterwards.
- **vs C6.S1** — C6.S5 is one allocation that is too big.  C6.S1 is too many allocations.

## C6.S6

### mechanism

An operating-system resource -- a file descriptor, a socket, a database connection, a cursor -- is held until something releases it.  CPython's reference counting usually releases it promptly when the last reference goes, which is why the sloppy form so often works, but "usually" is doing a lot of work: a reference caught in a cycle waits for the collector, an exception on the path leaves the handle bound in a traceback, and PyPy or Jython do not refcount at all.  The energy cost of holding one open is small; the cost of exhausting a descriptor table or a connection pool is a failure mode rather than a slowdown, and a leaked connection can hold a server-side session and its memory for as long as the process runs.

### how_to_tell

1. Find an acquisition -- `open`, `socket`, `connect`, `cursor` -- whose result is bound to a name rather than acquired in a `with` header.
2. Establish that nothing releases it. A `.close()` on a straight-line path, a `try`/`finally`, or a later `with` that adopts the handle all count as release, and reporting one of those is the commonest false positive.
3. Establish that ownership does not leave the function. A handle returned, yielded, stored on `self`, appended to a list of handles, or entered into an `ExitStack` belongs to someone else, and closing it here would be wrong.
4. Check the failure path. The question is not only whether it closes but whether it closes when the code between raises -- which is what a `with` guarantees and a trailing `.close()` does not.
5. Say what the volume is. One handle in a script is untidy; one per iteration of a loop over ten thousand inputs is an exhaustion bug.

### discriminators

- **vs C9.S1** — C6.S6 is about *releasing* a resource.  C9.S1 is about how many times one is used -- open once and write a thousand times rather than opening a thousand times.  If the repair moves an acquisition out of a loop, it is C9.S1 or C3.S3.
- **vs C3.S3** — C3.S3 hoists a per-iteration acquisition out of the loop.  C6.S6 wraps an acquisition so it is released.  A loop that both opens per iteration and never closes has one repair and both labels; pick one.

## C6.S7

### mechanism

A default argument is evaluated once, when the `def` statement runs, and the resulting object is stored on the function and shared by every call that does not supply its own.  For an immutable default that is invisible.  For a list, dict or set it means the same object accumulates across calls: memory grows without bound for the process lifetime, and any operation whose cost depends on the container's size gets slower with every call that touched it.  The energy cost is a consequence of the correctness bug rather than a separate thing -- the function is doing more work each time because it is carrying every previous call's data.

### how_to_tell

1. Find a parameter whose default is a mutable literal or a call producing a mutable object -- `[]`, `{}`, `set()`, `list()`, `dict()`, a dataclass instance, a `datetime.now()`.
2. Establish that the body mutates it. A mutable default that is only read is not accumulating anything, though it is still fragile.
3. Establish that callers do sometimes omit the argument. If every call site passes one, the default is never used and nothing accumulates -- though the next caller will be the one that finds out.
4. Check whether existing behaviour depends on the accumulation. It happens: a memo built accidentally in a default argument works, and replacing it with `None` silently removes a cache.
5. Say what the growth is per call, so the finding states the consequence rather than only the pattern.

### discriminators

- **vs C6.S4** — Both end with something retained too long.  C6.S7 is specifically the default-argument mechanism, and the retention is accidental.  C6.S4 is a deliberate store holding more than it needs.
- **vs C8.S1** — A mutable default used *deliberately* as a memo is C8.S1 done badly -- the repair is `functools.cache`, not `None`.  Read whether the sharing is load-bearing before choosing.

## C7.S1

### mechanism

Complexity is the only thing in this taxonomy that changes the *shape* of the cost curve rather than its constant factor.  Every other root cause makes each element cheaper; this one changes how many element-operations there are.  A linear scan over a sorted list is n comparisons where a binary search is log2(n) -- twenty against a million -- and a quadratic pairwise scan is n^2 where a hash-based pass is n.  That means the saving grows without bound as the input grows, and equally that it is negligible at small n, where the better algorithm's constant factor and setup cost can lose outright.

### how_to_tell

1. Name the algorithm the code implements and the algorithm you would replace it with. Both, by name. "A linear scan over sorted data" and "`bisect.bisect_left`"; "a hand-written insertion sort" and "Timsort via `sorted`". If you cannot name both, this is not the root cause -- you have noticed slowness, which is not the same thing.
2. State both complexities and where they cross. The better algorithm has a larger constant almost always, so there is an n below which the original wins, and you should know roughly where it is.
3. Establish that the replacement computes the same thing, including at the edges: ties, duplicates, empty input, the order of equal elements, and floating-point accumulation order.
4. Establish the input reaches the size where it matters, and say how you know. This is where most candidates fail: the code is quadratic and n is always eight.
5. Check the precondition the better algorithm needs. Binary search needs sorted input; a hash approach needs hashable keys; a sieve needs a bounded range. If the precondition has to be established first, its cost counts against the repair.

### discriminators

- **vs C10.S1** — The distinction that matters most here.  C7.S1 changes the *algorithm*: different complexity, different approach.  C10.S1 keeps the algorithm and runs it in C instead of in the interpreter.  A hand-written bubble sort replaced by `sorted()` is C7.S1 -- Timsort is a different algorithm.  A summing loop replaced by `sum()` is C10.S1 -- it is the same algorithm.
- **vs C3.S4** — C3.S4 removes a level of loop nesting while keeping the approach.  C7.S1 replaces the approach.  They co-occur often; report C3.S4 when the repair is recognisably "index the inner scan" and C7.S1 when the new code has a different name.
- **vs C5.S1** — If the whole repair is a container type at its construction site, it is C5.S1 even though the complexity changed.  C7.S1 requires the *logic* to change, not only what holds the data.
- **vs C7.S2** — C7.S1 swaps a known algorithm for a better-known one.  C7.S2 keeps the approach and stops it exploring subproblems it did not need -- pruning, ordering, reusing overlapping results.

## C7.S2

### mechanism

A search explores a space of subproblems, and its cost is how many of them it visits.  Three things make that number larger than necessary and all three are decomposition failures rather than algorithm failures.  Overlapping subproblems get re-solved from scratch, which is what turns naive Fibonacci from linear into exponential.  Branches that cannot contain a solution get explored anyway, because no bound is checked before descending.  And the exploration order delays the discovery that would have pruned the rest.  The repair keeps the algorithm's shape and changes which parts of the space it touches -- which is why the saving can be an entire exponent while the code changes by three lines.

### how_to_tell

1. Say what the subproblem space is and how the code walks it: recursion, an explicit stack, nested loops over combinations.
2. Name which of the three failures applies. Are the same subproblems reached by more than one path (memoise)? Can a branch be ruled out before descending (prune)? Would a different order find the pruning bound sooner (reorder)?
3. For the overlapping case, establish that subproblems really do repeat, by describing two paths that reach the same one. A tree with no shared subproblems gains nothing from memoisation but pays for the table.
4. For pruning, name the bound and confirm it is sound -- that no pruned branch could have contained a better answer. An unsound bound is a wrong answer, not a faster one.
5. Establish the space is large enough to matter. Exhaustive search over twelve combinations does not need pruning.

### discriminators

- **vs C8.S1** — Both add a cache and the split is what is being reused.  C7.S2 reuses *subproblem results within one search*, and the memo usually dies with the call.  C8.S1 caches *a function's results across calls* made by unrelated callers.  Ask whether the cache would still help if the function were called only once.
- **vs C7.S1** — C7.S2 keeps the approach and visits less of the space.  C7.S1 replaces the approach.  If the code's name changes, it is C7.S1.
- **vs C3.S6** — C3.S6 is about a loop touching elements it did not need.  C7.S2 is about a *search* exploring states it did not need.  If there is no subproblem structure, it is C3.S6.

## C7.S3

### mechanism

A Python call is expensive relative to a loop iteration: a frame object of two to four hundred bytes is allocated, arguments are bound into it, and it is torn down on return.  CPython does no tail-call elimination, so a self-recursive function pays that per level and holds every frame alive until the base case returns.  A loop with an accumulator does the same arithmetic in one frame.  The saving is therefore the frame cost times the depth -- and there is a correctness dimension too, since the default recursion limit is 1000 and a linear recursion over a large input raises rather than running slowly.

### how_to_tell

1. Establish the recursion is *linear* -- exactly one self-call on each path -- so the recursion is only sequencing, not branching. That is the case an accumulator loop replaces directly.
2. If it branches -- two or more self-calls, a tree, divide and conquer -- say so and reject. An explicit stack there is a reimplementation of the call stack in slower Python, and usually a regression.
3. Say what the accumulator is and confirm the loop can carry it: a running total, a product, a built list, a pair of values.
4. Establish the depth is worth it. A recursion three levels deep saves three frames; one a thousand deep is also a `RecursionError` waiting to happen, and that is worth reporting even where the energy saving is not.
5. Check the recursion is not the clearer expression of something genuinely recursive, on a path where depth is bounded and small.

### discriminators

- **vs C7.S2** — C7.S3 is about the *cost of the frames* in a recursion that visits each subproblem once.  C7.S2 is about a recursion that visits the same subproblem repeatedly.  If the saving is a complexity class rather than a constant factor, it is C7.S2.
- **vs C2.S3** — Both are about call overhead.  C7.S3 is a function calling *itself*; C2.S3 is a chain of different functions.

## C7.S4

### mechanism

When two operations commute, the order decides how much data the expensive one sees.  Filtering before transforming means the transform runs on the survivors; sorting after taking the top k means the sort sees k elements rather than n.  The saving is the expensive operation's per-element cost multiplied by the elements the cheap one removed -- so it scales with selectivity, and it is nothing when the cheap step removes nothing.  This is the same principle as short-circuit ordering in a boolean expression (C4.S1), applied to statements instead of operands.

### how_to_tell

1. Name the two operations, say which is more expensive per element, and say which currently runs first.
2. Prove they commute -- that running them in the other order gives the same answer. This is where the repair usually fails: a filter whose predicate reads the transform's output cannot move before it.
3. Say what fraction the cheap operation removes. High selectivity is the whole effect; a filter that keeps 95% of the rows is not worth reordering for.
4. Check the reorder does not change ties, ordering or numerical results. A sort applied to a filtered list can order equal elements differently, and floating-point sums change with order.
5. Check the cheap operation is actually cheap after the move. Deduplicating a million unique values to shrink a scan costs more than the scan.

### discriminators

- **vs C3.S6** — Nearly the same idea and the split is scope.  C7.S4 reorders *two operations* that are both already bulk steps -- two statements swapped. C3.S6 is about a *loop or comprehension* touching more elements than it needs -- a filter moved inside.
- **vs C4.S1** — The same principle at different granularity.  C4.S1 orders *operands* in one boolean expression; C7.S4 orders *statements* in a pipeline.
- **vs C7.S5** — C7.S4 keeps both operations and swaps them.  C7.S5 makes one of them cheaper, or removes it, using an algebraic fact.

## C7.S5

### mechanism

An expensive operation applied to an input that could have been reduced first does more work than the answer requires.  The reduction is algebraic rather than structural: a term that is provably zero or an identity, a wrapper that cannot change its argument, a general procedure whose result is determined by a cheap property of the input, a transformation the following step is invariant under.  The saving ranges from one operation per element to the entire computation, and unlike everything else in this category it needs knowledge of *what the values mean* rather than of the control flow -- which is why it is the root cause a reading agent can find and no tool can.

### how_to_tell

1. Point at the expensive operation and state the algebraic fact that makes part or all of it unnecessary. Write it out: "`k = max(a, b)` so `k - a >= 0`, so `abs` cannot change it"; "softmax is monotonic, so `argmax` does not need it".
2. Establish the fact holds for every input the function accepts, not only for the ones it usually gets. This is the step that decides correctness, and "it has always been positive so far" is not the same as "it cannot be negative".
3. Say what the simplified form is and check it agrees with the original everywhere -- including at the edges the fact is silent about: NaN, empty input, zero, negative zero, overflow.
4. Say what the saving is per execution: one call per element, one pass, or the whole operation.
5. Distinguish this from adding a guard. If the simplification applies to *all* inputs, it is this root cause; if it applies only to some and needs a branch, it is C4.S7.

### discriminators

- **vs C4.S7** — C7.S5 makes the operation cheaper for *every* input, with no branch added. C4.S7 adds a *guard* that skips the operation for some inputs.  Branch added: C4.S7.  Operation changed: C7.S5.  When one edit does both, say which you picked.
- **vs C1.S5** — The closest neighbour, and the softmax example sits between them.  C1.S5 is work whose *result is never consumed at all*.  C7.S5 is work whose result is consumed but whose cost was not needed to produce the answer. If deleting the statement leaves the code correct with no other change, it is C1.S5.
- **vs C4.S2** — C4.S2 deletes a *test* whose answer was determined.  C7.S5 changes an *operation* using a fact about the values.  No branch is removed here.
- **vs C7.S4** — C7.S4 keeps both operations and reorders them.  C7.S5 makes one cheaper or removes it outright.

## C8.S1

### mechanism

Memoisation replaces a computation with a dict probe.  Whether that is a saving depends on one ratio: how many distinct inputs there are against how many calls.  A million calls over five hundred distinct values means the function runs five hundred times instead of a million, and the other 999 500 calls become hash lookups -- which is where the 95% figures in this project's measurements come from.  A million calls over a million distinct values means a million computations plus a million dict insertions, which is strictly worse, plus a table holding every result for the rest of the process.  The key space against the call count is the whole finding.

### how_to_tell

1. Establish the function is deterministic: same arguments, same result, no dependence on a clock, a random source, a file, or mutable global state.
2. Establish it is free of side effects. A memoised function that writes, logs or increments something stops doing so on a hit.
3. Say the ratio -- roughly how many distinct argument values against how many calls -- and say how you know. This is the step that decides whether the repair is a saving or a regression, and it is a fact about the data rather than the code.
4. Confirm the arguments are hashable, and think about the key. `(x, y)` and `(y, x)` are different keys for a symmetric function, and normalising them to `(min, max)` can double the hit rate for free.
5. Say what the cache's lifetime and bound will be. `functools.cache` is unbounded; on a small integer key space that is correct, and on user-supplied strings it is a leak. Choose `lru_cache(maxsize=...)` when the key space is open, and never `@cache` on a method -- it keys on `self` and keeps every instance alive.

### discriminators

- **vs C1.S4** — The line that defines this whole category.  C1.S4 is the same computation twice *in one scope*, repaired with a local.  C8.S1 is the same computation across calls, repaired with something that outlives the call.  If a local fixes it, it is C1.S4.
- **vs C5.S2** — C8.S1 stores *the result of a computation*.  C5.S2 indexes *data already in hand*, and the index lives for one invocation.  If the stored thing had to be computed rather than merely located, it is C8.S1.
- **vs C7.S2** — C7.S2 memoises *subproblems within one search*, and the memo usually dies with the call.  C8.S1 caches across unrelated callers.  Ask whether the cache would still help if the function were called only once.
- **vs C6.S4** — These point in opposite directions and both can be right about one cache. C8.S1 says store more so work is not repeated; C6.S4 says store less so memory is not held.  When you add a cache, say what bounds it.

## C8.S2

### mechanism

Some artefacts are expensive to derive and cheap to reuse: a compiled regular expression, a parsed configuration file, a prepared SQL statement, a loaded template, a `struct.Struct`.  Deriving one per use pays the compilation or the parse every time; deriving it once and binding it at module or instance scope pays once for the process.  Unlike memoisation there is no key space to worry about, because there is exactly one artefact -- which makes this the safest repair in the category and the one with the fewest exceptions.  The cost saved is the derivation, which for a regex is a parse and a state-machine build, and for a config file is a syscall plus a parse.

### how_to_tell

1. Point at the derivation and say what it produces: a compiled pattern, a parsed document, a prepared statement, a formatter.
2. Establish the inputs to the derivation are constant. A pattern built from a literal is hoistable; one built from an argument is not.
3. Establish the artefact is safe to share. A compiled pattern is immutable and thread-safe; a database cursor is not, and a parsed config that callers mutate becomes shared mutable state.
4. Decide where it goes -- module scope, a class attribute, or an instance attribute -- and say why. Module scope costs the derivation at import time, which is wrong if the path may never run.
5. Check the standard library is not already doing this. `re` caches compiled patterns internally, so the saving for a regex is the cache probe and the call rather than the compilation, which is smaller than it looks.

### discriminators

- **vs C3.S3** — Same repair, different destination, and that is the whole distinction. Above the loop, so it is re-derived on the next call: C3.S3.  At module or instance scope, so it survives across calls: C8.S2.
- **vs C8.S1** — C8.S2 derives *one* artefact from constants.  C8.S1 caches *many* results keyed on varying arguments.  If the repair needs a dict, it is C8.S1.
- **vs C10.S2** — Replacing `re.match(r"^abc", s)` with a precompiled pattern is C8.S2 -- the repair is reuse.  Replacing it with `s.startswith("abc")` is C10.S2 -- the repair is a cheaper operation.  Ask whether the repair stores something or swaps something.

## C8.S3

### mechanism

Resolving a name is not free, and the cost depends on where it lives.  A local is an array index.  A global is a dict probe in the module namespace, with a second probe into builtins on a miss.  Each dot in an attribute chain is a `__dict__` lookup on the instance, then on the type and its bases, and possibly a descriptor invocation on top.  So `self.config.limits.batch` inside a loop is three lookups plus whatever the descriptors do, per iteration, for a value that never changes.  Binding it to a local before the loop makes every later read a single array index.  Each saved lookup is a few tens of nanoseconds, so this needs a genuinely hot region.

### how_to_tell

1. Point at the chain or the name and count the resolutions per iteration: one per dot, plus one for the base.
2. Establish nothing in the loop can rebind any link in the chain, including through any function the loop calls. A method that reassigns `self.config` invalidates the binding.
3. Check for a property or a descriptor in the chain. If one link computes, the saving is much larger than a dict lookup -- and the semantics may differ, because the property was being re-evaluated on purpose.
4. Say how many iterations. A three-link chain resolved a thousand times is microseconds; the same chain resolved ten million times is worth doing.
5. Check the local alias reads clearly. `batch = self.config.limits.batch` is fine; aliasing four things into cryptic names to save a loop is a net loss outside genuinely critical code.

### discriminators

- **vs C10.S5** — C8.S3 is an *attribute chain* whose cost is repeated `__dict__` lookups and possibly the descriptor protocol.  C10.S5 is a *global or builtin* whose cost is a namespace probe.  Same repair shape, different thing being resolved.
- **vs C3.S2** — C3.S2 hoists a *computation* whose result is invariant.  C8.S3 hoists a *resolution* -- nothing was being computed, only looked up.
- **vs C2.S1** — If the chain ends in a call to a wrapper that forwards, the larger finding is C2.S1 -- remove the layer rather than caching the path to it.

## C8.S4

### mechanism

An external fetch costs orders of magnitude more than anything in the process: a filesystem read is a syscall and possibly a disk seek, a database query adds parsing, planning and a round trip, and a network call adds latency measured in milliseconds.  Repeating one for data that has not changed pays all of that again for a value already in memory.  The energy is spent in three places at once -- the local CPU serialising and waiting, the network interface, and the remote system doing the work again -- which is why this category has the largest per-instance effects in the taxonomy and the least need for a large input to demonstrate them.

### how_to_tell

1. Point at the fetch and establish the same data is retrieved more than once: the same query, the same file, the same endpoint with the same parameters.
2. Establish how often the source actually changes. This is the load-bearing step and it is not a fact about the code: a config that changes on restart can be cached for the process, one that changes per minute needs a TTL, one that changes per write cannot be cached without invalidation.
3. Say what staleness would cost. Caching is a correctness decision as much as a performance one, and "how wrong can this be before someone notices" is the question the repair turns on.
4. Choose the lifetime and say why: per request, per process, a TTL, or invalidated on write. "Cache it" is not a repair; "cache it for the life of the request" is.
5. Check the fetch is not already cached a layer down -- by the ORM's identity map, an HTTP cache header, or the operating system's page cache. If it is, the saving is much smaller than the round trip suggests.

### discriminators

- **vs C9.S1** — C8.S4 is the *same* data fetched more than once, and the repair reuses it. C9.S1 is *different* data fetched in many small calls, and the repair batches them.  Ask whether the repair removes fetches or merges them.
- **vs C9.S3** — C9.S3 is one query per row for *different* rows -- the N+1 pattern -- and the repair joins them.  C8.S4 is the same query repeated.  Read the parameters: identical means C8.S4, varying means C9.S3.
- **vs C8.S1** — C8.S1 caches a *computation*.  C8.S4 caches a *retrieval*.  The difference matters because a retrieval can go stale and a pure computation cannot, which is why C8.S4 needs an invalidation rule and C8.S1 does not.
- **vs C3.S2** — When the repair is simply hoisting the fetch above a loop, both fit. Prefer C8.S4 to record that the hoisted work crossed a process boundary, which is where the cost was.

## C9.S1

### mechanism

Every external operation has a fixed cost before any data moves: a syscall boundary, a buffer flush, a protocol frame, a query parse, a network round trip.  Doing the work in N small operations pays that fixed cost N times; one bulk operation pays it once and moves the same bytes.  For a file that fixed cost is a syscall and a flush, a microsecond or two; for a database round trip it is parsing, planning and a network hop, a millisecond or more.  So the saving is N times the per-operation overhead, and it is entirely independent of how much data there is -- which is why batching a thousand tiny writes saves more than batching two large ones.

### how_to_tell

1. Establish the call actually leaves the process. This is the first step because it is where most candidates die: `.get()`, `.read()`, `.write()` and `.execute()` are all ordinary in-process method names too. Read what the receiver is.
2. Count the operations per call of the enclosing unit, and say what each one costs -- a syscall, a query, a network hop.
3. Establish the operations are independent, so they can be reordered and combined. If each one's input depends on the previous one's result, batching is unavailable and the finding is C9.S3.
4. Name the bulk form: `writelines`, one buffered `write`, `executemany`, `bulk_create`, a batch endpoint, a single query with an `IN` clause.
5. Check what batching changes about failure and memory. One transaction that fails loses everything where a thousand lose one; one buffered write holds the whole payload in memory. Both are real trade-offs and the finding should name them.

### discriminators

- **vs C9.S3** — C9.S1 is many *independent* operations that can be merged.  C9.S3 is many *dependent* ones, where each round trip's argument comes from the previous result, and the repair is a join rather than a batch.  Ask whether the calls could run in any order.
- **vs C8.S4** — C9.S1 fetches *different* data each time and batches it.  C8.S4 fetches the *same* data repeatedly and reuses it.  Read the arguments.
- **vs C3.S3** — If the repair moves an `open` or a `connect` out of the loop rather than merging the operations inside it, the finding is C3.S3.
- **vs C6.S6** — C9.S1 is about how many times a resource is *used*.  C6.S6 is about whether it is *released*.

## C9.S2

### mechanism

Data that crosses a process boundary is paid for at both ends and in between: the remote system reads and serialises it, the transport carries it, and the local process deserialises it into objects.  Fetching columns, rows or bytes the program never consults pays all three costs for nothing.  Deserialisation is usually the largest share and the least visible -- turning a wide row into Python objects allocates one object per field, so a `SELECT *` that returns forty columns where two are used allocates thirty-eight objects per row and frees them unread.

### how_to_tell

1. Say what is fetched and what is actually consumed. Name the fields, or the rows, or the byte range. "We use two of these columns" is the finding.
2. Establish the source can return less. A `SELECT` can project columns and a range request can fetch bytes; a fixed API endpoint may not, and then the repair does not exist.
3. Establish nothing downstream needs the rest, including code you have not read -- a serialiser that reflects over the row, a logger that dumps it, a caller that passes the object on.
4. Say how much is being saved as a proportion. Two columns of forty is a finding; thirty-eight of forty is not.
5. Check the projection does not cost more elsewhere. Selecting a subset can lose an index-only scan, and asking for a byte range can defeat a cache that held the whole object.

### discriminators

- **vs C6.S3** — C9.S2 reduces what *crosses the boundary*.  C6.S3 reduces what is *materialised locally* from data that has already crossed it.  Streaming a file you still read entirely is C6.S3; asking for a byte range is C9.S2.
- **vs C3.S6** — The same principle either side of a boundary.  C3.S6 filters in Python; C9.S2 filters at the source.  If the repair moves a predicate into a query, prefer C9.S2 -- the saving is transfer, not iteration.
- **vs C9.S1** — C9.S2 is one operation carrying too much.  C9.S1 is too many operations each carrying too little.

## C9.S3

### mechanism

The N+1 pattern: one query returns N rows, and then each row triggers another query for its related data.  The total is N+1 round trips where a join or a prefetch would be one or two.  The cost is dominated by latency and per-query overhead rather than by data volume, so it is largely independent of how much each query returns -- N+1 queries returning one row each cost far more than one query returning N rows, even though the bytes are comparable. It is the commonest expensive mistake in ORM code, and it is invisible at the call site: `order.customer` looks like an attribute read and is a network round trip.

### how_to_tell

1. Establish there is a loop over results of an earlier fetch, and that the loop body triggers another fetch.
2. Establish that the inner fetch is a fetch. In ORM code this is the whole difficulty: a lazy relation is an attribute access that issues SQL. Read the model, not only the loop.
3. Confirm the inner fetches depend on the outer row -- different parameters each time. Identical parameters means the same data is being re-fetched, which is C8.S4.
4. Name the repair and confirm the data layer supports it: a join, an `IN` clause over the collected keys, `select_related`, `prefetch_related`, `joinedload`, a batch endpoint.
5. Check what the joined form costs. A join that multiplies rows across two one-to-many relations can return far more data than the N+1 version did, and then the repair is `prefetch_related`-style separate queries rather than a single join.

### discriminators

- **vs C9.S1** — C9.S1 is many *independent* operations, merged into a batch.  C9.S3 is many *dependent* ones, where the second fetch needs the first result, merged into a join.  Ask whether the inner calls could have run before the outer one.
- **vs C8.S4** — Read the parameters of the inner fetch.  Varying per row: C9.S3.  Identical every time: C8.S4, and the repair is to hoist or cache rather than to join.
- **vs C3.S4** — The same structure -- a nested lookup -- on either side of a process boundary.  In memory it is C3.S4 and the repair is a dict; across a boundary it is C9.S3 and the repair is a join.

## C9.S4

### mechanism

Some queries are expensive for the engine to execute whatever the client does, and the cost is paid entirely at the far end -- in CPU, in temporary storage, and in energy on a machine this process is not measuring.  A missing join condition produces a Cartesian product, so two ten-thousand-row tables become a hundred million rows.  `UNION` sorts and deduplicates where `UNION ALL` does not.  A predicate wrapped in a function -- `WHERE lower(email) = ?` -- cannot use an index on `email`, so a lookup becomes a full scan.  And a query built by string interpolation is textually different on every execution, so the engine's plan cache never hits and every call re-parses and re-plans.

### how_to_tell

1. Read the query text and name the specific structure that is expensive: a missing join predicate, a deduplicating `UNION`, a function applied to an indexed column, a `LIKE '%...'` that cannot use an index, a correlated subquery per row.
2. Establish it is expensive here, from the schema and the data. A Cartesian product between two three-row tables is nine rows. Row counts and indexes are what make this a finding, and they are facts about the database rather than the code.
3. For a parameterisation finding, establish the query text really does vary. An f-string that interpolates a constant produces one distinct statement and caches fine; one that interpolates an id produces a new statement per call.
4. Name the repair and confirm it preserves the result: `UNION ALL` only when the inputs are provably disjoint, a rewritten predicate only when it selects the same rows including at the edges -- case, nulls, collation.
5. Say how you would confirm it. `EXPLAIN` is the instrument for this root cause, and a finding without it is a guess.

### discriminators

- **vs C9.S2** — C9.S4 is about the *engine's* cost to execute the query.  C9.S2 is about how much data comes back.  A query that returns three rows after scanning ten million is C9.S4; one that returns ten million rows to use three is C9.S2.
- **vs C9.S1** — C9.S4 is one query that is structurally expensive.  C9.S1 is many queries that are individually cheap.
- **vs C7.S1** — The same idea in a different execution engine.  When the algorithmic problem is in SQL the engine will execute, it is C9.S4; when it is in Python, C7.S1.

## C10.S1

### mechanism

A Python loop pays the interpreter on every element: a bytecode dispatch per operation, an unboxed-to-boxed round trip for each intermediate, a reference count increment and decrement per binding, and a frame lookup for every name. A C-implemented primitive does the whole traversal inside one C loop and pays none of it.  That is where the factor of five to fifty comes from, and it is entirely a *per-element* saving -- so it needs many elements, and it evaporates when the primitive is asked to touch elements the program does not need.  A primitive called once on two values is not a bulk operation at all; it is a function call where the loop had a comparison.

### how_to_tell

1. Name the primitive that does this job, and confirm it does the *same* job. `min`/`max` for a running extreme, `sum` for a total, `any`/`all` for a short-circuiting predicate, `Counter` for a tally, `set.intersection` for common members, `bisect` for a position in sorted data, `str.find` for a substring scan.
2. Establish that the loop's body is per-element interpreter work and nothing else -- no side effect, no early exit the primitive cannot express, no accumulation of two things at once. A loop that computes a sum and a maximum in one pass is not two primitives; replacing it with both costs two traversals.
3. Check the primitive is not asked to do more work than the loop did. This is the step that most often reverses the verdict. `Counter(items)` tallies every element; if the code then keeps a tenth of the result, the primitive counted nine tenths for nothing and the hand loop that skipped them is faster. The same applies to sorting when only the top k is wanted.
4. Count the elements. The saving is per element, so it needs thousands. On two scalars per iteration -- `max(best, value)` inside a loop -- the primitive pays a call, builds a tuple and returns, where the comparison is one bytecode: there the loop is right and the primitive is the smell.
5. Check the loop is not already the cheaper form because it exits early. A hand loop that returns on the first match beats a primitive that materialises everything first, however C-level that primitive is.

### discriminators

- **vs C10.S3** — C10.S1 replaces the *whole loop* with a primitive that computes the answer.  C10.S3 keeps the loop's shape and replaces a per-element operation with a batched one -- `append` in a loop becoming `extend`.  If a loop survives the repair, it is C10.S3.
- **vs C10.S2** — C10.S1 replaces hand-written code with a primitive.  C10.S2 replaces one primitive with a better primitive.  If there was no loop to begin with, it is C10.S2.
- **vs C7.S1** — C10.S1 keeps the algorithm and changes what executes it.  C7.S1 changes the algorithm -- different complexity, different approach.  Replacing a bubble sort with `sorted()` is C7.S1, because Timsort is a different algorithm; replacing a summing loop with `sum()` is C10.S1, because it is the same algorithm in C.
- **vs C3.S5** — If the hand loop is better *because it exits early*, the honest finding may be the reverse -- a primitive that materialises everything where the loop short-circuits.  Report that under C3.S6 or C7.S4, not here.

## C10.S2

### mechanism

Two constructs that compute the same answer can cost very different amounts, because CPython's implementations differ in how much work they do to get there.  `re.match("^abc", s)` walks a compiled state machine; `s.startswith("abc")` compares bytes.  `key in d.keys()` builds a view object before probing; `key in d` probes.  `n % 2` does a full division; `n & 1` masks a bit.  The saving is a fixed amount per call, so it is a finding only where the call count is large -- and the *direction* of the saving is not always what the style guides say, which is what the counter-examples here are for.

### how_to_tell

1. Name both constructs and say what the cheaper one stops doing. If you cannot state the mechanism -- a state machine avoided, an object not built, a division replaced by a mask -- you have a style preference rather than a finding.
2. Establish that the two are equivalent on this data. `str.startswith` matches a literal prefix where `re.match` matches a pattern; `n & 1` gives the wrong sign for negative operands where `n % 2` does not.
3. For `map` against a comprehension, check what the callable is. `map` avoids building a frame per element only when the callable is implemented in C. A lambda or a Python `def` pays a full call per element and loses to the comprehension, whose body is inlined bytecode.
4. Say how many calls there are. A fixed saving per call needs a large call count, and for the smaller cases the honest report is advisory.

### discriminators

- **vs C4.S8** — These overlap almost completely and the split is by what gets rewritten. C10.S2 swaps a **callable or method** for a cheaper one.  C4.S8 rewrites the spelling of a **condition** where CPython has a fast path for the idiom -- `not x` for `len(x) == 0`.  Boolean test: C4.S8.  Function call: C10.S2.
- **vs C10.S1** — C10.S2 has two primitives and picks the better one.  C10.S1 has hand-written code and replaces it with a primitive.
- **vs C8.S2** — Replacing `re.match(pattern, s)` in a loop with a precompiled pattern is C8.S2 -- the repair is *reuse* of a derived artefact.  Replacing it with `str.startswith` is C10.S2 -- the repair is a different, cheaper operation.  Ask whether the repair stores something or swaps something.

## C10.S3

### mechanism

A per-element call pays the full call protocol every time: resolve the attribute, build a bound method, push a frame, return.  A batched primitive resolves once and loops in C.  `lst.append(x)` in a Python loop does N attribute lookups and N calls; `lst.extend(other)` does one of each and copies the pointers in a C loop.  A comprehension goes further and uses a dedicated bytecode with no attribute lookup at all.  Everything here is a per-element constant-factor saving, and it is the most reliably positive family in the taxonomy because the batched form does exactly the same work with less ceremony around it.

### how_to_tell

1. Find a loop whose body is a single per-element operation on a container: `append`, `add`, a subscript assignment, an element copy.
2. Confirm there is a batched form that does the same thing -- `extend`, `update`, a slice assignment, a comprehension, a NumPy vector operation -- and that it produces the same container with the same contents.
3. Establish the loop body has no other effect. A body that also counts, logs or short-circuits is not a pure element transfer, and batching it changes behaviour.
4. For a NumPy loop, confirm the elements are numeric and the operation vectorises. Iterating a NumPy array with a Python loop is the worst of both worlds -- unboxing per element on top of interpreter overhead -- so the saving there is large.
5. Say how many elements. A loop over ten items is not a finding.

### discriminators

- **vs C10.S1** — C10.S3 keeps the traversal and batches the per-element operation, so a loop or a comprehension usually survives.  C10.S1 replaces the whole loop with a primitive that returns the answer.
- **vs C3.S1** — Turning an `append` loop into a comprehension can be read either way, and both are defensible.  C3.S1 frames it as the *iteration construct* being wrong; C10.S3 frames it as the *per-element call* being unbatched.  Pick one, say which, and do not report both.
- **vs C6.S2** — If the repair's point is that a copy was unnecessary rather than that it was unbatched, it is C6.S2.

## C10.S4

### mechanism

Python strings are immutable, so `s = s + part` must allocate a new object and copy both operands -- which over N concatenations of average length M is O(N*M) bytes copied.  That is the textbook account and it is **not what CPython does** for the commonest case.  When an accumulator's reference count is exactly one, the interpreter knows nothing else can observe the old string and resizes it in place, making the loop linear.  The optimisation cannot fire when a second reference exists, and that is what this root cause is actually about: not concatenation, but aliasing.  Through an attribute, a subscript, a global, or a local that is also read inside the loop, every iteration copies everything accumulated so far.

### how_to_tell

1. Find a string accumulator grown with `+=` or `s = s + x` inside a loop.
2. Identify the assignment target, and do this before anything else. An attribute (`self.buf += s`), a subscript (`d["k"] += s`, `xs[0] += s`), or a global or nonlocal name means a second reference exists and the in-place resize cannot fire. A plain local means it can.
3. For a plain local, check whether the name is *read* anywhere inside the loop -- passed to a function, appended to something, captured by a closure. Any of those takes a second reference and reinstates the smell.
4. If the target is an unaliased local that is never read in the loop, reject the candidate and say so. The loop is already linear, and the list-and-join repair measured *slower* on this project's host.
5. Confirm the accumulator is not read mid-loop in a way a deferred join cannot reproduce -- a length check on the partial result, an early exit that inspects it.

### discriminators

- **vs C10.S3** — Both end in a bulk primitive.  C10.S4 is about *where the string lives*: the repair works because the growing value stops being aliased.  C10.S3 is about replacing an element-at-a-time call with a bulk call.  If the accumulator is a plain local, neither applies to the concatenation, and any win comes from the comprehension rather than from the join.
- **vs C6.S1** — C10.S4 is specifically about a string accumulator.  If the repair is about the *count* of intermediate objects rather than about repeated copying of one growing value, it is C6.S1.

## C10.S5

### mechanism

A local read is `LOAD_FAST`: an index into the frame's array of locals.  A global read is `LOAD_GLOBAL`: a dict probe in the module namespace, and on a miss a second probe in builtins.  Recent CPython caches this per bytecode, so the gap is narrower than it used to be -- a few nanoseconds rather than tens -- but it is still a dict probe against an array index.  Aliasing the name to a local before the loop converts every read.  This is the smallest reliable effect in the taxonomy, and it needs roughly a million iterations before it is visible at all.

### how_to_tell

1. Find a global name or builtin read inside a loop -- a module constant, an imported function, `len`, `str`, `int`, `range`.
2. Count the reads per iteration and the iterations. One read in a thousand-iteration loop is nothing; three reads in a million-iteration loop is a few milliseconds.
3. Establish that the binding cannot change during the loop. If another thread or a callee rebinds the module attribute, the loop is deliberately re-reading it and aliasing would freeze a stale value.
4. Check the local alias does not shadow something confusingly, and that the loop body does not already have a local of that name.
5. Ask whether the honest report is advisory. This is worth nanoseconds per read, and a case file that manufactures a visible difference is measuring a quantity nobody will observe.

### discriminators

- **vs C8.S3** — C10.S5 is about *scope* -- a global or builtin whose cost is a namespace probe.  C8.S3 is about an *attribute chain* whose cost is repeated `__dict__` lookups and possibly the descriptor protocol.  Same repair shape, different thing being resolved.
- **vs C3.S2** — Both hoist something out of a loop.  C3.S2 hoists a *computation* whose result is invariant; C10.S5 hoists a *name resolution* whose result was never being computed at all.

## C10.S6

### mechanism

An operator on a built-in type is a single specialised bytecode with a C implementation behind it.  On a user-defined type the same operator is a full method dispatch: look up the dunder on the type, check for a reflected variant, build a bound method, push a frame, run Python, and usually allocate a new instance for the result.  So `a + b` on two `int`s costs a bytecode and `a + b` on two `Money` objects costs a function call plus an allocation.  In a loop that accumulates, the allocation is the larger half: every intermediate result is an object created and immediately discarded.

### how_to_tell

1. Find an operator -- `+`, `*`, `==`, `<`, `in`, `[]` -- applied to instances of a class defined in this codebase, inside a loop.
2. Read the dunder and say what it costs. A `__add__` that allocates a new instance, an `__eq__` that compares several fields, a `__contains__` that scans. If the dunder is a one-line delegation to a primitive, the cost is the call rather than the body.
3. Establish that the loop's intermediate results are not needed as objects. The repair works by doing the arithmetic on primitives and wrapping once at the end, which is only available if nothing observes the intermediates.
4. Confirm the primitive arithmetic preserves the type's invariants -- currency, units, precision, overflow behaviour. This is where the repair most often turns out to be wrong: the class exists because those invariants matter.
5. Count the iterations. One allocation per element needs thousands of elements to matter.

### discriminators

- **vs C2.S1** — Both are per-call overhead on a method.  C10.S6 is specifically an *operator* dispatching to a dunder, where the syntax hides the call. C2.S1 is a named method that only forwards.
- **vs C6.S1** — If the repair's point is the *number of objects allocated* rather than the dispatch cost, report C6.S1.  When one edit removes both -- as the accumulation example does -- pick the one you can defend and subsume the other.
- **vs C5.S3** — C5.S3 makes each instance lighter and keeps the operator.  C10.S6 keeps the type and stops using the operator on the hot path.

## C11.S1

### mechanism

An uncontended `threading.Lock` acquisition is cheap -- a few hundred nanoseconds of atomic operations.  A contended one is not: the waiting thread blocks on a futex, the operating system deschedules and later reschedules it, and the work that could have proceeded in parallel is serialised instead.  The energy cost has two parts, and the second is the one that matters.  Directly, threads spin and context-switch while making no progress.  Indirectly, a lock held across work that did not need protecting turns a parallel section into a serial one while the process continues to pay for every thread's stack, its scheduling, and its share of the GIL handoffs.  Narrowing the critical section lets the unprotected work overlap again.

### how_to_tell

1. Find the lock and read the critical section. Say what shared state it is actually protecting -- name the variable or the structure.
2. Identify work inside the section that touches nothing shared: a computation on locals, a format, a log call, an I/O operation on a private handle. That work is what the repair moves out.
3. Establish there is real contention: more than one thread reaching this lock concurrently, often enough to wait. A lock in single-threaded code costs its uncontended acquisition and nothing else.
4. Confirm narrowing preserves atomicity. Moving a read out of the section creates a window where the value can change before it is used, and if the code relies on read-then-write being indivisible, the repair is a race.
5. Consider whether the lock is needed at all. A `queue.Queue`, a `threading.local`, per-thread accumulators merged at the end, or an immutable snapshot may remove the synchronisation instead of narrowing it.

### discriminators

- **vs C11.S2** — C11.S1 is a lock held too broadly or acquired too often, and the repair narrows or removes it.  C11.S2 is an *architecture* in which everything must pass through one resource, and no amount of narrowing fixes it.  Ask whether a smaller critical section would help.
- **vs C3.S3** — If the repair simply moves the acquisition out of a loop, the finding is C3.S3 -- per-iteration setup that should be hoisted.

## C11.S2

### mechanism

Amdahl's law: if a fraction of the work must run serially, no number of workers reduces the total below that fraction.  A single shared resource -- one connection, one lock all workers acquire, one pipeline stage everything passes through -- makes that fraction close to one, so the system is effectively serial while still paying for concurrency in full: thread stacks, process forks, pickling, scheduling, GIL handoffs, and the context switches of workers waiting their turn.  That is the specific waste here.  The work would have cost the same serially; the concurrency machinery is pure overhead on top.

### how_to_tell

1. Identify the resource everything passes through: one connection, one lock, one queue consumer, one file handle, one external service with a concurrency limit of one.
2. Establish that every worker needs it for a substantial share of its work. A resource touched briefly at the start and end does not serialise the middle.
3. Say what the serial fraction is, roughly, and what speed-up that bounds. If most of the time is inside the shared resource, the concurrency is buying nothing and the honest repair may be to remove it.
4. Name the repair: a pool of the resource, a per-worker instance, sharding the work so each worker owns a partition, or removing the concurrency entirely.
5. Consider that removing the concurrency *is* a repair, and often the right one. A serial program that does the same work without forking, pickling and scheduling uses less energy than a parallel one that cannot parallelise.

### discriminators

- **vs C11.S1** — Ask whether a narrower critical section would help.  If yes, C11.S1.  If the resource itself is the constraint however briefly it is held, C11.S2.
- **vs C11.S5** — Opposite directions.  C11.S5 is serial work that should be concurrent. C11.S2 is nominally concurrent work that is serial in practice -- and its repair is sometimes to become honestly serial.
- **vs C9.S1** — If the shared resource is external and the repair is to batch the operations rather than to duplicate the resource, the finding is C9.S1.

## C11.S3

### mechanism

A thread that is never stopped keeps its stack allocated -- eight megabytes of virtual address space, and whatever it has actually touched resident -- for the life of the process.  If it is doing anything at all, it also periodically acquires the GIL, which every other thread must then wait for: a leaked poller with a one-second sleep costs almost nothing, and a leaked busy-wait costs a core.  Non-daemon threads additionally block interpreter shutdown, so the process cannot exit.  The energy cost scales with how many accumulate, which is why the serious form is a thread started per request or per iteration rather than one forgotten at start-up.

### how_to_tell

1. Find the `Thread(...)`, `Process(...)`, `create_task(...)` or pool construction, and establish nothing stops it: no `join`, no `shutdown`, no cancellation, no shutdown event it watches, and no context manager around it.
2. Say how many are created and how often. One at start-up is untidy; one per request accumulates until the process dies.
3. Say what the thread does while it lives. A blocking wait on a queue costs memory only; a polling loop costs a GIL acquisition per poll; a busy-wait costs a core continuously.
4. Establish whether the lifetime is deliberate. A daemon thread meant to live for the process, started once, is a design decision and not a leak -- and `daemon=True` is the marker for it.
5. Name the repair: a bounded pool reused across requests, `daemon=True` plus a shutdown event, an `ExitStack`, or `asyncio.TaskGroup` for tasks.

### discriminators

- **vs C6.S6** — The same failure applied to different resources.  C6.S6 is a file, socket or connection not released; C11.S3 is a thread, process or task not stopped.  Both are lifetime findings.
- **vs C11.S5** — C11.S5 adds concurrency that was missing.  C11.S3 is about concurrency that was added and never cleaned up -- and a finding of C11.S5 that ignores shutdown creates a C11.S3.

## C11.S4

### mechanism

An event loop runs one coroutine at a time and switches only at an `await`. A synchronous blocking call inside a coroutine therefore stops the entire loop: every other task -- including ones with nothing to do but wait for I/O that has already completed -- makes no progress until it returns.  The energy cost is distinctive and it is the clearest divergence between energy and time in the taxonomy: the core stays occupied doing nothing useful, so the process draws power while the work that could have overlapped does not.  A `time.sleep(5)` in a coroutine burns five seconds of a busy loop where `await asyncio.sleep(5)` yields and lets everything else run.

### how_to_tell

1. Establish the function is a coroutine or runs on the event loop -- `async def`, or a callback scheduled on it.
2. Find the blocking call: `time.sleep`, `requests.get`, `open`/`read`/`write`, a synchronous database driver, `subprocess.run`, or a CPU-bound loop with no `await` in it.
3. Establish it blocks for long enough to matter. A microsecond of computation between awaits is fine; the loop is not a real-time system. Milliseconds of I/O is the finding.
4. Name the repair: the async equivalent (`asyncio.sleep`, `httpx.AsyncClient`, `aiofiles`), or `run_in_executor` for a synchronous library with no async version, or a process pool for CPU-bound work.
5. For a UI thread rather than an event loop, the same reasoning applies with the main thread in place of the loop, and the symptom is a frozen interface.

### discriminators

- **vs C11.S5** — C11.S4 is work blocking a thread that must stay responsive.  C11.S5 is independent work not overlapped at all.  A serial loop of blocking calls in a coroutine is both; report whichever the repair matches and subsume the other.
- **vs C11.S1** — C11.S1 is a lock serialising threads.  C11.S4 is a blocking call serialising coroutines on one thread.  No lock is involved.
- **vs C9.S1** — If the repair batches the external calls rather than overlapping them, the finding is C9.S1.

## C11.S5

### mechanism

Independent work run serially takes the sum of its parts where concurrency could take the maximum.  Whether that lowers *energy* rather than only time depends entirely on what the work is waiting for.  For I/O-bound work the process is idle during each wait, so overlapping the waits removes idle time the machine was paying for anyway -- energy falls with time.  For CPU-bound work there is no idle to reclaim: eight cores at load draw more than one core at load, and the total energy is roughly unchanged or worse while wall time falls.  And two Python-specific costs cut against it in both cases: the GIL means threads do not parallelise CPU work at all, and processes pay a fork plus pickling of every argument and every result.

### how_to_tell

1. Establish the work items are genuinely independent: no shared mutable state, no ordering requirement, no dependency between one result and the next input.
2. Classify the work as I/O-bound or CPU-bound, and say which. This decides both the mechanism and the tool, and getting it wrong produces a repair that cannot help: threads for CPU-bound Python work gain nothing because of the GIL.
3. Estimate the bytes transferred per task against the work per task. For a process pool every argument and every result is pickled both ways, so a task that receives a large structure and computes for microseconds is dominated by transfer.
4. Say what you expect to happen to energy *and* to time, separately, before measuring. For I/O-bound work expect both to fall; for CPU-bound expect time to fall and energy to be flat or worse. A repair that only improves time is still worth reporting, labelled honestly.
5. Account for what concurrency costs even when it works: pool creation, scheduling, and a shutdown path that must exist or you have created a C11.S3.

### discriminators

- **vs C11.S2** — Opposite directions, and worth checking before proposing either.  C11.S5 adds concurrency; C11.S2 is concurrency already added that cannot help because everything funnels through one resource.  Adding workers to a C11.S2 system makes it worse.
- **vs C11.S4** — C11.S4 is a blocking call preventing overlap on a thread that must stay responsive.  C11.S5 is work never arranged to overlap at all.
- **vs C10.S3** — Check this one first for numeric work.  A vectorised call is usually faster than a process pool and has no transfer or fork cost, so C10.S3 is the better repair whenever it is available -- which for array arithmetic it almost always is.
- **vs C11.S3** — A C11.S5 repair that starts workers without a shutdown path has introduced C11.S3.  Every finding here must say how the pool stops.

## C12.S1

### mechanism

A NumPy array is one flat block of memory, and its `strides` decide which logical direction is contiguous in it.  A C-ordered 2-D array stores each row end to end, so walking a row reads consecutive bytes: the hardware prefetcher predicts the next cache line and it is already there.  Walking a *column* steps by the row length each time, so every element lands on a different cache line -- the CPU fetches 64 bytes to use 8, the prefetcher's prediction is wrong every time, and for an array bigger than last-level cache each read goes to DRAM.  The arithmetic is identical.  What changes is how many bytes have to cross the memory bus to do it, and DRAM traffic is one of the few things in a Python program that is expensive in energy but not obviously expensive in code.

### how_to_tell

1. Confirm the data is in a contiguous buffer: a NumPy array, an `array.array`, a `memoryview`, a ctypes array. A list of lists has no layout to get wrong -- its rows are separate heap objects at unrelated addresses -- so this root cause does not apply to one.
2. Establish the layout. Read `arr.flags` or `arr.strides`; C-order means the last axis is contiguous, Fortran order means the first is. Do not assume: a transpose, a slice, or `np.asfortranarray` upstream changes it, and `arr.T` returns a view whose order is the opposite of its base.
3. Establish the traversal direction, and that it is against the layout. The shape to look for is an index expression whose fastest-varying subscript is not the contiguous axis -- `arr[:, j]` inside a loop over `j` on a C-ordered array.
4. Check the size against cache. The effect is a cache-miss effect, so it needs an array that does not fit in last-level cache -- tens of megabytes on a typical server. Below that the whole array is resident and stride costs almost nothing.
5. Confirm the traversal order is a free choice. If the algorithm requires column-at-a-time processing, or the result depends on the order, then the repair is to change the *layout* rather than the loop -- and that is only available if you control where the array is created.

### discriminators

- **vs C10.S3** — These get conflated constantly, and the test is what the patch changes. C12.S1 keeps the Python loop and changes the *order* it reads memory in. C10.S3 *removes* the Python loop in favour of a vectorised call.  A before/after that replaces a loop with `arr.sum()` is C10.S3, and quoting its saving as evidence for C12.S1 is measuring the wrong thing.
- **vs C12.S2** — C12.S1 is a *regular* stride against the layout -- every step the same wrong distance.  C12.S2 is irregular, data-dependent access with no stride to fix.
- **vs C3.S4** — Both involve nested loops over a matrix.  C3.S4 changes how many iterations run; C12.S1 keeps the iteration count identical and changes only which addresses they touch.

## C12.S2

### mechanism

A cache line is 64 bytes -- eight doubles.  Reading one element brings the whole line in, so a traversal that uses all eight gets seven of them free. Scattered access uses one and evicts the rest before they are needed, so the memory bus carries eight times the bytes the computation consumes.  Unlike a regular stride there is no order to fix in the loop: the addresses come from the data.  What can be fixed is either the *order the indices are visited*, so that nearby ones are handled together, or the *density of the structure*, so that the elements actually wanted sit next to each other.

### how_to_tell

1. Confirm the container is a large contiguous buffer and the indices are scattered rather than sequential. Random indices, an index array from a previous computation, a permutation, keys from a hash lookup.
2. Establish that the buffer is much larger than cache. Scattered access inside a resident array is free; this whole root cause is about DRAM.
3. Say which repair is available. Sorting the indices helps only if the visiting order does not matter to the result. Compacting the data helps only if the same subset is read repeatedly, so the copy amortises.
4. Cost the repair against the misses. Sorting n indices is n log n comparisons in the interpreter, which is far more expensive per element than a cache miss -- so this pays only when each index is used for substantial work, or when the sorted order is reused across many passes.
5. Check the access is genuinely scattered rather than sequential-with-gaps. A strided read like `arr[::4]` still walks memory forwards and the prefetcher handles it.

### discriminators

- **vs C12.S1** — C12.S1 is a regular stride you can fix by reordering the loop.  C12.S2 is irregular access you can only fix by reordering the *data* or the visit sequence.
- **vs C5.S1** — If the repair changes the container type -- a dict of populated entries instead of a sparse array -- the finding is C5.S1.  C12.S2 keeps the container and changes the order or the density.
- **vs C6.S4** — Compacting a scattered subset into a dense buffer also reduces footprint. Report C12.S2 when the point is access cost and C6.S4 when the point is how much is retained.

## C12.S3

### mechanism

A modern CPU speculates past a conditional branch, executing ahead on its predicted outcome; when the prediction is wrong the pipeline is flushed and the speculative work is discarded, having consumed energy for nothing.  A branch on effectively random data is mispredicted about half the time.  In CPython none of this is reachable: the interpreter evaluates a conditional through a chain of indirect dispatches, boxed comparisons and refcount updates, and that overhead is one to two orders of magnitude larger than a misprediction penalty -- so the data-dependent branch in Python source contributes almost nothing to what the hardware predictor sees.  The effect is real, and it is only observable in compiled code: a Cython loop, a C extension, a numba-jitted kernel.

### how_to_tell

1. Establish that the loop runs in compiled code. Cython with bounds checking off, a hand-written C extension, a numba `njit` kernel. If it is interpreted Python, stop here -- the answer is no, and saying so is the correct outcome.
2. Establish that the branch is data-dependent and genuinely unpredictable: the condition's outcome must be close to random across iterations rather than mostly one way or in long runs.
3. Say what would make it predictable. Sorting the data so the branch takes long runs of one outcome, or replacing the branch with arithmetic that computes both sides and selects.
4. Cost the repair. Sorting to fix a branch is n log n to save n/2 mispredictions, which almost never pays for a single pass -- it pays when the sorted data is traversed many times.
5. Confirm the branchless form is genuinely branchless. A conditional expression in Cython still compiles to a branch; a multiply by a boolean mask does not.

### discriminators

- **vs C10.S3** — The single most important distinction in this category.  If the repair replaces a Python loop with a vectorised or C-level call, the finding is C10.S3, whatever the branch was doing.  C12.S3 requires the loop to stay in the same language and the branch to stay in the loop.
- **vs C4.S1** — C4.S1 is about which operand is *evaluated*, and it applies in interpreted Python.  C12.S3 is about how the hardware speculates past a branch whose operands are all evaluated either way.
- **vs C12.S2** — Both are about the hardware guessing wrong.  C12.S2 is a wrong guess about the next *address*; C12.S3 is a wrong guess about the next *instruction*.

## C12.S4

### mechanism

In a compiled struct, the fields are laid out at fixed offsets in declaration order, and the hardware brings in a whole cache line at a time. Declaring a large cold buffer before a small hot one pushes the hot fields onto a different line from the struct's header, so touching them costs an extra fetch that a different declaration order would have made free.  Field order also decides how much padding the compiler inserts for alignment.  None of this is visible from Python: a Python object's attributes live in a dict or in slot pointers, at addresses the interpreter chooses, and the author has no say.  The root cause is only reachable through `ctypes.Structure`, `struct` layouts, or a C extension's own types.

### how_to_tell

1. Confirm you are looking at a declared layout -- a `ctypes.Structure` `_fields_` list, a `struct` format string, a Cython `cdef struct` -- and not at an ordinary Python class. If it is an ordinary class, this root cause does not apply and `__slots__` is a different finding (C5.S3).
2. Establish which fields are hot and which are cold, by reading the code that uses the structure rather than by guessing from the names.
3. Establish that the order is a free choice. An externally defined layout -- a wire format, a file header, a struct shared with a C library -- is fixed, and reordering it corrupts the data.
4. Check the structure is used at a volume where an extra cache line per access could matter: many instances, or one instance touched in a tight compiled loop.

### discriminators

- **vs C5.S3** — The distinction that matters, because C5.S3 is what almost every candidate actually is.  C12.S4 reorders fields in a *declared layout* whose addresses are fixed by the declaration.  C5.S3 makes a Python object lighter -- `__slots__`, a namedtuple, a plain tuple -- where the declaration order is irrelevant.
- **vs C6.S5** — C12.S4 keeps every field and changes their order.  C6.S5 is about a buffer sized far larger than the data needs.
