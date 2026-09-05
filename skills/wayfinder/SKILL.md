---
name: wayfinder
description: Use when a task is too big and foggy to even approach — charts it on GitHub as small, agent-sized decision tickets, resolved one at a time with reasons in the issue and any resulting commit.
license: LICENSE.txt
compatibility: Requires an authenticated gh CLI against a GitHub repository with sub-issues and issue dependencies enabled (see TRACKER.md), network access, write access to the target repository when an outcome changes it. Prototype tickets require the sibling prototype skill installed; grilling tickets run on the bundled grilling contract. No OS constraint.
metadata:
  selfos.version: "2.0.0"
---

# Wayfinder

When a task matches, announce that this workflow is starting and
proceed — the owner can interrupt at any point. Unattended runs may
work through the read-only and draft stages but stop before any
tracker mutation and at every inner confirmation point: no ticket is
claimed, no repository change lands, and nothing publishes
to the tracker without the owner.

A loose idea has arrived — too big for one agent session, and wrapped in
fog: the way from here to the **destination** isn't visible yet.
Wayfinding is about finding that way, not charging at the destination.
This skill charts the way as a **shared map** on the repository's GitHub
tracker, then works its **decision tickets** — questions whose
resolution is a decision, not slices of a build to execute — one at a
time until the route is clear.

The destination varies per effort, and naming it is the first act of
charting — it shapes every ticket. Here it defaults to an
**approved implementation-ready scope**: goals and decisions precise enough
for `slice` to create vertical implementation issues.
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
repository the effort belongs to. Its
tickets are native sub-issues of the map; blocking uses native issue
dependencies; the assignee is the claim. The conventions and verified
commands live in [TRACKER.md](TRACKER.md). GitHub access is required
(see `compatibility`): when the tracker is unreachable, stop and say so
— never improvise a local substitute store.

The map indexes ticket resolutions. The issue records the decision and
its reason. When a decision changes the repository, the resulting commit
records why and links back to the issue. Code expresses current behavior;
`GOALS.md`, when present, expresses future work. No separate decision-log
file is required.

Everything written to the tracker — map, tickets, comments — is neutral
original prose under the repository's public-data policy: invented
examples only; no personal data, credentials, private paths, or local
agent state.

### The map body

The whole map at low resolution, reloaded before choosing each ticket.
Open tickets are **not** listed — they are open sub-issues, found by query.

```markdown
## Destination

<what reaching the end of this map looks like — by default the approved
scope this effort is making implementation-ready. One or two lines;
every session orients to it before choosing a ticket.>

## Notes

<domain; skills every session should consult; standing preferences for
this effort>

## Decisions so far

<!-- the index — one line per closed ticket: enough to judge relevance;
the decision and reason live in the linked issue resolution -->

- [<closed ticket title>](<resolution comment URL>) — <one-line gist>

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

Record the decision in a resolution comment (see
[Work through the map](#work-through-the-map)).
Assets created while resolving a ticket are linked from the issue, not
pasted in.

## Ticket types

Every ticket is either **HITL** — human in the loop, worked _with_ a
human who speaks for themselves — or **AFK**, driven by the agent
alone. A HITL ticket only resolves through that live exchange; the
agent never stands in for the human's side of it (a grilling agent that
answers its own questions has broken this).

- **Research** (AFK): Reading documentation, third-party APIs, or local
  resources to surface a fact a decision waits on. Read primary sources
  and cite them in the ticket resolution. Resolve it directly or delegate
  an independent lookup when the host supports it and the task permits it.
  No separate findings file or research branch is required.
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

Continue the agreed work while a useful next step is available. Pause
when an owner decision or confirmation is needed, a real blocker prevents
progress, or the agreed goal is complete. Charting, resolving successive
tickets, and moving to slicing do not themselves require a new session.

### Chart the map

User invokes with a loose idea.

1. **Name the destination.** Run the bundled grilling contract (and the
   host's domain-modeling skill when installed) to pin down what this
   map is finding its way to — by default, which approved scope it is making
   implementation-ready. The destination fixes the scope, so it's
   settled first.
2. **Map the frontier.** Grill again, **breadth-first** this time: fan
   out across the whole space rather than deep on any one thread,
   surfacing the open decisions and the first steps takeable now. **If
   this surfaces no fog** — the way to the destination is already
   clear — skip map creation and continue the already-authorized next
   step. If the agreed goal is complete, report the result.
3. **Create the map** (label `wayfinder:map`): Destination and Notes
   filled in, Decisions-so-far empty, the fog sketched into **Not yet
   specified**.
4. **Create the tickets you can specify now** as sub-issues of the map
   — born **claimed** (self-assigned), so the half-wired map never
   shows a falsely-unblocked frontier to a parallel session — then wire
   blocking edges in a **second pass** (issues need ids before they can
   reference each other). Once the edges are in place, release the
   claims, keeping only those on the unblocked research tickets step 5
   is about to investigate. Wiring sorts tickets into the frontier and the
   blocked; everything you can't yet specify stays in **Not yet
   specified**.
5. **Investigate unblocked research tickets.** Keep each claimed while
   resolving its question from primary sources. Independent lookups may
   run in parallel when permitted; blocked tickets wait for their
   prerequisites. Record cited findings in the resolution comment,
   following the close ordering below.
6. Continue with **Work through the map** in this session, selecting
   the next unblocked ticket within the agreed scope.

### Work through the map

User invokes with a map (URL or number). A ticket is **optional** —
without one, you pick the next decision, not the user.

1. Load the **map** — the low-res view, not every ticket body.
2. Choose the ticket. If the user named one, verify it is open,
   unblocked, and unclaimed before using it — a blocked ticket resolved
   early lands a decision whose prerequisites haven't closed, so stop
   and say which blocker is still open instead. Otherwise take the
   first frontier ticket in order. **Claim it**: assign it to yourself
   before any work. Claiming is a tracker mutation: when this run was
   announced rather than explicitly requested, name the chosen ticket
   and claim only after the owner confirms it, and an unattended run
   stops here instead of claiming — so no ticket stays locked with
   nobody working it.
3. Resolve it — **zoom as needed**: fetch the full body of any related
   or closed ticket on demand; invoke the skills the `## Notes` block
   names. If in doubt, run the bundled grilling contract (and the
   host's domain-modeling skill when installed).
4. **Land the decision, then close.** First check scope: if resolving
   revealed that this ticket sits beyond the destination, nothing lands
   — rule it out of scope instead (step 5). If the outcome changes code
   or goals, land that authorized change through the repository's normal
   process first; the commit explains why and references the ticket.
   Then post a **resolution comment** with the confirmed decision,
   reason, any rejected alternative that matters, and the landing
   commit when there is one. Close the ticket
   and index its resolution in Decisions-so-far. A planning-only
   decision needs no empty commit or separate log file. A `task` or
   pure `research` ticket closes on its results and sources, without
   a line in Decisions-so-far. Any new decision it surfaces becomes
   its own ticket. One more gate on the
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

If agreed work remains after resolving a ticket, repeat from step 1 to
reload the map and select from its current frontier. Apply the same claim,
decision, and publication rules to each ticket.

When the map is done — no open tickets, no fog — the destination's approved
scope is implementation-ready. If the agreed work includes slicing,
continue with `slice` in this session under its publication rules.
Otherwise report the completed planning outcome.

The user may run unblocked tickets in parallel, so expect other
sessions to be editing the tracker concurrently. Map-body edits are
whole-body replacements, not merges — so re-read the map immediately
before saving, apply your lines to that fresh body, and check after
saving that your edit and any concurrent one both survived; on a lost
update, re-merge and retry.
