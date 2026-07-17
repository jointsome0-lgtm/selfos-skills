#!/usr/bin/env bash
# codex-pr-watch.sh — after a push, wait for the Codex cloud review verdict on a PR.
#
# Protocol (verified against chatgpt-codex-connector[bot]):
#   push → bot reacts 👀 on the PR body → review runs → 👀 removed →
#   either 👍 reaction on the PR body (all clear)
#   or a PR review tied to the pushed commit (findings, mostly inline comments).
#
# "Fresh" is anchored to the round, not to watcher start: by default events
# count from the push of the expected head (PushEvent, or the head-changing
# PullRequestEvent); with --trigger, from script start — the trigger opens a
# new round on the same head; an explicit --since overrides both. Reviews
# must also match the expected head (.commit_id), so a previous head's
# review still finishing after the push cannot deliver stale findings, and a
# previous round's same-head review is not re-accepted — except that a
# fresh review for a different head is surfaced (with a head warning) when
# the cutoff sits on a boundary that applies to other heads (push/PR event
# or explicit --since — never a --trigger, which requests this head's own
# review, nor the fallback cutoffs) and no 👀 round is running: immediately
# if none was observed,
# else only after a short verdict-gap grace so a finishing round's own
# same-head verdict wins the race. A push racing the bot leaves the verdict
# on the older head, and only that verdict will ever arrive. When no push
# event is found, reviews anchor to the head commit's committer date (safe:
# they are commit-tied) while reactions fall back to the conservative
# start − 90 s cutoff (a 👍 is not commit-tied, and one created between an
# old commit's date and its late push could belong to a previous round);
# those fallback cutoffs are no round boundary, so the different-head
# surfacing stays disabled on them. A 👍 is additionally ignored while 👀
# is up: a verdict 👍 only appears after 👀 is removed.
#
# Exit codes:
#   0  APPROVED    — fresh 👍 reaction from the review bot
#   2  FINDINGS    — bot posted a review; body + inline comments on stdout
#   3  TIMEOUT     — no verdict within --timeout
#   4  PR_NOT_OPEN — PR merged/closed and no fresh verdict
#   1  usage / resolution error

set -uo pipefail

REPO="" PR="" SHA="" SINCE="" BOT="codex"
INTERVAL=30 TIMEOUT=1500 TRIGGER=0 REPO_FLAG=0
# seconds after the last observed 👀 before step 2b may surface a
# different-head review: an imminent same-head verdict must win that gap.
# Env-tunable so tests need not wait a real minute.
GAP_GRACE="${CODEX_PR_WATCH_GAP_GRACE:-60}"

usage() {
  cat <<'EOF'
Usage: codex-pr-watch.sh [options]

Waits until the Codex review bot delivers a verdict on a pull request:
a fresh 👍 reaction on the PR body (exit 0) or a posted review (exit 2,
review body + inline comments printed to stdout).

Options:
  --pr N             PR number         (default: the current branch's PR)
  --repo OWNER/NAME  repository        (default: the current directory's repo)
  --sha SHA          expected head     (default: local git HEAD, else PR head)
  --since ISO8601Z   count events (reviews and reactions) after this instant
                     (default: the push of the expected head; if no push event
                      is found, reviews — its committer date − 60 s, reactions —
                      start − 90 s; with --trigger: script start)
  --bot REGEX        reviewer login regex, case-insensitive (default: codex)
  --interval SEC     poll interval     (default: 30)
  --timeout SEC      give up after     (default: 1500)
  --trigger          post an "@codex review" comment before waiting
  -h, --help         this help

Exit codes: 0 approved · 2 findings · 3 timeout · 4 PR not open · 1 error
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pr)       PR="$2"; shift 2 ;;
    --repo)     REPO="$2"; REPO_FLAG=1; shift 2 ;;
    --sha)      SHA="$2"; shift 2 ;;
    --since)    SINCE="$2"; shift 2 ;;
    --bot)      BOT="$2"; shift 2 ;;
    --interval) INTERVAL="$2"; shift 2 ;;
    --timeout)  TIMEOUT="$2"; shift 2 ;;
    --trigger)  TRIGGER=1; shift ;;
    -h|--help)  usage; exit 0 ;;
    *) echo "unknown option: $1" >&2; usage >&2; exit 1 ;;
  esac
done

log() { printf '[%s] %s\n' "$(date -u +%H:%M:%SZ)" "$*" >&2; }

# api PATH…  → raw gh api call, non-fatal
api() { gh api "$@" 2>/dev/null; }

# fetch PATH → all pages concatenated into one JSON array ("[]" on failure)
fetch() { gh api --paginate "$1" 2>/dev/null | jq -s 'add // []' 2>/dev/null || echo '[]'; }

