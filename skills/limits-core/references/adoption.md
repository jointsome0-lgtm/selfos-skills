# Example adoption

An invented workspace already uses `notes/direction.md`, `notes/current.md` and `notes/later.md`. Its established archive holds completed work. Adopt those files without renaming them or copying their contents into new documents.

Merge a small settings block into its existing agent instructions:

```markdown
## Working kernel

Read notes/direction.md and notes/current.md at session entry or after context compaction. Consult notes/later.md before choosing new work or returning to a deferred topic. Preserve active restrictions and answers needed for the current task in the always-read files.

The active target is 6000 Unicode characters, the deferred target 2400, and the review margin 33%. At entry or after compaction, run the registered limits-core checker command once. Review only a group that reaches its threshold, then verify once. During work, update facts and statuses without routine measurement or compression. An explicit owner request may start a review immediately.

Use the existing archive for evidence and prior decisions. Verify references when material moves and keep the prior version recoverable. A completed task is not an automatic trigger for compression.
```

Register the command using the actual installed skill location:

```sh
python3 -B <skill-dir>/scripts/check_core.py \
  --active notes/direction.md notes/current.md --target 6000 \
  --deferred notes/later.md --deferred-target 2400 --margin-percent 33
```

These settings give review thresholds of 7980 active characters and 3192 deferred characters. The example numbers are replaceable adoption settings. A smaller workspace with one existing file and no deferred list can use:

```sh
python3 -B <skill-dir>/scripts/check_core.py --active CONTEXT.txt --target 3000
```

Do not add a deferred file until there is material that belongs there. Neither example installs a watcher or changes the host's context-compaction mechanism.
