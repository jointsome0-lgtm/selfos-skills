#!/usr/bin/env bash
# check_plugin_install.sh — exercise the marketplace end-to-end with a real
# Claude Code CLI: validate the manifest, add this checkout as a marketplace,
# install every plugin into a clean CLAUDE_CONFIG_DIR, and assert that
# installing sdd pulls in decision via its declared dependency.
#
# CLAUDE_CONFIG_DIR defaults to a fresh temp dir so a local run never touches
# the caller's real ~/.claude; CI can leave the default in place.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export CLAUDE_CONFIG_DIR="${CLAUDE_CONFIG_DIR:-$(mktemp -d)}"

claude plugin validate "$ROOT"
claude plugin marketplace add "$ROOT"

# dependency resolution: installing sdd alone must pull in decision. The
# legacy packages vanish with the dated plugins/ removal (#66); once only the
# aggregate marketplace entry remains there is no dependency edge to exercise.
if jq -e '.plugins | any(.name == "sdd")' "$ROOT/.claude-plugin/marketplace.json" >/dev/null; then
  claude plugin install sdd@selfos
  if ! claude plugin list | grep -q "decision@selfos"; then
    echo "FAIL: installing sdd@selfos did not pull in decision@selfos" >&2
    exit 1
  fi
fi

# every plugin in the marketplace installs cleanly (install is idempotent,
# so plugins already present as dependencies are fine to re-request)
while IFS= read -r plugin; do
  claude plugin install "$plugin@selfos"
done < <(jq -r '.plugins[].name' "$ROOT/.claude-plugin/marketplace.json")

claude plugin list
echo "OK: all marketplace plugins installed; dependency resolution verified"
