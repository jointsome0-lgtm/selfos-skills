# `codex-prompting@selfos` is deprecated

This legacy Claude package is a frozen compatibility snapshot. Its deprecation notice first shipped in version `0.2.1` on 2026-07-20.

## Migrate now

If the package is already installed, refresh the marketplace and cached package so this final notice is visible:

```text
/plugin marketplace update selfos
/plugin update codex-prompting@selfos
```

Install the canonical `compose` skill globally for Claude Code:

```bash
npx skills add jointsome0-lgtm/selfos-skills --skill compose --agent claude-code --global --yes
```

After confirming the canonical skill is available, remove the legacy package and reload plugins:

```text
/plugin uninstall codex-prompting@selfos
/reload-plugins
```

## Removal gate

The package will not be removed before **2026-07-20**. Removal also requires all named downstream repositories to stop using the legacy package, the canonical installation smoke matrix to be green, and a dedicated major-migration release note. Removal is tracked in [issue #66](https://github.com/jointsome0-lgtm/selfos-skills/issues/66).
