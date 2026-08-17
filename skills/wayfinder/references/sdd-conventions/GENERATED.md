# Generated bundle copy — do not edit

This tree is a build artifact: a copy of the canonical
skill `skills/sdd-conventions/` (version 1.0.1) bundled into
`skills/wayfinder/` as declared by `skills/wayfinder/BUNDLE.json`.
The skill entrypoint is renamed `SKILL.md` -> `CONTRACT.md`
(links rewritten) so hosts that discover skills by recursive filename
scan catalog only canonical skills.
Test files (`test_*.py`) are omitted: CI runs them from the
canonical tree only.

Edit the canonical source instead, then refresh every bundle with
`python scripts/build_bundles.py`. CI rejects drift via
`python scripts/build_bundles.py --check`.
