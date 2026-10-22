# The taxonomy, in full

An **energy smell** is code that spends energy on work the program does not
need, and that a specific refactoring can remove without changing what the
program does. This taxonomy names them: twelve categories, sixty-five root
causes.

This page is what to look for in step 1. Read it before you read the code, and
keep it beside you: of every function, ask whether any of these is happening
there. The **category table** says what each family of waste covers; the
**root cause table** below it lists all sixty-five, one line each — enough to
recognise one, not enough to decide it. Deciding is step 2, with the root
cause's card.

Cards live at `reference/categories/<ID>.md` — a category's root causes, with
the repair for each — and `reference/root-causes/<ID>.<S>.md`, which open at
`step.py done 1`.

## Categories

{{CATEGORY_INDEX}}

## Every root cause, one line each

{{ROOT_CAUSE_INDEX}}

## Using this well

**Any category may apply to any code.** Nothing about a repository rules a
category in or out in advance. Work from what the code actually does.

**Read the card, not the name, and not the line above.** These names are three
or four words long and several of them cover something narrower — or wider —
than they sound like. The one-line summaries here are index entries, precise
enough to recognise something by and not enough to decide anything from. The
card is the claim.

**The index tells you what to look for, not what you will find.** A unit goes
on your list because of what its code does, not because a line here sounds
like it. Finding nothing in a category is a perfectly ordinary outcome.

**Cards overlap.** When two root causes both describe what you repaired,
either attribution is fine — say which you chose.

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
