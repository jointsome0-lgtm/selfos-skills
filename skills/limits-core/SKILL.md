---
name: limits-core
description: Use when setting up or reviewing a persistent agent working kernel with ready defaults, bounded active context, deferred work and recoverable history. Reuses existing memory files and checks size at session entry or after context compaction. Does not run maintenance on every turn or enforce code-repository limits.
license: LICENSE.txt
compatibility: Host-neutral instructions. The optional read-only checker needs Python 3.10+ and read access to selected UTF-8 files. No Git, network, external service or OS-specific runtime is required by the checker. Updating memory needs the workspace's existing write permissions.
metadata:
  selfos.version: "0.2.0"
---

# Limits core

Keep a small working kernel that lets an agent continue the right task with the owner's current constraints and the evidence behind its decisions. Detailed history remains recoverable outside the always-read context.

This skill owns memory selection, continuation and review cadence. Existing workspace instructions govern permissions, publication and version control. It runs independently of `limits`, which checks code repositories, and `handoff`, which creates a temporary transfer document.

## Set up with defaults

For a request such as "Set up limits-core here with the defaults", follow [the default setup](references/adoption.md) and complete the ordinary setup choices without asking the owner to select paths, numbers or commands. Creating a setup follows a setup request; ordinary use continues an existing setup. Preserve the workspace's explicit settings and fill only missing choices from the preset.

Read the workspace's memory instructions and identify the files already serving these roles:

- Always read: direction, active agreements, the current assignment, the next decision and any unresolved answer needed now. Include short pointers to completed results whose absence would invite repeating work.
- Read on demand: deferred obligations and supporting material. Each deferred item needs its state, the condition for returning to it and a usable source reference. Active restrictions and answers needed now stay in the always-read context.
- History: original evidence and past decisions, reached through references. Use the workspace's existing durable storage. The presence of a Git repository alone does not establish that memory is saved there.

These are roles, not required filenames or separate documents. Reuse existing files and settings without duplicating or renaming them. The preset creates one small kernel only when no memory exists; a deferred file is added only when it has material to hold. Store the adopted mapping and checker settings in the workspace's effective agent instructions. On repeat setup, reuse that record and fill missing settings instead of appending another copy.

Verify the setup with one check. Report `review_due` without compressing existing memory during adoption. Correct a mapping error and verify the correction; if a required runtime or source cannot be established, report what remains unverified. The preset numbers are adjustable starting values, not capacity recommendations. Do not raise a target merely to silence a review signal.

## Continue and update

Read the active kernel at session entry or after context compaction. Recheck operational facts needed for the task before treating an old observation as current. Before proposing another task or experiment, find the relevant completed attempt and its evidence, then identify what remains unknown and how the proposed step differs. An invalid or unsuccessful attempt still counts as an attempt.

Update facts and task state when meaningful changes happen. Keep a proposal, an authorized assignment, a sent request, a received answer and a verified result distinct. An elapsed deadline is not an answer or permission. Do not restart a size check or a general memory review on ordinary turns, task completion or memory updates.

## Review at entry boundaries

Run the configured check once at session entry or after compaction. If neither size reaches its review threshold, continue the task without compressing memory. If a threshold is reached, review that group once and verify the result once. An explicit owner request can start a review at any time. The skill does not create timers, scheduled calls or automatic hooks.

During review, remove duplication and resolved expectations from active text; move conditional detail to its durable source or deferred record. Preserve current constraints, unresolved questions, uncertainty, the reason a conclusion changed and the evidence needed to revisit it. Age alone does not close an obligation. Correct a false fact promptly during work without turning the correction into a general review.

For each moved or shortened point, verify what remains, where its source lives and when it will be read. Check the resulting references against the actual files or source records. Keep the prior version recoverable using the workspace's existing history practice. Aim for the configured target without sacrificing necessary meaning; if that cannot be done in one pass, report what still needs room rather than repeating compression or silently changing the budget. A review signal does not authorize bulk deletion, archive migration or publication.

## Read-only check

Run [scripts/check_core.py](scripts/check_core.py) from the adopted workspace with explicit files and targets:

```sh
python3 -B <skill-dir>/scripts/check_core.py \
  --active notes/direction.md notes/current.md --target 6000 \
  --deferred notes/later.md --deferred-target 2400 --margin-percent 33
```

`<skill-dir>` is the installed skill directory. Paths are resolved from the command's working directory. `--deferred` and `--deferred-target` are optional together; both groups accept one or more files. Each resolved file must appear only once. Targets are positive integers and the margin is a nonnegative integer percentage, defaulting to 33.

The checker counts decoded UTF-8 Unicode code points, including whitespace, each CRLF character separately, and a UTF-8 BOM as one code point. These are characters, not tokens or grapheme clusters. Each group's threshold is `ceil(target * (100 + margin_percent) / 100)`; the target itself is informational, and review is due at or above the threshold.

Results are JSON with per-file counts, group totals, thresholds and a status. Exit codes are 0 for `ok`, 1 for `review_due`, and 2 for `error`, such as unreadable input or invalid arguments. Errors take precedence over size findings; incomplete counts are omitted. Fix the named input or argument before rerunning. `--help` prints usage. Input contents are never printed, executed or modified. The checker measures size and input readability; it does not validate links, meaning, completeness or successful history preservation. Reference validation belongs to the actual review above.
