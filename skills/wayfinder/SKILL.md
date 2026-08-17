---
name: wayfinder
description: Use when a task is too big and foggy to even approach — charts it on GitHub as small, agent-sized decision tickets, worked one at a time into the SDD Decision Log until the way forward is clear.
license: LICENSE.txt
compatibility: Requires an authenticated gh CLI against a GitHub repository with sub-issues and issue dependencies enabled (see TRACKER.md), network access, write access to the repository holding the SDD Decision Log, and Python 3.9+ for the bundled Decision Log lint. Research and prototype tickets require the sibling research and prototype skills installed; grilling tickets run on the bundled grilling contract. No OS constraint.
metadata:
  selfos.version: "0.2.4"
---

# Wayfinder

An explicit request to run this workflow counts as confirmation. Absent
one, when a task matches, propose the workflow and start only after the
owner confirms in the live session; in an unattended run with no
explicit request, do not start — record the recommendation and continue
the surrounding task.

A loose idea has arrived — too big for one agent session, and wrapped in
fog: the way from here to the **destination** isn't visible yet.
Wayfinding is about finding that way, not charging at the destination.
This skill charts the way as a **shared map** on the repository's GitHub
tracker, then works its **decision tickets** — questions whose
resolution is a decision, not slices of a build to execute — one at a
time until the route is clear.

The destination varies per effort, and naming it is the first act of
charting — it shapes every ticket. Here it defaults to an
**implementation-ready SDD scope**: spec sections sharp enough for the
`slice` skill to ticket the build, so the chain runs wayfinder (fog →
decisions → SDD) → slice (SDD → tracer-bullet issues) → implementation.
Other destinations stay legitimate — a decision to lock before planning
starts, or a change made in place — but a departure from the default is
named explicitly on the map.

## Plan, don't do

Wayfinder is **planning** by default: each ticket resolves a decision,
and the map is done when the way is clear — nothing left to decide
before someone goes and does the thing. The pull to just do the work is
usually the signal you've reached the edge of the map and it's time to
hand off — by default, to `slice`. An effort can override this in its
**Notes** — carrying execution into the map itself — but absent that,
produce decisions, not deliverables.

## Refer by name

Every map and ticket is an issue, so it has a **name** — its title. In
everything the human reads — narration, the map's Decisions-so-far —
refer to it by that name, never by a bare id, number, or slug. A wall of
`#42, #43, #44` is illegible; names read at a glance. The id and URL
don't vanish — a name wraps its link — but they ride _inside_ the name,
never stand in for it.

## The map

The map is a single GitHub issue, labelled `wayfinder:map`, on the
repository whose Decision Log the effort's decisions land in. Its
tickets are native sub-issues of the map; blocking uses native issue
dependencies; the assignee is the claim. The conventions and verified
commands live in [TRACKER.md](TRACKER.md). GitHub access is required
(see `compatibility`): when the tracker is unreachable, stop and say so
— never improvise a local substitute store.

The map is an **index**, not a store. A decision lives in exactly one
place — the repository's **SDD Decision Log** — because issues are host
data: not cloned, not backed up, gone on migration or access loss,
while the log is versioned, reviewed, and greppable offline. The ticket
keeps the question, the discussion, the claim, and the blocking edges —
disposable working state. The map never restates a decision; it gists
it and points into the repo.

Everything written to the tracker — map, tickets, comments — is neutral
original prose under the repository's public-data policy: invented
examples only; no personal data, credentials, private paths, or local
agent state.

### The map body

The whole map at low resolution, loaded once per session. Open tickets
are **not** listed — they are open sub-issues, found by query.

```markdown
## Destination

<what reaching the end of this map looks like — by default the SDD
sections this effort is making implementation-ready. One or two lines;
every session orients to it before choosing a ticket.>

## Notes

<domain; skills every session should consult; standing preferences for
this effort>

## Decisions so far

<!-- the index — one line per closed ticket: enough to judge relevance;
the decision itself lives in the repository's Decision Log -->

- [<closed ticket title>](link) — <one-line gist of the decision> —
  [log](<link to the Decision Log section on the default branch>)

## Not yet specified

<!-- see "Fog of war": in-scope fog you can't ticket yet; graduates as
the frontier advances -->

## Out of scope

<!-- see "Out of scope": work ruled beyond the destination; closed,
never graduates -->
```

### Tickets

Each ticket is a **sub-issue** of the map; the issue id is its
identity. Its body is the question, sized to one agent session:

```markdown
## Question

<the decision or investigation this ticket resolves>
```

