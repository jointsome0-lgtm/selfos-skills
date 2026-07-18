# Shared SDD conventions — portable distribution

`SDD-CONVENTIONS.md` is the canonical, versioned template for structural rules shared by SDD-stage repositories. A consuming repository embeds a generated copy rather than linking to this skill at runtime, so a fresh checkout can validate its own rules offline with no agent, plugin, or network dependency.

The Decision Log contract lives in [`DECISION-LOG.md`](DECISION-LOG.md). Its standalone checker is [`../scripts/check_decision_log.py`](../scripts/check_decision_log.py).

## Adopt the conventions

1. Copy `../scripts/sync_conventions.py` into the consuming repository, for example as `scripts/check_sdd_conventions.py`.
2. Generate the managed block into the file that owns repository instructions, usually `AGENTS.md` or `SDD.md`:

   ```bash
   python3 scripts/check_sdd_conventions.py sync AGENTS.md \
     --template /path/to/selfos-skills/skills/sdd-conventions/conventions/SDD-CONVENTIONS.md
   ```

3. Commit the vendored script and generated block. Add the offline check to CI:

   ```bash
   python3 scripts/check_sdd_conventions.py check AGENTS.md
   ```

The block records the template version and a SHA-256 digest between managed markers. `sync` edits only that span, preserving repository-specific content before and after it. `check` always validates marker shape and the embedded digest; when a template is supplied or found next to the installed skill, it also rejects stale versions and body drift.

## Vendor the Decision Log lint

Copy `../scripts/check_decision_log.py` into the consuming repository, record its `CHECKER_VERSION`, and invoke it against the file containing the Decision Log:

```bash
python3 scripts/check_decision_log.py SDD.md
```

Both scripts are Python 3.9-compatible, standard-library-only, and independent of this repository after copying. Updating either vendored tool or the conventions block is an explicit reviewed change in the consuming repository.

## What stays local

Product rules, phase plans, commands, privacy classes, lanes, and review policy stay in the consuming repository. The shared template supplies section mechanics only; it never grants tools, permissions, or publication authority.
