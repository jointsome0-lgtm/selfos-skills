# Default setup

Use this preset when asked to set up limits-core. Preserve existing memory, explicit targets, review cadence and required checker commands. Fill only missing choices. A later setup request reuses the recorded setup; a heading alone is not evidence that its settings are complete. Keep the checker and its documented cadence when local instructions mandate them; limits-core then supplies the memory roles and compatible review guidance.

## Choose the existing memory first

Read the effective workspace instructions and the memory they reference. Map the memory roles from their actual contents; do not include every startup document in the character count. Keep the existing files and established history practice. If a material ambiguity remains, ask about that ambiguity instead of creating a competing memory system.

Use these defaults only where the workspace has no explicit setting:

| Setting | Default |
| --- | --- |
| Combined always-read target | 6000 Unicode characters |
| Deferred target, when needed | 2400 Unicode characters |
| Review margin | 33 percent |
| Check cadence | Once at session entry or after context compaction |
| New kernel, only if no memory exists | `memory/KERNEL.md` |
| New deferred file, only when it has material | `memory/DEFERRED.md` |

The resulting default thresholds are 7980 active characters and 3192 deferred characters. These are adjustable starting values, not measured capacity limits.

## Start a workspace without memory

Create `memory/KERNEL.md` only if no existing memory serves the role. Start with this structure and fill it from known current facts; leave a section empty when the request supplies nothing for it:

```markdown
# Working kernel

## Direction and agreements

## Current
```

If no substantive assignment is known, Current can say "No assignment recorded"; adopting the skill is not a new ongoing assignment. Do not invent agreements or a prior history. Do not create a deferred file or archive just to fill the layout. If no recoverable history practice exists, record that fact; a prior version must be saved before the first review rewrites memory.

## Record the setup once

Merge one settings block into the instruction file the current host actually reads. Find the record that refers to limits-core and reuse it by its meaning and contents. A complete preset record has the active file list, positive target, margin, checker location or resolution rule, working directory and cadence, plus either deferred files with a target or an explicit "none yet". For a retained custom checker, the record is complete when it names that checker's command, files, working directory and documented cadence; do not add preset targets or a margin to it. Repair missing settings in place. If no instruction file exists, create the workspace entrypoint supported by the current host, such as `AGENTS.md` where supported. Keep unrelated instructions intact and follow existing pointers between host entrypoints. If several hosts are being configured, point their entrypoints to one shared settings record instead of copying the settings.

For the new one-file layout, use this block:

```markdown
## Working kernel with limits-core

At session entry or after context compaction, read memory/KERNEL.md and use the installed limits-core skill. Update the current facts and task state there during work.

Always read: memory/KERNEL.md.
Deferred: none yet. When material first needs deferring, create memory/DEFERRED.md and add --deferred memory/DEFERRED.md --deferred-target 2400 to the checker arguments. Consult that file before choosing new work or returning to the deferred topic.
History: not established. Preserve a recoverable prior version before the first review rewrites memory.
Checker working directory, relative to the workspace root: .
Checker arguments: --active memory/KERNEL.md --target 6000 --margin-percent 33

Resolve scripts/check_core.py from the currently installed limits-core skill and run it with Python 3.10+ and these arguments once at entry or after compaction. Review only a group that reaches its threshold, then verify once. During work, update facts without routine size checks or compression. An explicit owner request can start a review at any time. During initial setup, report review_due without compressing memory.
```

Resolve the installed script location at execution time. Record concrete arguments with paths relative to the recorded working directory and quoted for the current shell, not a placeholder command or a versioned plugin-cache path. Keep settings in this block; do not duplicate them in the kernel or a new configuration file. Retain a mandated custom checker and its own command rather than passing limits-core arguments to it.

For an existing workspace with `notes/direction.md`, `notes/current.md` and `notes/later.md`, reuse those files. Keep its actual targets, cadence and history reference; if no targets were set, the preset arguments are:

```text
--active notes/direction.md notes/current.md --target 6000 --deferred notes/later.md --deferred-target 2400 --margin-percent 33
```

Record all three files' roles and replace the new-layout history line with the established recoverable source. An existing custom checker keeps its own invocation. No copy, rename or replacement of memory is needed.

## Verify and report

Run the recorded check from its recorded working directory. `ok` confirms the size check works. `review_due` also confirms the check works and signals a later review; do not compress during setup. Correct an input or argument error and check the corrected setup. If Python 3.10+ or the installed skill directory cannot be located, preserve the mapping and report verification as not performed.

Tell the owner which files and defaults were adopted, which existing choices were retained, and the actual check result. No watcher or host compaction hook is installed. A successful size check does not establish preservation of meaning or history.
