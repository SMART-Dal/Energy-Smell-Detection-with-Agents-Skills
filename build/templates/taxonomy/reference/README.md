# The taxonomy, in full

Twelve categories, sixty-five root causes. This index exists so that a category
can be chosen deliberately rather than recalled.

Read a category card before its root-cause cards. The category card says what
kind of waste the group is about and lists its members with a line each, which
is usually enough to drop most of them.

{{CATEGORY_INDEX}}

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
