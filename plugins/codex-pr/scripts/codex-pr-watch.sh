#!/usr/bin/env bash
# codex-pr-watch.sh — after a push, wait for the Codex cloud review verdict on a PR.
#
# Protocol (verified against chatgpt-codex-connector[bot]):
#   push → bot reacts 👀 on the PR body → review runs → 👀 removed →
#   either 👍 reaction on the PR body (all clear)
#   or a PR review tied to the pushed commit (findings, mostly inline comments).
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
  --since ISO8601Z   count events after this instant
                     (default: reviews — script start; reactions — start − 90 s)
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
if [[ -n "$SINCE" ]]; then
  RSINCE="$SINCE"                 # explicit --since applies to reviews too
else
  RSINCE="$START_ISO"             # reviews: only ones submitted after start
  SINCE=$(date -u -d '90 seconds ago' +%Y-%m-%dT%H:%M:%SZ)  # reactions: push→start buffer
fi

log "watching $REPO#$PR — head ${SHA:0:10}, bot /$BOT/i, every ${INTERVAL}s, timeout ${TIMEOUT}s"

if [[ $TRIGGER -eq 1 ]]; then
  if gh pr comment "$PR" -R "$REPO" --body "@codex review" >/dev/null 2>&1; then
    log "posted '@codex review' trigger comment"
  else
    log "WARNING: failed to post the trigger comment"
  fi
fi

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
poll=0

while :; do
  poll=$((poll + 1))

  # 1) a review from the bot for this push?
  reviews=$(fetch "repos/$REPO/pulls/$PR/reviews?per_page=100")
  review=$(jq -c --arg bot "$BOT" --arg sha "$SHA" --arg since "$RSINCE" '
      [.[] | select((.user.login | test($bot; "i"))
                    and ((.commit_id == $sha) or (.submitted_at > $since)))]
      | sort_by(.submitted_at) | last // empty' <<<"$reviews" 2>/dev/null) || review=""
  if [[ -n "$review" ]]; then
    report_review "$review"
    exit 2
  fi

  # 2) a fresh 👍 on the PR body?
  reacts=$(fetch "repos/$REPO/issues/$PR/reactions?per_page=100")
  thumb=$(jq -r --arg bot "$BOT" --arg since "$SINCE" '
      [.[] | select((.user.login | test($bot; "i")) and .content == "+1" and .created_at > $since)]
      | last | if . == null then "" else "\(.user.login) at \(.created_at)" end' <<<"$reacts" 2>/dev/null) || thumb=""
  if [[ -n "$thumb" ]]; then
    echo "VERDICT: APPROVED"
    echo "👍 reaction on the PR body from $thumb"
    exit 0
  fi

  if [[ $poll -eq 1 ]]; then
    stale=$(jq -r --arg bot "$BOT" --arg since "$SINCE" '
        [.[] | select((.user.login | test($bot; "i")) and .content == "+1" and .created_at <= $since)]
        | last | if . == null then "" else .created_at end' <<<"$reacts" 2>/dev/null) || stale=""
    [[ -n "$stale" ]] && log "note: stale 👍 from before this push ($stale) — ignored"
  fi

  eyes=$(jq -r --arg bot "$BOT" '
      [.[] | select((.user.login | test($bot; "i")) and .content == "eyes")] | length' <<<"$reacts" 2>/dev/null) || eyes=0
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
