# Wayfinding operations — GitHub

How the skill's tracker conventions map onto GitHub, with verified
commands. `$R` is `owner/repo`. `$N`-style variables hold issue
numbers, and **endpoint paths always take issue numbers** — only the
relationship fields in request bodies (`sub_issue_id`, `issue_id`)
take the numeric database **id** (`gh api repos/$R/issues/$N --jq
.id`). Never swap the two: an id in a path 404s or hits the wrong
issue. Map and tickets live in
one repository (sub-issues must share the repository owner): the one
whose Decision Log the effort lands in.

## Conventions

- **Map** — one issue labelled `wayfinder:map`.
- **Ticket** — a native sub-issue of the map, labelled
  `wayfinder:research`, `wayfinder:prototype`, `wayfinder:grilling`, or
  `wayfinder:task`.
- **Claim** — the assignee, set before any work; an open, unassigned
  ticket is unclaimed.
- **Blocking** — GitHub's native issue dependencies (blocked-by), so
  the tracker UI renders the frontier.
- **Frontier** — open, unblocked, unclaimed sub-issues of the map.

## Preflight

Sub-issues and issue dependencies must be enabled for the repository
(generally available on github.com; verify on GHES) — and one can be
enabled without the other. Probe **both** endpoints read-only, against
any existing issue number, and stop with a clear message on an error
**before** mutating anything — labels, map, or tickets — rather than
failing mid-chart or falling back to another store:

```bash
n=$(gh issue list --repo "$R" --state all --limit 1 \
  --json number --jq '.[0].number')
gh api repos/$R/issues/$n/sub_issues --jq length
gh api repos/$R/issues/$n/dependencies/blocked_by --jq length
```

In a repository with no issues at all, create the labels first (label
creation needs no issues), then the map carrying its `wayfinder:map`
label — a plain labelled issue works everywhere — and probe against
its number before creating any tickets. One stray issue to close is
the worst case, not a half-built map.

Create the labels once per repository (safe to re-run):

```bash
for t in map research prototype grilling task; do
  gh label create "wayfinder:$t" --repo "$R" --color BFD4F2 \
    --description "wayfinder $t" 2>/dev/null || true
done
```

## Create the map

```bash
gh issue create --repo "$R" --title "<map name>" \
  --label wayfinder:map --body-file map.md
```

## Create a ticket, then attach it

`gh issue create` prints the new issue's URL; the number is its last
path segment. `$TYPE` is the ticket's type — `research`, `prototype`,
`grilling`, or `task`. During charting, create every ticket claimed
(`--assignee @me`) so a half-wired map never shows a falsely-unblocked
frontier; release the claim (`--remove-assignee @me`) only after the
blocking edges are wired.

```bash
url=$(gh issue create --repo "$R" --title "<ticket name>" \
  --label "wayfinder:$TYPE" --assignee @me --body-file ticket.md)
n=${url##*/}
id=$(gh api repos/$R/issues/$n --jq .id)
gh api -X POST repos/$R/issues/$MAP/sub_issues -F sub_issue_id=$id
```

## Wire a blocking edge (second pass)

Ticket `$N` waits on blocker `$B`:

```bash
bid=$(gh api repos/$R/issues/$B --jq .id)
gh api -X POST repos/$R/issues/$N/dependencies/blocked_by -F issue_id=$bid
```

## Query the frontier

Open, unassigned sub-issues with no open blocker:

```bash
gh api --paginate repos/$R/issues/$MAP/sub_issues \
  --jq '.[] | select(.state=="open" and (.assignees|length)==0) | .number' |
while read -r n; do
  open=$(gh api --paginate --slurp repos/$R/issues/$n/dependencies/blocked_by \
    --jq '[.[][] | select(.state=="open")] | length')
  [ "$open" -eq 0 ] && echo "$n"
done
```

`--slurp` matters: plain `--paginate` applies `--jq` to each page
separately, so a ticket with more than one page of blockers would
yield several counts (`0`, `0`, …) and break the integer comparison.

## Claim, resolve, close

Assigning is not atomic — `--add-assignee` adds to a list, and two
sessions racing on the same frontier can both succeed. Claim, then
re-fetch: proceed only as the sole assignee, otherwise withdraw and
take the next frontier ticket.

```bash
gh issue edit "$N" --repo "$R" --add-assignee @me   # claim — before any work
me=$(gh api user --jq .login)
claimants=$(gh api repos/$R/issues/$N --jq '[.assignees[].login] | join(",")')
if [ "$claimants" != "$me" ]; then
  gh issue edit "$N" --repo "$R" --remove-assignee @me   # lost the race
fi
```

```bash
gh issue comment "$N" --repo "$R" --body-file resolution.md
gh issue close "$N" --repo "$R"
```

Ordering is the skill's contract, not the tracker's: the Decision Log
entry lands in the repository first, the resolution comment quotes it
and links the landing commit or pull request, and the close comes last.