# --- resolve repo / PR / head SHA -------------------------------------------
if [[ -z "$REPO" ]]; then
  REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null) || true
fi
[[ -n "$REPO" ]] || { echo "cannot resolve repository; pass --repo OWNER/NAME" >&2; exit 1; }

if [[ -z "$PR" ]]; then
  PR=$(gh pr view --json number -q .number 2>/dev/null) || true
fi
[[ -n "$PR" ]] || { echo "no PR for the current branch; pass --pr N" >&2; exit 1; }

if [[ -z "$SHA" && $REPO_FLAG -eq 0 ]]; then
  # the freshest truth about what was just pushed is the local HEAD
  SHA=$(git rev-parse HEAD 2>/dev/null) || true
fi
if [[ -z "$SHA" ]]; then
  SHA=$(gh pr view "$PR" -R "$REPO" --json headRefOid -q .headRefOid 2>/dev/null) || true
fi
[[ -n "$SHA" ]] || { echo "cannot resolve the expected head SHA; pass --sha" >&2; exit 1; }

START_ISO=$(date -u +%Y-%m-%dT%H:%M:%SZ)
start_epoch=$(date +%s)

# post the trigger before computing cutoffs, so the requested round provably
# starts after them — a previous round's same-head review landing between
# script start and the comment post must not satisfy the new round's cutoff
TRIGGER_ISO=""
if [[ $TRIGGER -eq 1 ]]; then
  TRIGGER_ISO=$(api -X POST "repos/$REPO/issues/$PR/comments" -f body="@codex review" \
                  | jq -r '.created_at // empty' 2>/dev/null) || TRIGGER_ISO=""
  if [[ -n "$TRIGGER_ISO" ]]; then
    log "posted '@codex review' trigger comment at $TRIGGER_ISO"
  else
    log "WARNING: failed to post the trigger comment"
  fi
fi

# ROUND_BOUNDARY: the cutoff marks a boundary that applies to OTHER heads —
# an explicit --since or the push/PR event that made $SHA the head. The
# commit-date and start-anchored fallbacks below are sound for commit-tied
# same-head reviews only; a different-head review has no tie to this head's
# commit date, so poll-loop step 2b stays disabled without a real boundary.
ROUND_BOUNDARY=0

if [[ -n "$SINCE" ]]; then
  RSINCE="$SINCE"                 # explicit --since applies to both paths
  ROUND_BOUNDARY=1
elif [[ $TRIGGER -eq 1 ]]; then
  # a re-review round on the same head: the verdict follows the trigger
  # comment; anchor to its server-side timestamp (script start if the post
  # failed and the round may not have been requested at all). Deliberately
  # NOT a step-2b boundary in either case: a posted trigger requests a
  # review of $SHA itself, so the same-head verdict is pending by
  # construction and a previous round's different-head review draining in
  # after the trigger must not preempt it; a failed post requested nothing.
  SINCE="${TRIGGER_ISO:-$START_ISO}"; RSINCE="$SINCE"
