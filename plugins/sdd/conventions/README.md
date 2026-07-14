# Shared SDD conventions — distribution model

`SDD-CONVENTIONS.md` is the canonical, versioned template of the structural
rules every SDD-stage repository shares. Consuming repositories do **not**
link to it at runtime — a bare link to `selfos-skills` would make a fresh
checkout depend on another repository (or on network access) for its own
correctness rules. Instead, each repository embeds a generated copy and can
validate it offline.

## How a repository adopts the conventions

1. Vendor the tool: copy `../scripts/sync_conventions.py` into the
   repository (for example as `scripts/check_sdd_conventions.py`). It is a
   single stdlib-only file with no imports from this repository.
2. Generate the fragment into the file that should carry the rules —
   typically `AGENTS.md` or `SDD.md`, after the repository-specific
   preamble:

   ```
   python3 scripts/check_sdd_conventions.py sync AGENTS.md \
       --template /path/to/selfos-skills/plugins/sdd/conventions/SDD-CONVENTIONS.md
   ```

3. Commit both. Add the offline check to local CI:

   ```
   python3 scripts/check_sdd_conventions.py check AGENTS.md
   ```

The fragment lives between two markers and records the template version plus
a sha256 of the block body:

```
<!-- BEGIN SDD-CONVENTIONS v1.0.0 sha256:<64-hex digest> -->
…template body…
<!-- END SDD-CONVENTIONS -->
```

`sync` touches nothing outside the markers, so the repository-specific
preamble and any local rules before or after the block survive regeneration.

## What `check` verifies

- **Always (offline, no plugin, no network):** the markers are well formed
  and unique, and the recorded sha256 matches the block body — hand edits
  inside the markers are detected on a fresh checkout with nothing
  installed.
- **When a template is available** (passed with `--template`, or found
  automatically when the script runs from its home in this plugin): the
  block also matches the template's version and body, so a stale local copy
  fails the check with the two versions named.

Updating to a new template version is an explicit PR in the consuming
repository: rerun `sync --template …` against a current `selfos-skills`
checkout and commit the diff.

## Versioning

The template records its version in the first line
(`<!-- sdd-conventions-template vX.Y.Z -->`): patch for editorial rewording,
minor for a new or loosened rule, major when an existing rule changes
meaning. Editing the template in this repository requires bumping the
version — the self-test pins the released (version, digest) pair, so a body
edit without a bump fails CI here rather than drifting silently.

## What stays local

Repository-specific product rules, phase plans, commands, privacy classes,
lanes, and review policy never move into the template. Repositories with
deliberately different lifecycle rules may keep a concise local summary
instead of the fragment; the summary should name the template version it was
checked against, and such a repository simply does not wire the `check`
command into CI.

Skills in this plugin (`grill-sdd`, and `slice` when it lands) point at the
consuming repository's embedded block — "follow this repository's SDD
conventions" — rather than restating the rules in their own bodies.
