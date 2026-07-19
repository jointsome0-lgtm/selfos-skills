#!/usr/bin/env bats
# Tests for codex-pr-watch.sh — verdict-cutoff anchoring (issue #34), review
# head matching, and terminal states. `gh` is a stub serving per-test JSON
# fixtures; `jq` and `date` are real. Timeout tests use --interval 1
# --timeout 2, so each costs ~2 s of wall clock.

setup() {
  WATCH="$BATS_TEST_DIRNAME/codex-pr-watch.sh"
  SHA="1234567890abcdef1234567890abcdef12345678"
  export GH_FIXTURES="$BATS_TEST_TMPDIR/fixtures"
  mkdir -p "$GH_FIXTURES" "$BATS_TEST_TMPDIR/bin"

  # stub gh: dispatch on the API path, serve the matching fixture; a missing
  # fixture file fails the call, which the watcher treats as a soft error
  cat >"$BATS_TEST_TMPDIR/bin/gh" <<'STUB'
#!/usr/bin/env bash
path=""
for a in "$@"; do case "$a" in repos/*) path="$a" ;; esac; done
case "$path" in
  */pulls/*/reviews*)    cat "$GH_FIXTURES/reviews.json" ;;
  */pulls/*/comments*)   cat "$GH_FIXTURES/comments.json" ;;
  */issues/*/reactions*)
    # reactions.json.2, when present, is served from the second call on —
    # lets a test change the PR state between polls (e.g. a post-trigger 👍)
    if [[ -f "$GH_FIXTURES/reactions.json.2" && -f "$GH_FIXTURES/.reactions_served" ]]; then
      cat "$GH_FIXTURES/reactions.json.2"
    else
      : >"$GH_FIXTURES/.reactions_served"
      cat "$GH_FIXTURES/reactions.json"
    fi ;;
  */issues/*/comments*)  cat "$GH_FIXTURES/trigger.json" ;;
  */events*)             cat "$GH_FIXTURES/events.json" ;;
  */commits/*)           cat "$GH_FIXTURES/commit.json" ;;
  */pulls/*)             cat "$GH_FIXTURES/pr.json" ;;
  *) echo "stub gh: unmatched call: $*" >&2; exit 1 ;;
esac
STUB
  chmod +x "$BATS_TEST_TMPDIR/bin/gh"
  PATH="$BATS_TEST_TMPDIR/bin:$PATH"

  printf '{"head":{"ref":"feat","sha":"%s"},"state":"open","merged":false}' "$SHA" >"$GH_FIXTURES/pr.json"
  echo '[]' >"$GH_FIXTURES/events.json"
  echo '[]' >"$GH_FIXTURES/reviews.json"
  echo '[]' >"$GH_FIXTURES/reactions.json"
}

iso() { date -u -d "$1 seconds ago" +%Y-%m-%dT%H:%M:%SZ; }

push_event() { # seconds-ago [ref] — PushEvent that made $SHA the head of ref
  printf '[{"type":"PushEvent","created_at":"%s","payload":{"ref":"refs/heads/%s","head":"%s"}}]' \
    "$(iso "$1")" "${2:-feat}" "$SHA" >"$GH_FIXTURES/events.json"
}

thumb() { # seconds-ago — bot 👍 on the PR body
  printf '[{"user":{"login":"chatgpt-codex-connector[bot]"},"content":"+1","created_at":"%s"}]' \
    "$(iso "$1")" >"$GH_FIXTURES/reactions.json"
}

review() { # seconds-ago commit-id — bot review tied to a commit
  printf '[{"id":42,"user":{"login":"chatgpt-codex-connector[bot]"},"commit_id":"%s","submitted_at":"%s","state":"COMMENTED","html_url":"https://x/r/42","body":"Found a bug."}]' \
    "$2" "$(iso "$1")" >"$GH_FIXTURES/reviews.json"
}

run_watch() { run "$WATCH" --repo o/r --pr 7 --sha "$SHA" --interval 1 --timeout 2 "$@"; }

@test "fresh 👍 after the push-event cutoff → APPROVED" {
  push_event 120
  thumb 60
  run_watch
  [ "$status" -eq 0 ]
  [[ "$output" == *"VERDICT: APPROVED"* ]]
}

@test "issue #34: a watcher starting long after the 👍 still accepts it (cutoff anchors to the push, not start − 90 s)" {
  push_event 1800
  thumb 1200
  run_watch
  [ "$status" -eq 0 ]
  [[ "$output" == *"VERDICT: APPROVED"* ]]
}

@test "👍 predating the round's push is a previous round's — ignored, with a note" {
  push_event 120
  thumb 300
  run_watch
  [ "$status" -eq 3 ]
  [[ "$output" == *"VERDICT: TIMEOUT"* ]]
  [[ "$output" == *"from before the cutoff"* ]]
}

@test "👍 while 👀 is still up is a leftover, not a verdict" {
  push_event 120
  printf '[{"user":{"login":"chatgpt-codex-connector[bot]"},"content":"eyes","created_at":"%s"},{"user":{"login":"chatgpt-codex-connector[bot]"},"content":"+1","created_at":"%s"}]' \
    "$(iso 60)" "$(iso 30)" >"$GH_FIXTURES/reactions.json"
  run_watch
  [ "$status" -eq 3 ]
  [[ "$output" == *"review in progress"* ]]
}

@test "fresh same-head review → FINDINGS with body and inline comments" {
  push_event 120
  review 60 "$SHA"
  printf '[{"pull_request_review_id":42,"path":"foo.sh","line":3,"body":"off-by-one","html_url":"https://x/c/1"}]' \
    >"$GH_FIXTURES/comments.json"
  run_watch
  [ "$status" -eq 2 ]
  [[ "$output" == *"VERDICT: FINDINGS"* ]]
  [[ "$output" == *"matches the expected head"* ]]
  [[ "$output" == *"Found a bug."* ]]
  [[ "$output" == *"foo.sh:3"* ]]
  [[ "$output" == *"off-by-one"* ]]
}

@test "issue #34: a same-head review from before the round's push is not re-accepted" {
  push_event 120
  review 300 "$SHA"
  run_watch
  [ "$status" -eq 3 ]
}

@test "a previous head's review stays ignored while the new round is visibly running" {
  push_event 120
  review 60 "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
  printf '[{"user":{"login":"chatgpt-codex-connector[bot]"},"content":"eyes","created_at":"%s"}]' \
    "$(iso 30)" >"$GH_FIXTURES/reactions.json"
  run_watch
  [ "$status" -eq 3 ]
}

@test "a fresh stale-head review with no round running is surfaced once the startup grace expires" {
  push_event 120
  review 60 "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
  echo '[]' >"$GH_FIXTURES/comments.json"
  export CODEX_PR_WATCH_GAP_GRACE=2
  run "$WATCH" --repo o/r --pr 7 --sha "$SHA" --interval 1 --timeout 8
  [ "$status" -eq 2 ]
  [[ "$output" == *"VERDICT: FINDINGS"* ]]
  [[ "$output" == *"WARNING: reviewed commit"* ]]
  [[ "$output" == *"Found a bug."* ]]
}

@test "issue #50: the startup guard is wall-clock — at --interval 1 a fresh stale-head review stays silent through GAP_GRACE" {
  push_event 120
  review 60 "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
  echo '[]' >"$GH_FIXTURES/comments.json"
  run "$WATCH" --repo o/r --pr 7 --sha "$SHA" --interval 1 --timeout 5
  [ "$status" -eq 3 ]
  [[ "$output" == *"VERDICT: TIMEOUT"* ]]
}

@test "commit-date fallback: a fresh other-head review is not surfaced (no round boundary)" {
  printf '{"commit":{"committer":{"date":"%s"}}}' "$(iso 600)" >"$GH_FIXTURES/commit.json"
  review 60 "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
  run "$WATCH" --repo o/r --pr 7 --sha "$SHA" --interval 1 --timeout 5
  [ "$status" -eq 3 ]
  [[ "$output" == *"no push event found"* ]]
}

@test "👀-removed verdict gap: an other-head review is not surfaced before the grace expires" {
  push_event 120
  review 60 "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
  printf '[{"user":{"login":"chatgpt-codex-connector[bot]"},"content":"eyes","created_at":"%s"}]' \
    "$(iso 30)" >"$GH_FIXTURES/reactions.json"
  ( sleep 3; echo '[]' >"$GH_FIXTURES/reactions.json" ) &
  run "$WATCH" --repo o/r --pr 7 --sha "$SHA" --interval 1 --timeout 7
  [ "$status" -eq 3 ]
  [[ "$output" == *"verdict imminent"* ]]
}

@test "a round observed reviewing the pre-push head: its review is surfaced once the grace expires" {
  push_event 120
  review 60 "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
  echo '[]' >"$GH_FIXTURES/comments.json"
  printf '[{"user":{"login":"chatgpt-codex-connector[bot]"},"content":"eyes","created_at":"%s"}]' \
    "$(iso 30)" >"$GH_FIXTURES/reactions.json"
  ( sleep 2; echo '[]' >"$GH_FIXTURES/reactions.json" ) &
  export CODEX_PR_WATCH_GAP_GRACE=3
  run "$WATCH" --repo o/r --pr 7 --sha "$SHA" --interval 1 --timeout 30
  [ "$status" -eq 2 ]
  [[ "$output" == *"WARNING: reviewed commit"* ]]
}

@test "no push event: reactions keep the conservative start − 90 s cutoff" {
  printf '{"commit":{"committer":{"date":"%s"}}}' "$(iso 600)" >"$GH_FIXTURES/commit.json"
  thumb 300
  run_watch
  [ "$status" -eq 3 ]
  [[ "$output" == *"no push event found"* ]]
}

@test "no push event: a 👍 within the last 90 s is still accepted" {
  printf '{"commit":{"committer":{"date":"%s"}}}' "$(iso 600)" >"$GH_FIXTURES/commit.json"
  thumb 30
  run_watch
  [ "$status" -eq 0 ]
  [[ "$output" == *"VERDICT: APPROVED"* ]]
}

@test "a PushEvent for the same SHA on another ref does not anchor the round" {
  push_event 400 other
  printf '{"commit":{"committer":{"date":"%s"}}}' "$(iso 600)" >"$GH_FIXTURES/commit.json"
  thumb 300
  run_watch
  [ "$status" -eq 3 ]
  [[ "$output" == *"no push event found"* ]]
}

@test "events pagination: the anchoring push can sit on a later page" {
  { printf '[{"type":"WatchEvent","created_at":"%s"}]' "$(iso 60)"
    push_event_page=$(printf '[{"type":"PushEvent","created_at":"%s","payload":{"ref":"refs/heads/feat","head":"%s"}}]' "$(iso 120)" "$SHA")
    printf '%s' "$push_event_page"
  } >"$GH_FIXTURES/events.json"
  thumb 60
  run_watch
  [ "$status" -eq 0 ]
  [[ "$output" == *"VERDICT: APPROVED"* ]]
}

@test "closed PR with no verdict → PR_NOT_OPEN" {
  printf '{"head":{"ref":"feat"},"state":"closed","merged":true}' >"$GH_FIXTURES/pr.json"
  run_watch
  [ "$status" -eq 4 ]
  [[ "$output" == *"VERDICT: PR_NOT_OPEN"* ]]
}

@test "--trigger post failure is no round boundary: a fresh other-head review is not surfaced" {
  push_event 600
  review -5 "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
  run "$WATCH" --repo o/r --pr 7 --sha "$SHA" --interval 1 --timeout 5 --trigger
  [ "$status" -eq 3 ]
  [[ "$output" == *"failed to post the trigger comment"* ]]
}

@test "a posted --trigger requests this head's own review: an other-head review is not surfaced" {
  push_event 600
  printf '{"created_at":"%s"}' "$(iso 0)" >"$GH_FIXTURES/trigger.json"
  review -5 "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
  run "$WATCH" --repo o/r --pr 7 --sha "$SHA" --interval 1 --timeout 5 --trigger
  [ "$status" -eq 3 ]
  [[ "$output" == *"posted '@codex review' trigger"* ]]
}

@test "--trigger: the cutoff anchors to the trigger comment, not the earlier push" {
  push_event 600
  thumb 300
  printf '{"created_at":"%s"}' "$(iso 0)" >"$GH_FIXTURES/trigger.json"
  run_watch --trigger
  [ "$status" -eq 3 ]
  [[ "$output" == *"posted '@codex review' trigger"* ]]
}

# --- issue #47: auto-trigger --------------------------------------------------

@test "issue #47: no bot activity after the push → the watcher posts '@codex review' itself and accepts the post-trigger 👍" {
  push_event 600
  printf '{"created_at":"%s"}' "$(iso 5)" >"$GH_FIXTURES/trigger.json"
  printf '[{"user":{"login":"chatgpt-codex-connector[bot]"},"content":"+1","created_at":"%s"}]' \
    "$(iso 2)" >"$GH_FIXTURES/reactions.json.2"
  run_watch --grace 0
  [ "$status" -eq 0 ]
  [[ "$output" == *"posted '@codex review' trigger comment"* ]]
  [[ "$output" == *"VERDICT: APPROVED"* ]]
}

@test "issue #47: the auto-trigger re-anchors the cutoffs — a 👍 predating the trigger comment is not accepted" {
  push_event 600
  thumb 900
  printf '{"created_at":"%s"}' "$(iso 5)" >"$GH_FIXTURES/trigger.json"
  run_watch --grace 0
  [ "$status" -eq 3 ]
  [[ "$output" == *"posted '@codex review' trigger comment"* ]]
  [[ "$output" == *"An '@codex review' trigger was posted"* ]]
}

@test "issue #47: --no-trigger keeps the watcher read-only" {
  push_event 600
  run_watch --no-trigger --grace 0
  [ "$status" -eq 3 ]
  [[ "$output" != *"posted '@codex review'"* ]]
  [[ "$output" == *"re-run with --trigger"* ]]
}

@test "issue #47: 👀 up means a review is in progress — no auto-trigger" {
  push_event 600
  printf '[{"user":{"login":"chatgpt-codex-connector[bot]"},"content":"eyes","created_at":"%s"}]' \
    "$(iso 60)" >"$GH_FIXTURES/reactions.json"
  run_watch --grace 0
  [ "$status" -eq 3 ]
  [[ "$output" == *"review in progress"* ]]
  [[ "$output" != *"posted '@codex review'"* ]]
}

@test "issue #47: no push event + a 👍 before the conservative cutoff → auto-trigger is skipped, not a silent re-review" {
  printf '{"commit":{"committer":{"date":"%s"}}}' "$(iso 600)" >"$GH_FIXTURES/commit.json"
  thumb 300
  run_watch --grace 0
  [ "$status" -eq 3 ]
  [[ "$output" == *"skipping auto-trigger"* ]]
  [[ "$output" != *"posted '@codex review'"* ]]
}

@test "issue #47: an explicit --since pins the round — no auto-trigger" {
  push_event 600
  run_watch --since "$(iso 60)" --grace 0
  [ "$status" -eq 3 ]
  [[ "$output" != *"posted '@codex review'"* ]]
}

@test "issue #47: within the grace period the watcher still just waits" {
  push_event 10
  printf '{"created_at":"%s"}' "$(iso 0)" >"$GH_FIXTURES/trigger.json"
  run_watch --grace 300
  [ "$status" -eq 3 ]
  [[ "$output" != *"posted '@codex review'"* ]]
}

@test "issue #47: a PR that is no longer open is reported before the auto-trigger posts anything" {
  push_event 600
  printf '{"head":{"ref":"feat"},"state":"closed","merged":false}' >"$GH_FIXTURES/pr.json"
  printf '{"created_at":"%s"}' "$(iso 0)" >"$GH_FIXTURES/trigger.json"
  run_watch --grace 0
  [ "$status" -eq 4 ]
  [[ "$output" == *"VERDICT: PR_NOT_OPEN"* ]]
  [[ "$output" != *"posted '@codex review'"* ]]
}

@test "issue #47: a newer push moved the PR head → auto-trigger skipped (this watcher is pinned to the old head)" {
  push_event 600
  printf '{"head":{"ref":"feat","sha":"ffffffffffffffffffffffffffffffffffffffff"},"state":"open","merged":false}' \
    >"$GH_FIXTURES/pr.json"
  printf '{"created_at":"%s"}' "$(iso 0)" >"$GH_FIXTURES/trigger.json"
  run_watch --grace 0
  [ "$status" -eq 3 ]
  [[ "$output" == *"the PR head moved"* ]]
  [[ "$output" != *"posted '@codex review'"* ]]
}

@test "issue #47: an unreadable PR head postpones the auto-trigger instead of posting blind" {
  push_event 600
  rm -f "$GH_FIXTURES/pr.json"   # every pulls/N read fails
  printf '{"created_at":"%s"}' "$(iso 0)" >"$GH_FIXTURES/trigger.json"
  run_watch --grace 0
  [ "$status" -eq 3 ]
  [[ "$output" == *"postponing the auto-trigger"* ]]
  [[ "$output" != *"posted '@codex review'"* ]]
}

@test "issue #47: unreadable reactions postpone the auto-trigger — an empty read is not proof the bot is idle" {
  push_event 600
  rm -f "$GH_FIXTURES/reactions.json"   # every reactions read fails
  printf '{"created_at":"%s"}' "$(iso 0)" >"$GH_FIXTURES/trigger.json"
  run_watch --grace 0
  [ "$status" -eq 3 ]
  [[ "$output" == *"postponing the auto-trigger"* ]]
  [[ "$output" != *"posted '@codex review'"* ]]
}

@test "issue #47: a posted auto-trigger is no step-2b boundary — an other-head review after the trigger is not surfaced" {
  push_event 600
  printf '{"created_at":"%s"}' "$(iso 5)" >"$GH_FIXTURES/trigger.json"
  review -5 "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
  export CODEX_PR_WATCH_GAP_GRACE=0
  run "$WATCH" --repo o/r --pr 7 --sha "$SHA" --interval 1 --timeout 5 --grace 0
  [ "$status" -eq 3 ]
  [[ "$output" == *"posted '@codex review' trigger comment"* ]]
  [[ "$output" != *"VERDICT: FINDINGS"* ]]
}

@test "issue #47: a pre-cutoff 👍 discovered after a failed first reactions read still suppresses the auto-trigger" {
  printf '{"commit":{"committer":{"date":"%s"}}}' "$(iso 600)" >"$GH_FIXTURES/commit.json"
  rm -f "$GH_FIXTURES/reactions.json"   # first reactions read fails…
  printf '[{"user":{"login":"chatgpt-codex-connector[bot]"},"content":"+1","created_at":"%s"}]' \
    "$(iso 300)" >"$GH_FIXTURES/reactions.json.2"   # …the second one sees the old 👍
  printf '{"created_at":"%s"}' "$(iso 0)" >"$GH_FIXTURES/trigger.json"
  run_watch --grace 0
  [ "$status" -eq 3 ]
  [[ "$output" == *"skipping auto-trigger"* ]]
  [[ "$output" != *"posted '@codex review'"* ]]
}

@test "issue #47: --trigger and --no-trigger together are rejected" {
  run_watch --trigger --no-trigger
  [ "$status" -eq 1 ]
  [[ "$output" == *"mutually exclusive"* ]]
}