Each ticket carries a `wayfinder:<type>` label — one of `research`,
`prototype`, `grilling`, `task` (see [Ticket types](#ticket-types)).

A session **claims** a ticket by assigning it to the dev driving the
map, **first**, before any work, so concurrent sessions skip it. That
assignee _is_ the claim: an open, unassigned ticket is unclaimed.

Blocking uses GitHub's **native** dependency relationship — essential
because it renders the frontier _visually_ in the tracker's own UI, so
the human sees what's takeable without opening the map. A ticket is
**unblocked** when every ticket blocking it is closed; the **frontier**
is the open, unblocked, unclaimed sub-issues — the edge of the known.

The decision isn't part of the body — it's landed in the Decision Log
on resolution (see [Work through the map](#work-through-the-map)).
Assets created while resolving a ticket are linked from the issue, not
pasted in.

## Ticket types

Every ticket is either **HITL** — human in the loop, worked _with_ a
human who speaks for themselves — or **AFK**, driven by the agent
alone. A HITL ticket only resolves through that live exchange; the
agent never stands in for the human's side of it (a grilling agent that
answers its own questions has broken this).

- **Research** (AFK): Reading documentation, third-party APIs, or local
  resources to surface a fact a decision waits on. Resolved by a
  background subagent per the sibling `research` skill: findings on a
  throwaway `research/<name>` branch, a context pointer on the ticket,
  and only the resulting decision graduating into the Decision Log. Use
  when knowledge outside the current working directory is required.
- **Prototype** (HITL): Raise the fidelity of the discussion by making
  a cheap, rough, concrete artifact to react to via the sibling
  `prototype` skill; link the prototype as an asset. Use when "how
  should it look" or "how should it behave" is the key question.
- **Grilling** (HITL): Conversation. The default case. Always run the
  bundled [grilling contract](references/grilling/CONTRACT.md), and invoke
  the host's domain-modeling skill when one is installed.
- **Task** (HITL or AFK): Manual work that must happen before a
  _decision_ can be made — nothing to decide, prototype, or research,
  but the discussion is blocked until it's done. Signing up for a
  service so its API can be judged, provisioning access, moving data so
  its shape can be seen. This is the one type that _does_ rather than
  decides — and it earns its place by unblocking a decision, not by
  delivering the destination. The agent drives it alone where it can
  (AFK); otherwise it hands the human a precise checklist (HITL).
  Resolved when the work is done; the resolution records what was done
  and any resulting facts later tickets depend on — never credentials
  or private data on a public tracker.

## Fog of war

The map is _deliberately_ incomplete: don't chart what you can't yet
see. Beyond the live tickets lies the **fog of war** — the dim view of
decisions and investigations you can tell are coming but can't yet pin
down, because they hang on questions still open. Resolving a ticket
clears the fog ahead of it, graduating whatever's now specifiable into
fresh tickets — one at a time, until the way to the destination is
clear and no tickets remain.

The map's **Not yet specified** section is where that dim view is
written down: the suspected question, the area to revisit later. It's
the undiscovered frontier _toward_ the destination — everything here is
in scope, just not sharp enough to ticket. Write as loosely or as fully
as the view allows; it doubles as a signpost for collaborators reading
where the effort is headed.

**Fog or ticket?** The test is whether you can state the question
precisely now — _not_ whether you can answer it now.

- **Ticket when** the question is already sharp — even if it's blocked
  and you can't act on it yet.
- **Not yet specified when** you can't yet phrase it that sharply.
  Don't pre-slice the fog into ticket-sized pieces: it's coarser than a
  ticket, and one patch may graduate into several tickets, or none,
  once the frontier reaches it.

**Not yet specified** excludes what's already decided (Decisions so
far), what's already a live ticket, and what's out of scope.

## Out of scope

Fog only ever gathers _toward_ the destination. The destination fixes
the scope, so work beyond it is **out of scope** — it isn't fog, and it
doesn't belong in **Not yet specified**. It gets its own **Out of
scope** section on the map: work you've consciously ruled out of _this_
effort. Scope, not sharpness, lands it here.

Out-of-scope work never graduates — the frontier stops at the
destination — so it returns only if the destination is redrawn, and
then as a fresh effort, not a resumption.

Ruling something out of scope is a scoping act, not a step on the
route. When a ticket that already exists turns out to sit past the
destination — mis-scoped in while charting, or exposed by a resolution
— **close it** (a closed ticket is unambiguously off the frontier) and
leave one line in the **Out of scope** section: the gist plus why it's
out of scope, linking the closed ticket. It stays out of **Decisions so
far**, which records the route actually walked — a scope boundary isn't
a step on it.

## Invocation

Two modes. Either way, **never resolve more than one ticket per
session** — with the exception of research tickets.

### Chart the map

User invokes with a loose idea.

1. **Name the destination.** Run the bundled grilling contract (and the
   host's domain-modeling skill when installed) to pin down what this
   map is finding its way to — by default, which SDD scope it is making
   implementation-ready. The destination fixes the scope, so it's
   settled first.
2. **Map the frontier.** Grill again, **breadth-first** this time: fan
   out across the whole space rather than deep on any one thread,
   surfacing the open decisions and the first steps takeable now. **If
   this surfaces no fog** — the way to the destination is already
   clear, the whole journey small enough for one session — you don't
   need a map. Stop and ask the user how they'd like to proceed.
3. **Create the map** (label `wayfinder:map`): Destination and Notes
   filled in, Decisions-so-far empty, the fog sketched into **Not yet
   specified**.
4. **Create the tickets you can specify now** as sub-issues of the map
   — born **claimed** (self-assigned), so the half-wired map never
   shows a falsely-unblocked frontier to a parallel session — then wire
   blocking edges in a **second pass** (issues need ids before they can
   reference each other). Once the edges are in place, release the
   claims, keeping only those on the unblocked research tickets step 5
   is about to fire. Wiring sorts tickets into the frontier and the
   blocked; everything you can't yet specify stays in **Not yet
   specified**.
5. **Fire the research subagents.** For each **unblocked** `research`
   ticket you just created — still claimed from step 4, so no
   concurrent session duplicates the investigation — spin up a
   background subagent per the `research` skill to resolve it in
   parallel. A blocked research ticket waits for the frontier — fired
   early, it would investigate against prerequisites that haven't been
   decided yet.
6. Stop — charting is one session's work; it hand-resolves nothing.

### Work through the map

User invokes with a map (URL or number). A ticket is **optional** —
without one, you pick the next decision, not the user.

1. Load the **map** — the low-res view, not every ticket body.
2. Choose the ticket. If the user named one, verify it is open,
   unblocked, and unclaimed before using it — a blocked ticket resolved
   early lands a decision whose prerequisites haven't closed, so stop
   and say which blocker is still open instead. Otherwise take the
   first frontier ticket in order. **Claim it**: assign it to yourself
   before any work.
3. Resolve it — **zoom as needed**: fetch the full body of any related
   or closed ticket on demand; invoke the skills the `## Notes` block
   names. If in doubt, run the bundled grilling contract (and the
   host's domain-modeling skill when installed).
4. **Land the decision, then close.** First check scope: if resolving
   revealed that this ticket sits beyond the destination, nothing lands
   — rule it out of scope instead (step 5) so a scope boundary never
   pollutes the log or Decisions-so-far. Otherwise the decision lands
   in the
   repository's Decision Log through the repo's normal change flow —
   direct commit or pull request, whichever the repository's convention
   is — as one dated entry carrying the rejected alternative and ending
   with the ticket's reference (`#123`); grammar and lint are the
   bundled [Decision Log
   contract](references/sdd-conventions/conventions/DECISION-LOG.md).
   Then post the **resolution comment**: the entry line quoted
   verbatim, plus a link to the landing commit or pull request.
   **Close** the ticket only after the entry has landed, and append its
   line to the map's Decisions-so-far. A decision ticket without a
   landed log entry is unresolved, however finished the discussion
   looks. The exceptions are the tickets with nothing to decide: a
   `task` ticket closes on a resolution comment recording what was done
   and the resulting facts, and a `research` ticket whose question was
   pure investigation closes on its findings and context pointer — in
   either case no log entry and no line in Decisions-so-far. Any
   decision a task or research run surfaces becomes its own ticket,
   resolved through the log like every other. One more gate on the
   close: when the answer surfaces new tickets or fog, create and wire
   them (step 5) **before** closing this one — otherwise the map can
   momentarily show no open tickets and no fog, and a parallel session
   could hand off to `slice` on a route that isn't actually clear.
5. Add newly-surfaced tickets (create-then-wire); graduate any fog the
   answer has made specifiable, clearing each graduated patch from
   **Not yet specified** so it lives only as its new ticket. If the
   answer reveals a ticket — this one or another — sits beyond the
   destination, **rule it out of scope** rather than resolving it on
   the route. If the decision invalidates other parts of the map,
   update or delete those tickets.

When the map is done — no open tickets, no fog — the default hand-off
is `slice`: the destination's SDD scope is implementation-ready, and
slicing it into tracer-bullet issues is a fresh session's work, not
this skill's.

The user may run unblocked tickets in parallel, so expect other
sessions to be editing the tracker concurrently. Map-body edits are
whole-body replacements, not merges — so re-read the map immediately
before saving, apply your lines to that fresh body, and check after
saving that your edit and any concurrent one both survived; on a lost
update, re-merge and retry.
