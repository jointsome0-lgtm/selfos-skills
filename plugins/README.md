# Deprecated Claude Code packages

The `sdd@selfos`, `design@selfos`, `decision@selfos`, `learning@selfos`, `codex-pr@selfos`, and `codex-prompting@selfos` packages were deprecated on **2026-07-20**. Each package received one final deprecation release so existing version-keyed Claude caches can surface its package-level README and migration command.

The canonical Agent Skills catalog lives in [`../skills/`](../skills/). New features and normal maintenance must start there. To install the full canonical catalog globally for Claude Code:

```bash
npx skills add jointsome0-lgtm/selfos-skills --skill '*' --agent claude-code --global --yes
```

Package-level READMEs list narrower commands for users who want only the canonical replacements for one legacy package. Existing cached users can fetch the final notice with `/plugin marketplace update selfos` followed by `/plugin update <name>@selfos`.

## What remains mutable

- Nothing in this tree is generated.
- `deprecation.json`, this file, every package README, and every legacy manifest are manually maintained deprecation metadata.
- All skill bodies, examples, conventions, scripts, tests, and provenance files are frozen compatibility snapshots.
- CI rejects changes under `plugins/` by default. A maintainer may label a PR `legacy-plugin-compatibility` for a necessary host-compatibility fix or `legacy-plugin-security` for a security fix. Either exception remains package-scoped, cannot add another legacy package, and still requires a strict manifest-version increase. The security label is the explicit escape hatch when freezing vulnerable content would be unsafe.
- The dedicated removal PR uses `legacy-plugin-removal`; CI accepts it only on or after the earliest removal date and only when it removes every legacy package together.

## Removal checklist

The tree will not be removed before **2026-07-20**. [Issue #66](https://github.com/jointsome0-lgtm/selfos-skills/issues/66) owns the major migration and stays blocked until:

- `selfos`, `atlas`, `exp2res`, `tollgate`, and `story` no longer document or depend on a legacy domain package;
- repository and ecosystem docs point to the canonical `npx skills add jointsome0-lgtm/selfos-skills` path or the aggregate `selfos-skills@selfos` adapter;
- the canonical installation smoke matrix is green for the removal commit; and
- a major-migration release note names all removed packages, repeats the migration command, and explains the cache transition.
