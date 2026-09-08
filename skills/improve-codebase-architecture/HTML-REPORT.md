# HTML report

Deliver one HTML file that opens locally without a server or internet access. Include its JavaScript, CSS, fonts, images, shaders, and other assets in the file. Build-time downloads do not authorize runtime requests or sending repository content to an external service.

## Libraries and interaction

Choose any suitable rendering approach or library. CSS, SVG, Canvas, WebGL, WebGPU, Mermaid, and frontend frameworks are options, not a required stack. A separate artifact-builder skill is optional when available.

Use stable library releases published at least **30 days before the report build**. Verify the publication date of the selected version through the publisher's release metadata or package registry, and pin the resolved versions during the build. The age of the project itself does not establish the age of a release. If a version's date cannot be verified, choose another eligible release or use browser-native APIs. Keep version and date evidence with the temporary build files. Avoid unpinned version aliases and runtime CDN imports.

Acquire dependencies without executing package lifecycle hooks, before staging repository-derived data. Execute downloaded build tools or plugins only with networking disabled and filesystem access limited to the temporary workspace and required runtimes, excluding the source checkout and user files. If the host cannot enforce this isolation, use browser-native APIs or prebuilt browser bundles acquired as inert files and executed only in the restricted preview context.

Keep repository-derived names, paths, and excerpts as data. Escape them for their markup, diagram, or embedded-data context; never evaluate them as code. If using Mermaid, retain `securityLevel: "strict"` and disabled diagram click actions.

Useful interactions include highlighting a call path, expanding dependencies, filtering a large graph, and moving between before and after states. Animation should explain a change or relationship. Give the reader stable views and a way to pause motion; honor reduced-motion preferences. Keep the findings and comparison readable when a GPU API is unavailable.

## Token budget

Use the project's configured token budget and counting rules. Prefer its existing read-only measurement. Record the command or calculation, included paths and exclusions, and whether the result describes a commit, the index, or the working tree. Include tests when the project's rules count them. Do not install a checker, change a budget, or modify CI to produce the report.

Repository-provided counters are executable code. Run them only with networking disabled, read access limited to allowed repository paths and required runtimes, and writes confined to the isolated temporary workspace. Exclude user files and keep the source checkout read-only. If the host cannot enforce this isolation, or the counter requires broader access, use the static byte estimate below and state why the project counter was not run.

Show the measured tokens, budget, percentage used, and remaining room or excess. A partial scan must remain labelled partial and must not imply that the full repository fits its budget. Read-scope exclusions still apply when measuring.

If there is no configured budget, show **Budget not configured**. If no project counter exists, a labelled estimate of `ceil(total bytes / 4)` over the allowed tracked files is acceptable. State its scope and exclusions; do not invent a budget or present that estimate as tokenizer output. If measurement cannot be obtained, show **Token usage unavailable** and the reason.

Express size-based recommendations in tokens rather than lines. A proposed change is an estimate or range until implemented and measured; do not present an imagined after-count as a measured result.

## Report structure

Include UTF-8 and viewport declarations. Use semantic sections and choose the layout for the material.

Place a restrictive Content Security Policy before scripts or styles. Block external connections and resource loads, frames, form submissions, and base-URL changes; allow only the embedded scripts, styles, and required data/blob assets. Keep outbound networking blocked during verification and automatic preview even with this policy. Record attempted external requests and treat any attempt as a failed check, including requests that the policy blocks.

The header identifies the repository, date, reviewed revision, token-budget result, and a compact diagram legend. For example, solid boxes can mark modules and dashed arrows can mark seams. State the meaning used in this report.

Each candidate contains:

- A short title naming the proposed deepening.
- The affected files or modules.
- The observed problem and a plain-language proposed solution.
- Benefits in terms of locality, leverage, and observable tests.
- Comparable before and after views.
- A recommendation strength of `Strong`, `Worth exploring`, or `Speculative`.
- A commit or issue reference when the proposal would reopen an earlier decision.

Use the project's domain terminology and the bundled [design vocabulary](references/codebase-design/CONTRACT.md). Keep prose concise and connect every visual to the finding it explains. Finish with a top recommendation, its reason, and a link to its candidate.

## Visual patterns

Choose patterns that make the architecture easier to inspect. These are examples:

- A dependency or call graph can highlight the chain affected by a change.
- A sequence diagram can compare calls or round trips.
- A cross-section can collapse several shallow modules into one deep module.
- A mass diagram can compare interface size with implementation size. Label the measure used; it is not automatically a token count.
- A before/after transition can show moved responsibilities while keeping module identities clear.

Use space and colour to distinguish the important relationships. Keep controls keyboard-accessible and labels readable. Verify the result offline at the intended viewing size, including the main interaction and its resting state. The report remains advisory: controls inspect the proposal and never apply repository changes.
