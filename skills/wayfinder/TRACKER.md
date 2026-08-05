# Wayfinding operations — GitHub

How the skill's tracker conventions map onto GitHub, with verified
commands. `$R` is `owner/repo`. `$N`-style variables hold issue
numbers; the sub-issue and dependency endpoints take the numeric
database **id** instead (`gh api repos/$R/issues/$N --jq .id`) — never
pass an issue number where an id is required. Map and tickets live in
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
(generally available on github.com; verify on GHES). Probe read-only
and stop with a clear message on an error rather than falling back to
another store:

```bash
gh api repos/$R/issues/$MAP/sub_issues --jq length
```

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
path segment.

```bash
url=$(gh issue create --repo "$R" --title "<ticket name>" \
  --label wayfinder:grilling --body-file ticket.md)
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
  open=$(gh api --paginate repos/$R/issues/$n/dependencies/blocked_by \
    --jq '[.[] | select(.state=="open")] | length')
  [ "$open" -eq 0 ] && echo "$n"
done
```

## Claim, resolve, close

```bash
gh issue edit "$N" --repo "$R" --add-assignee @me   # claim — before any work
gh issue comment "$N" --repo "$R" --body-file resolution.md
gh issue close "$N" --repo "$R"
```

Ordering is the skill's contract, not the tracker's: the Decision Log
entry lands in the repository first, the resolution comment quotes it
and links the landing commit or pull request, and the close comes last.
