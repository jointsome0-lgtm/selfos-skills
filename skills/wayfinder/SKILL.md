---
name: wayfinder
description: Use when a task is too big and foggy to even approach — charts it on GitHub as small, agent-sized decision tickets, resolved one at a time with reasons in the issue and any resulting commit.
license: LICENSE.txt
compatibility: Requires an authenticated gh CLI against a GitHub repository with sub-issues and issue dependencies enabled (see TRACKER.md), network access, write access to the target repository when an outcome changes it. Prototype tickets require the sibling prototype skill installed; grilling tickets run on the bundled grilling contract. No OS constraint.
metadata:
  selfos.version: "2.0.2"
---

# Wayfinder

When a task matches, announce that this workflow is starting and
proceed — the owner can interrupt at any point. Unattended runs may
work through the read-only and draft stages but stop before any
tracker mutation and at every inner confirmation point: no ticket is
claimed, no repository change lands, and nothing publishes
to the tracker without the owner.

Chart a large, unclear effort as a GitHub **map** of **decision tickets**.
Resolve them one at a time until the route to the **destination** is clear.
Define the destination first. By default it is an **approved
implementation-ready scope** for `slice` to turn into vertical implementation
issues. Name any different destination explicitly on the map.

## Plan, don't do

Wayfinder plans by default: tickets settle decisions, and the map ends when
nothing remains to decide before implementation. Include execution in the
map only when its **Notes** override that default.

## Refer by name

In everything the human reads, refer to each issue by its linked title,
never by a bare number, id, or slug.

## The map

The map is one GitHub issue labelled `wayfinder:map` in the effort's
repository. Tickets are native sub-issues; blocking uses native dependencies,
and assignees represent claims. See [TRACKER.md](TRACKER.md) for conventions
and commands. If GitHub is unreachable, stop and report it; do not substitute
a local store.

The map indexes resolutions. Each issue records its decision and reason;
any resulting commit explains why and links to that issue. Code expresses
current behavior; `GOALS.md`, when present, expresses future work. No separate
decision-log file is required.

Write maps, tickets, and comments in neutral original prose under the
repository's public-data policy. Use invented examples; include no personal
data, credentials, private paths, or local agent state.

### The map body

Reload the map before choosing each ticket. Query open sub-issues instead
of listing them in the body.

```markdown
## Destination

<approved scope this map will make implementation-ready, or another stated
destination; one or two lines; orient to it before choosing a ticket>

## Notes

<domain; skills every session should consult; standing preferences;
any execution override>

## Decisions so far

<!-- One line per closed decision ticket; the reason lives in its resolution. -->

- [<closed ticket title>](<resolution comment URL>) — <one-line gist>

## Not yet specified

<!-- In-scope questions too unclear to ticket yet; see "Fog of war". -->

## Out of scope

<!-- Work beyond the destination; see "Out of scope". -->
```

### Tickets

Each ticket is a native sub-issue identified by its issue id. Its body is a
question sized to one agent session:

```markdown
## Question

<the decision or investigation this ticket resolves>
```

Apply one `wayfinder:<type>` label: `research`, `prototype`, `grilling`, or
`task`. See [Ticket types](#ticket-types).

Claim a ticket before work by assigning it to the developer driving the map.
An open, unassigned ticket is unclaimed. A ticket is **unblocked** when all
its blockers are closed. The **frontier** is the open, unblocked, unclaimed
sub-issues.

Record results in a resolution comment under
[Work through the map](#work-through-the-map). Link assets from the issue
instead of pasting them in.

## Ticket types

**HITL** tickets require a live exchange with a human; never answer on their
behalf. **AFK** tickets are driven by the agent alone.

- **Research** is AFK: find a fact a decision needs. Read primary sources and
  cite them in the resolution. Resolve directly or delegate an independent
  lookup when the host supports it and the task permits it. No separate
  findings file or research branch is required.
- **Prototype** is HITL: use the sibling `prototype` skill to make a cheap,
  rough artifact when appearance or behavior is the question. Link the
  prototype as an asset.
- **Grilling** is HITL and the default: follow the bundled
  [grilling contract](references/grilling/CONTRACT.md) and invoke the host's
  domain-modeling skill when installed.
- **Task** is HITL or AFK: do prerequisite work that blocks a decision when
  there is nothing to decide, prototype, or research. It earns its place by
  unblocking that decision, not by delivering the destination. The agent
  drives it where possible; otherwise give the human a precise checklist.
  Resolve when the work is done, recording what was done and facts later
  tickets need. Never record credentials or private data on a public tracker.

## Fog of war

**Fog** consists of in-scope questions you cannot yet phrase precisely;
record it in **Not yet specified**. If you can state a question, create a
ticket even if it is blocked or you cannot yet answer it. Do not pre-slice
unclear areas into tickets.

This section excludes decisions already made, live tickets, and out-of-scope
work. As resolutions clarify it, replace each newly specifiable patch with
tickets. One patch may produce several tickets or none.

## Out of scope

**Out of scope** holds work beyond this map's destination. It never graduates
into this map's tickets. Revisit it only under a redrawn destination in a
fresh effort.

If a ticket proves out of scope, close it and record one line here with its
gist, reason, and link. Exclude it from **Decisions so far**, which indexes
decisions on the route.

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
