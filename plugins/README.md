# Legacy Claude Code packages

This tree is retained for compatibility with existing `sdd@selfos`, `design@selfos`, `decision@selfos`, `learning@selfos`, `codex-pr@selfos`, and `codex-prompting@selfos` installations.

The canonical Agent Skills catalog now lives in [`../skills/`](../skills/). New features and normal maintenance must start there. The root Claude and Codex adapters both consume that same catalog; do not add a new domain package or duplicate canonical skill text here.

Changes in this directory should be limited to compatibility or security fixes until the legacy packages are retired.
