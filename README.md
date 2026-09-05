# selfos-skills

Portable workflow skills for coding agents. The canonical distribution is the open Agent Skills layout under `skills/`; Claude Code and Codex plugin manifests are thin adapters over the same files, not the repository's organizing principle.

## Install

The recommended path is CI-tested across Codex, Claude Code, Cursor, and OpenCode. Cline and other Agent Skills-compatible clients are community-tested until they gain their own matrix case:

```bash
npx skills add jointsome0-lgtm/selfos-skills
```

The installer detects available agents and lets you choose skills and scope. Useful non-interactive forms:

```bash
# All skills for Codex, globally
npx skills add jointsome0-lgtm/selfos-skills --skill '*' --agent codex --global --yes

# One skill for Claude Code in the current project
npx skills add jointsome0-lgtm/selfos-skills --skill codebase-design --agent claude-code --yes

# Show the catalog without installing
npx skills add jointsome0-lgtm/selfos-skills --list
```

No clone, working-directory trick, `AGENTS.md` pointer, or prompt-time file path is required.

### Installation support

| Surface | CI evidence | Status |
| --- | --- | --- |
| `skills` catalog discovery | Exact discovered skill set compared with `skills/*/SKILL.md` | CI-tested |
| Codex via `skills` | Isolated global install with complete copied trees and executable modes checked | CI-tested |
| Claude Code via `skills` | Isolated global install with complete copied trees and executable modes checked | CI-tested |
| Cursor via `skills` | Isolated global install with complete copied trees and executable modes checked | CI-tested |
| OpenCode via `skills` | Isolated global install with complete copied trees and executable modes checked | CI-tested |
| Codex native plugin | Representative Codex CLI adds the local marketplace, discovers the sole plugin, installs it, and exposes the exact canonical catalog | CI-tested |
| Claude root marketplace | Representative Claude CLI validates and installs the aggregate package; the aggregate tree and discovered skill union match the canonical catalog | CI-tested |
| Cline and other compatible clients | No dedicated CI matrix case yet | Community-tested |

Every install check rejects missing or unexpected skills, missing or changed companion files, lost executable modes, and absolute checkout paths embedded in installed skill payloads. The matrix source of truth is `scripts/install_smoke_matrix.json`.

### Codex native plugin

The repository also ships a root `.codex-plugin/plugin.json` and `.agents/plugins/marketplace.json`. Register the Git repository as a marketplace, then open `/plugins` and install **selfos-skills**:

```bash
codex plugin marketplace add https://github.com/jointsome0-lgtm/selfos-skills.git
```

The plugin manifest points directly to `./skills/`; it does not mirror or rewrite the catalog.

### Claude Code native plugin

The preferred Claude package is the aggregate plugin over the canonical catalog:

```text
/plugin marketplace add jointsome0-lgtm/selfos-skills
/plugin install selfos-skills@selfos
/reload-plugins
```

