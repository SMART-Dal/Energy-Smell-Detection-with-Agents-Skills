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