else
  # anchor to the round boundary: the event that made the expected head the
  # PR head — a PushEvent (later pushes) or a PullRequestEvent (opened /
  # synchronize; the first push of a new branch emits no PushEvent). The
  # commit date alone is not enough — an old local commit pushed late would
  # set the cutoff before a previous round's 👍 and let it pass as fresh.
  # only head-changing PR actions count: a later labeled/edited event carries
  # the same head.sha but postdates the round and could mask its verdict;
  # likewise a PushEvent only counts on the PR's own head ref — the same SHA
  # pushed to another branch later must not advance the cutoff
  headref=$(api "repos/$REPO/pulls/$PR" | jq -r '.head.ref // empty' 2>/dev/null) || headref=""
  # fetch paginates: in a busy repository the anchoring event can sit past
  # the first page of the events feed (up to 300 events are retained)
  push_iso=$(fetch "repos/$REPO/events?per_page=100" | jq -r --arg sha "$SHA" --arg pr "$PR" --arg ref "$headref" '
      [.[] | select((.type == "PushEvent" and $ref != ""
                     and .payload.ref == ("refs/heads/" + $ref)
                     and .payload.head == $sha)
                    or (.type == "PullRequestEvent"
                        and (.payload.action == "opened" or .payload.action == "synchronize")
                        and ((.payload.pull_request.number | tostring) == $pr)
                        and .payload.pull_request.head.sha == $sha))]
      | sort_by(.created_at) | last | .created_at // empty' 2>/dev/null) || push_iso=""
  if [[ -n "$push_iso" ]]; then
    SINCE="$push_iso"; RSINCE="$push_iso"
    ROUND_BOUNDARY=1
  else
    # no push event (feed lag or retention). Reviews can still anchor to the
    # head commit's committer date (− 60 s clock skew): a review must match
    # .commit_id, and a review of this head cannot predate the head itself.
    # Reactions are not commit-tied — a 👍 created between an old commit's
    # date and its late push could be a previous round's — so they keep the
    # conservative start − 90 s cutoff here.
    commit_iso=$(api "repos/$REPO/commits/$SHA" | jq -r '.commit.committer.date // empty' 2>/dev/null) || commit_iso=""
    commit_epoch=""
    if [[ -n "$commit_iso" ]]; then
      commit_epoch=$(date -d "$commit_iso" +%s 2>/dev/null) || commit_epoch=""
    fi
    if [[ -n "$commit_epoch" ]]; then
      RSINCE=$(date -u -d "@$(( commit_epoch - 60 ))" +%Y-%m-%dT%H:%M:%SZ)
      log "note: no push event found for ${SHA:0:10} — reviews anchored to its commit date ($RSINCE), reactions to start − 90 s"
    else
      RSINCE="$START_ISO"
      log "WARNING: cannot resolve a push event or commit date for ${SHA:0:10} — falling back to start-anchored cutoffs"
    fi
    SINCE=$(date -u -d '90 seconds ago' +%Y-%m-%dT%H:%M:%SZ)
  fi
fi

log "watching $REPO#$PR — head ${SHA:0:10}, bot /$BOT/i, every ${INTERVAL}s, timeout ${TIMEOUT}s"

# --- findings report ---------------------------------------------------------
report_review() {
  local review="$1" rid rsha rurl rstate rbody inline n
  rid=$(jq -r .id <<<"$review")
  rsha=$(jq -r .commit_id <<<"$review")
  rurl=$(jq -r .html_url <<<"$review")
  rstate=$(jq -r .state <<<"$review")
  rbody=$(jq -r '.body // ""' <<<"$review")

  inline=$(fetch "repos/$REPO/pulls/$PR/comments?per_page=100" \
             | jq -c --argjson rid "$rid" '[.[] | select(.pull_request_review_id == $rid)]')
  [[ -n "$inline" ]] || inline='[]'
  n=$(jq length <<<"$inline")

  echo "VERDICT: FINDINGS"
  echo "Review: $rurl (state $rstate)"
  if [[ "$rsha" == "$SHA" ]]; then
    echo "Reviewed commit: $rsha (matches the expected head)"
  else
    echo "WARNING: reviewed commit $rsha, expected head $SHA — an older/newer push?"
  fi
  echo "Inline comments: $n"
  echo
  echo "--- review body ---"
  sed '/^<details>/,/^<\/details>/d' <<<"$rbody"   # drop the static "About Codex" blurb
  echo
  if (( n > 0 )); then
    jq -r '.[] | "--- \(.path):\(.line // .original_line // "?") ---\n\(.body)\n(\(.html_url))\n"' <<<"$inline"
  else
    echo "(no inline comments — read the body above; it may even be an all-clear note)"
  fi
  echo "Next: fix (or explicitly rebut) each item, commit, push, re-run this watcher."
}

# --- poll loop ----------------------------------------------------------------
deadline=$(( start_epoch + TIMEOUT ))
eyes_seen=0
eyes_up_epoch=0   # last instant 👀 was seen up; step 2b's grace counts from it
poll=0

while :; do
  poll=$((poll + 1))

  # 1) a review from the bot for this push?
  reviews=$(fetch "repos/$REPO/pulls/$PR/reviews?per_page=100")
  # both conditions are mandatory: freshness — a same-head review from a
  # previous round must not be re-accepted just because .commit_id still
  # matches (issue #34) — and the expected head — a previous head's review
  # still finishing after the push must not deliver stale findings
  review=$(jq -c --arg bot "$BOT" --arg sha "$SHA" --arg since "$RSINCE" '
      [.[] | select((.user.login | test($bot; "i"))
                    and (.commit_id == $sha) and (.submitted_at > $since))]
      | sort_by(.submitted_at) | last // empty' <<<"$reviews" 2>/dev/null) || review=""
  if [[ -n "$review" ]]; then
    report_review "$review"
    exit 2
  fi

  # 2) a fresh 👍 on the PR body?
  reacts=$(fetch "repos/$REPO/issues/$PR/reactions?per_page=100")
  eyes=$(jq -r --arg bot "$BOT" '
      [.[] | select((.user.login | test($bot; "i")) and .content == "eyes")] | length' <<<"$reacts" 2>/dev/null) || eyes=0
  # a visible 👀 continuously restarts step 2b's verdict-gap grace
  [[ "$eyes" -gt 0 ]] && eyes_up_epoch=$(date +%s)
  thumb=$(jq -r --arg bot "$BOT" --arg since "$SINCE" '
      [.[] | select((.user.login | test($bot; "i")) and .content == "+1" and .created_at > $since)]
      | last | if . == null then "" else "\(.user.login) at \(.created_at)" end' <<<"$reacts" 2>/dev/null) || thumb=""
  # a verdict 👍 appears only after 👀 is removed; while 👀 is up the round's
  # review is still running and any visible 👍 is a previous round's leftover
  if [[ -n "$thumb" && "$eyes" -eq 0 ]]; then
    echo "VERDICT: APPROVED"
    echo "👍 reaction on the PR body from $thumb"
    exit 0
  fi

  # 2b) a fresh bot review for a DIFFERENT head of this PR, with no round in
  #     progress? A push can race the bot before its round starts (e.g. a
  #     bookkeeping commit moments after opening the PR): the bot then
  #     reviews the older head and never opens a round for the expected one.
  #     When no 👀 is up after two full intervals' grace (time for a real
  #     new round to raise 👀), that post-cutoff stale-head review is this
  #     round's only verdict — surface it through report_review, whose head
  #     warning tells the operator the findings target an older commit,
  #     instead of sitting silent until timeout while the PR page shows a
  #     delivered review. Two guards keep a previous round's review out:
  #     ROUND_BOUNDARY — the commit-date/start fallback cutoffs are not
  #     boundaries that apply to other heads, and an old head's review can
  #     legitimately postdate them — and GAP_GRACE seconds of silence after
  #     the last observed 👀: in the 👀-removed→verdict gap the finishing
  #     round's own verdict is imminent and must win (it may be the expected
  #     head's 👍 or review); only when nothing lands within the grace was
  #     the observed round itself reviewing another head (e.g. one already
  #     running for the pre-push head when this watcher started).
  if [[ $poll -ge 3 && "$eyes" -eq 0 && $ROUND_BOUNDARY -eq 1 ]] \
     && (( $(date +%s) - eyes_up_epoch >= GAP_GRACE )); then
    other=$(jq -c --arg bot "$BOT" --arg sha "$SHA" --arg since "$RSINCE" '
        [.[] | select((.user.login | test($bot; "i"))
                      and (.commit_id != $sha) and (.submitted_at > $since))]
        | sort_by(.submitted_at) | last // empty' <<<"$reviews" 2>/dev/null) || other=""
    if [[ -n "$other" ]]; then
      report_review "$other"
      exit 2
    fi
  fi

  if [[ $poll -eq 1 ]]; then
    stale=$(jq -r --arg bot "$BOT" --arg since "$SINCE" '
        [.[] | select((.user.login | test($bot; "i")) and .content == "+1" and .created_at <= $since)]
        | last | if . == null then "" else .created_at end' <<<"$reacts" 2>/dev/null) || stale=""
    [[ -n "$stale" ]] && log "note: 👍 from before the cutoff ($stale) — ignored; if it is this head's verdict (late start, no push event found), verify manually or re-run with --since set to the push instant"
  fi

  if [[ "$eyes" -gt 0 && $eyes_seen -eq 0 ]]; then
    eyes_seen=1
    log "👀 — review in progress"
  elif [[ "$eyes" -eq 0 && $eyes_seen -eq 1 ]]; then
    eyes_seen=2
    INTERVAL=10
    log "👀 removed — verdict imminent, polling every ${INTERVAL}s"
  fi

  # 3) PR still open? (checked after verdicts so a just-merged PR still reports one)
  prjson=$(api "repos/$REPO/pulls/$PR") || prjson=""
  if [[ -n "$prjson" ]]; then
    state=$(jq -r .state <<<"$prjson")
    merged=$(jq -r .merged <<<"$prjson")
    if [[ "$state" != "open" ]]; then
      echo "VERDICT: PR_NOT_OPEN"
      if [[ "$merged" == "true" ]]; then
        echo "PR $REPO#$PR was merged — nothing to watch."
      else
        echo "PR $REPO#$PR is closed — nothing to watch."
      fi
      exit 4
    fi
  fi

  now=$(date +%s)
  if (( now >= deadline )); then
    echo "VERDICT: TIMEOUT"
    echo "No Codex verdict on $REPO#$PR within ${TIMEOUT}s (expected head $SHA)."
    echo "If reviews are not auto-triggered by pushes in this repo, re-run with --trigger."
    exit 3
  fi
  (( poll % 4 == 1 )) && log "waiting… ($(( now - start_epoch ))s elapsed)"
  sleep "$INTERVAL"
done