The former domain packages (`sdd@selfos`, `design@selfos`, `decision@selfos`, `learning@selfos`, `codex-pr@selfos`, `codex-prompting@selfos`) were removed on 2026-07-20 after their migration window closed ([issue #66](https://github.com/jointsome0-lgtm/selfos-skills/issues/66)); the major-migration release note names each one. Cached installs keep working but receive no updates — migrate with the aggregate plugin above or the universal installer, then uninstall the old package.

## Catalog

| Skill | Purpose | Activation |
| --- | --- | --- |
| `codebase-design` | Deep-module vocabulary, seams, adapters, deletion test, testability | automatic or explicit |
| `compose` | Lean outcome-first prompts for delegating to another model or agent | automatic or explicit |
| `delegate-pr-loop-query` | Ready-to-run continuation query for an open PR review loop, targeting a model from compose's routing table | automatic or explicit |
| `grilling` | Shared one-question-at-a-time owner decision primitive | automatic or explicit |
| `handoff` | Compact privacy-safe context for a fresh agent in one temporary Markdown file | automatic or explicit |
| `improve-codebase-architecture` | Surface deepening candidates as an HTML report, then grill the pick | automatic or explicit (announce first) |
| `limits` | Three-sources-of-truth model enforced as CI numbers: budget, map, goals bound to tests | automatic or explicit |
| `prototype` | Answer one design question with a throwaway worktree prototype | automatic or explicit |
| `research` | Background-subagent investigation captured as one cited Markdown file | automatic or explicit |
| `sdd-conventions` | Portable SDD conventions plus sync and Decision Log lint scripts | automatic or explicit |
| `slice` | Turn one implementation-ready SDD scope into vertical issues | automatic or explicit (announce first) |
| `unslop` | Strip AI tells from prose and add a human voice, meaning preserved | automatic or explicit |
| `wait-what` | Re-pitch the last message simply when it did not land | explicit only |
| `watch` | Codex cloud PR push-review-fix loop | automatic or explicit |
| `wayfinder` | Chart a foggy effort as a map of decision tickets until slice-ready | automatic or explicit (announce first) |

<!-- BEGIN GENERATED COMPATIBILITY; do not edit by hand. -->
## Compatibility

Compatibility describes hard runtime needs and conditional capabilities; descriptive host affinity in a skill's body is not lock-in.

| Skill | Version | Runtime compatibility |
| --- | --- | --- |
| `codebase-design` | `0.1.3` | Host-neutral Markdown guidance; no required tools, OS constraints, network access, write access, or external integrations. |
| `compose` | `0.4.0` | Host-neutral Markdown guidance; no required tools, OS constraints, write access, or external integrations. Network access is optional for refreshing linked provider guidance. |
| `delegate-pr-loop-query` | `0.3.4` | Requires git, gh, network access, authenticated GitHub pull-request read access, and permission to create one file in the operating system's temporary directory. Repository write access is not used by the delegating run after artifact creation; the generated query may authorize it for the fresh run. The generated query directs the fresh run to the sibling `watch` skill, which must be installed in the delegated run's own environment. |
| `grilling` | `0.2.2` | Requires read access to owner-scoped sources. No specific CLI or OS; network, write access, and external integrations are needed only when the chosen facts or an owner-confirmed outcome require them. |
| `handoff` | `0.1.2` | Requires permission to create one file in the operating system's temporary directory. No specific CLI, OS, network access, repository write access, or external integration is required. |
| `improve-codebase-architecture` | `0.3.0` | Requires read access to the target repository and its git history, Python 3.9+ for the bundled SDD helpers, a writable OS temp directory, and a local opener plus a browser for the report. The report page loads and executes Tailwind and Mermaid from public CDNs, so it needs network access — weigh that for private repositories. Repository write access is needed only to land owner-confirmed domain-model or Decision Log updates during the grilling loop. |
| `limits` | `0.2.5` | Requires Python 3.10+ and git for the bundled python scripts, and the checked repository's Python files must parse. OS-independent and offline, with no external integration. |
| `prototype` | `0.1.1` | Requires the host project's own runtime and task runner to run the prototype, and git worktree support for the throwaway branch. Capturing the answer needs write access to the driving issue's tracker and push access to the repository remote; without a writable remote the prototype branch stays local and the pointer says so. No OS constraint; no other external integration. |
| `research` | `0.1.1` | Requires a background subagent mechanism (without one, run the investigation inline), network access for web sources, and write access to the repository checkout to save findings — in a read-only checkout, write to the host's temporary directory and say where. Ticket-driven capture also needs git worktree support, tracker write access, and push access to the remote; without a writable remote the branch stays local and the pointer says so. No OS constraint; no other external integration. |
| `sdd-conventions` | `1.0.1` | Requires Python 3.9+ for the standard-library helpers and write access to the target file when syncing. OS-independent and offline, with no external integration. |
| `slice` | `0.3.0` | Requires Python 3.9+ for bundled SDD helpers, read access to the target repository, network access, and authenticated GitHub issue read/write integration to publish confirmed tickets. No OS constraint. |
| `unslop` | `0.1.0` | No specific CLI, OS, network access, repository write access, or external integration is required. |
| `wait-what` | `0.1.1` | No specific CLI, OS, network access, repository write access, or external integration is required. |
| `watch` | `1.0.1` | Requires bash, git, gh, jq, network access, repository write access, authenticated GitHub pull-request read/write access, and an open PR with Codex review configured; repositories that require a post-verdict manual dispatch additionally need authenticated GitHub Actions write (workflow-dispatch) access; requires a POSIX-style shell environment but no specific OS. |
| `wayfinder` | `0.3.0` | Requires an authenticated gh CLI against a GitHub repository with sub-issues and issue dependencies enabled (see TRACKER.md), network access, write access to the repository holding the SDD Decision Log, and Python 3.9+ for the bundled Decision Log lint. Research and prototype tickets require the sibling research and prototype skills installed; grilling tickets run on the bundled grilling contract. No OS constraint. |
<!-- END GENERATED COMPATIBILITY -->

## Repository layout

```text
skills/<name>/SKILL.md              canonical installable Agent Skill
skills/<name>/references/           bundled docs and generated self-contained dependency copies
skills/<name>/scripts/              portable executable helpers
.codex-plugin/plugin.json           thin Codex adapter over ./skills/
.agents/plugins/marketplace.json    Codex marketplace entry
.claude-plugin/plugin.json          thin Claude aggregate adapter
.claude-plugin/marketplace.json     aggregate entry
AGENTS.md                            generated catalog/fallback, not an installer
scripts/                             catalog validation, indexing, and bundle generation
```

Every top-level skill is independently installable. Where one workflow composes another, a machine-readable manifest at `skills/<name>/BUNDLE.json` declares the canonical dependencies once:

```json
{
  "dependencies": [
    "codebase-design",
    "grilling"
  ]
}
```

`python scripts/build_bundles.py` deterministically copies each complete canonical source folder under `references/<dependency>/`, renames the copied entrypoint `SKILL.md` to `CONTRACT.md` (rewriting same-directory links to it) so hosts that discover skills by recursive filename scan catalog only canonical skills, stamps every copy with a `GENERATED.md` marker so it self-identifies as a build artifact, and maintains a managed `linguist-generated` block in `.gitattributes` so regenerated trees fold away from authored changes in review diffs. Contributors edit only canonical sources — never the generated copies — and CI runs `python scripts/build_bundles.py --check`, which fails with actionable diagnostics on drift, stale trees, dependency cycles, nested composition, missing dependencies, and path-escaping names. Installed skills therefore stay standalone: at runtime they need neither network access nor sibling installations nor host-specific plugin dependency semantics.

One intentionally host-specific field is permitted in canonical frontmatter: `disable-model-invocation: true` on explicit-only skills. Claude Code only enforces the invocation guard when it is a top-level field, other hosts ignore unknown fields, and the portable contract stays in each skill's prose ("Run this workflow only on an explicit request"). Validation allows exactly this field — paired with `metadata.selfos.explicit-only` — and rejects any other host-only frontmatter.

One current skill uses the pairing: `wait-what`, a one-shot owner-invoked trigger whose whole point is that the owner fires it — a topical match must never activate it. The four workflow skills that previously carried it (`improve-codebase-architecture`, `slice`, `wayfinder`, and `grill-sdd` — the last since removed entirely, [issue #122](https://github.com/jointsome0-lgtm/selfos-skills/issues/122)) were deliberately opened to model invocation on 2026-08-05 ([issue #100](https://github.com/jointsome0-lgtm/selfos-skills/issues/100)): Claude Code hides explicit-only skills from the model entirely — the agent cannot even propose them when a task matches — while Codex ignores the field, so the hosts diverged anyway. This is an intentional departure from the "user-invoked in both harnesses or neither" convention; do not restore the flags on those skills to make the hosts symmetric. Each instead opens with an announce-and-proceed prose gate (relaxed from the original confirm-first gate on 2026-08-18, [issue #126](https://github.com/jointsome0-lgtm/selfos-skills/issues/126)): when a task matches, the agent announces the workflow and starts, and the owner can interrupt; unattended runs may work through the read-only and draft stages but stop at every inner confirmation point, so nothing publishes, lands, or merges without the owner.

## Add or change a skill

A canonical skill follows the Agent Skills specification:

```text
skills/my-skill/
  SKILL.md
  references/    # optional
  scripts/       # optional
  assets/        # optional
```

`SKILL.md` uses only standard top-level fields (`name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`). Repository extensions belong in namespaced metadata. Every canonical skill declares its release identity as `metadata.selfos.version: "MAJOR.MINOR.PATCH"`; host-specific extensions likewise stay namespaced rather than becoming Claude- or Codex-only top-level keys.

After editing canonical sources:

```bash
python scripts/build_bundles.py
python scripts/build_index.py
python scripts/validate_skills.py
python scripts/check_version_bump.py --base origin/main
python scripts/build_bundles.py --check
python scripts/build_index.py --check
```

The main CI additionally runs the canonical SDD helper tests, the watcher suite, ShellCheck, and the matrixed installation checks described above.

## Versioning and releases

Canonical skills are versioned independently. `metadata.selfos.version` in each top-level `skills/<name>/SKILL.md` is the source of truth, and every change anywhere in that installable skill tree requires a strict semantic-version increase. Use major for a breaking workflow contract, minor for a backward-compatible capability, and patch for fixes, documentation, or packaging-only changes.

Generated bundle copies carry the source skill's version unchanged because `scripts/build_bundles.py` copies the complete source tree, changing only the entrypoint name (`SKILL.md` → `CONTRACT.md`, links rewritten) and adding the `GENERATED.md` marker. When a dependency changes, bump the source skill and rerun the build, then also bump every composed skill whose regenerated tree changed. The version gate checks each changed top-level tree independently.

The Claude and Codex aggregate manifest versions are generated, not released independently. `scripts/build_index.py` sums the major, minor, and patch components of every canonical skill version separately and adds the committed `VERSION_BASE.json` offset; for example, `1.2.3` plus `0.4.5` on a zero base derives adapter version `1.6.8`. The gate requires every changed skill version to increase, and removing a skill requires folding the removed components into `VERSION_BASE.json` so the derived version still strictly increases, so the derived adapter version strictly increases across release batches whenever canonical skill content changes: two batches can never share it. `python scripts/build_index.py` writes the same value to both manifests, while validation and `--check` reject drift. A nine-skill catalog of nine initial `0.1.0` releases would therefore derive adapter `0.9.0`; the derived value is both a cache identity for the validated version set and the catalog's release identity. It is not a bundle API version and implies no compatibility semantics between independently versioned skills.

Generated version-only edits to the two manifests are part of an ordinary skill release. Any other change under `.claude-plugin/`, `.codex-plugin/`, or `.agents/` changes the aggregate packaging for every skill, so it requires a patch-or-greater bump of every canonical skill even when no behavior changes. The gate distinguishes those substantive adapter edits from the generated version fields and prevents host caches from retaining stale packaging.

Every canonical skill bump gets a tag on the validated merge commit using the existing double-hyphen convention: `{skill}--v{version}` (for example, `watch--v0.1.1`). A release batch tags that same commit as `v{derived}` (for example, `v0.12.11`) and publishes one GitHub Release anchored to that tag. The release title leads with the version plus a short human summary; the date belongs in the release notes or metadata, not the release identity. Existing `bundle-2026-07-16`, `bundle-2026-07-20`, and `bundle-2026-07-21` tags and releases are historical and are not retro-tagged. The release notes must list the complete canonical skill version set and separate these headings, using `None` where a category is empty:

- Skill behavior changes
- Packaging-only changes

Because releases follow merges of skill changes, a release batch that changes nothing installable should not exist: it has no new derived version and therefore nothing to release.

Before tagging, run the full CI validation set against the exact commit and confirm both adapter manifests equal the generated catalog version. Push every new per-skill tag plus the catalog version tag, then create the single GitHub Release; the tag set identifies the exact source revision of an independently installed skill without the original checkout.

## Removed legacy packages

The six Claude domain packages under `plugins/` (`sdd`, `design`, `decision`, `learning`, `codex-pr`, `codex-prompting`) were deprecated on 2026-07-20 and removed the same day after every known consumer migrated ([issue #66](https://github.com/jointsome0-lgtm/selfos-skills/issues/66)). Their `{name}--v{version}` tags and final deprecation-notice releases remain in history for version-keyed caches. New installations use the canonical catalog:

```bash
npx skills add jointsome0-lgtm/selfos-skills --skill '*' --agent claude-code --global --yes
```

## Public repository rules

Use invented examples only. Do not commit personal data, credentials, private repository excerpts, machine-local paths, or agent/tool state. Skills remain repository-agnostic and must not widen the permissions supplied by the user or host runtime.

## License

MIT. Vendored or adapted material carries its required provenance notice inside the installable skill folder.
