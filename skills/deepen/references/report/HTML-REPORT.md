# HTML Report Format

The architectural review is rendered as a single self-contained HTML file in the OS temp directory. **Offline and script-free**: all CSS is inline in one `<style>` block, all diagrams are hand-built divs and inline SVG, and there is no `<script>`, CDN, or network reference of any kind — the file must render fully from `file://` with no connectivity. If the owner wants richer external assets, that is their explicit action after the run, never the report's dependency. Repository-derived strings (paths, identifiers, excerpts) are HTML-escaped data, kept to the minimum each card needs.

## Scaffold

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Architecture review — {{repo name}}</title>
    <style>
      /* Everything inline — no external assets, no scripts. */
      :root { --ink: #0f172a; --paper: #fafaf9; --line: #e2e8f0;
              --accent: #059669; --leak: #dc2626; --warn: #d97706; }
      body { margin: 0; background: var(--paper); color: var(--ink);
             font: 16px/1.6 system-ui, sans-serif; }
      main { max-width: 64rem; margin: 0 auto; padding: 3rem 1.5rem; }
      article { border: 1px solid var(--line); border-radius: .5rem;
                background: #fff; padding: 1.5rem; margin: 2.5rem 0; }
      .files { font-family: ui-monospace, monospace; font-size: .875rem; }
      .badge { display: inline-block; padding: .1rem .6rem; border-radius: 999px;
               font-size: .75rem; text-transform: uppercase; letter-spacing: .05em; }
      .strong { background: #d1fae5; color: #065f46; }
      .worth { background: #fef3c7; color: #92400e; }
      .spec { background: #e2e8f0; color: #334155; }
      .pair { display: flex; gap: 1rem; }
      .pair > * { flex: 1; min-width: 0; }
      .label { font-size: .75rem; text-transform: uppercase; letter-spacing: .08em; }
      .seam { stroke-dasharray: 4 4; }
      .leak { stroke: var(--leak); stroke-width: 2; }
      .deep { background: linear-gradient(135deg, #0f172a, #1e293b); color: #e2e8f0; }
      .callout { border-left: 4px solid var(--warn); background: #fffbeb;
                 padding: .5rem 1rem; }
      .evidence { font-size: .8rem; color: #475569; }
    </style>
  </head>
  <body>
    <main>
      <header>…</header>
      <section id="candidates">…</section>
      <section id="top-recommendation">…</section>
    </main>
  </body>
</html>
```

## Header

Repo name, date, the scan scope (the named direction or the history window used), and a compact legend: solid box = module, dashed line = seam, red arrow = leakage, thick dark box = deep module. No introduction paragraph — straight into the candidates.

## Candidate card

The diagrams carry the weight. Prose is sparse, plain, and uses the glossary terms (from [../codebase-design/SKILL.md](../codebase-design/SKILL.md)) without ceremony.

Each candidate is one `<article>`:

- **Title** — short, names the deepening (e.g. "Collapse the intake pipeline").
- **Badge row** — recommendation strength (`Strong` = emerald, `Worth exploring` = amber, `Speculative` = slate), plus a tag for the dependency category (`in-process`, `local-substitutable`, `ports & adapters`, `mock`).
- **Files** — monospaced list, minimum paths only.
- **Before / After diagram** — the centrepiece. Two columns, side by side. See patterns below.
- **Problem** — one sentence. What hurts.
- **Evidence** — one line naming the source that grounds the problem: the traced call path, the failing test surface, or the history hot spot. No candidate ships without it.
- **Solution** — one sentence. What changes.
- **Wins** — bullets, ≤6 words each. e.g. "Tests hit one interface", "Pricing logic stops leaking", "Delete 4 shallow wrappers".
- **Recorded-decision callout** (if applicable) — one line in an amber-tinted box naming the Decision Log entry or decided issue it conflicts with, and the concrete new friction that justifies reopening.

No paragraphs of explanation. If the diagram needs a paragraph to be understood, redraw the diagram.

## Diagram patterns

Pick the pattern that fits the candidate. Mix them. Don't make every diagram look the same — variety is part of the point.

### Boxes-and-arrows in inline SVG (the workhorse for dependencies / call flow)

Modules as `<rect>` or bordered `<div>`s with labels; calls as SVG `<line>`/`<path>` with marker arrowheads. Colour leakage edges with `.leak`, dash seams with `.seam`, and render the "after" module with `.deep` so it reads as one thick-walled deep module with greyed-out internals. When the point is "X calls Y calls Z, and look at the mess", draw exactly that mess — six arrows crossing — beside the after-column's single entry point.

```html
<div class="pair">
  <figure>
    <figcaption class="label">Before</figcaption>
    <svg viewBox="0 0 320 200" role="img" aria-label="call flow before">
      <rect x="10" y="10" width="120" height="36" fill="#fff" stroke="#0f172a"/>
      <line x1="130" y1="28" x2="190" y2="28" class="leak"/>
      <!-- … -->
    </svg>
  </figure>
  <figure>
    <figcaption class="label">After</figcaption>
    <!-- one thick-bordered deep module, internals faded -->
  </figure>
</div>
```

### Cross-section (good for layered shallowness)

Stack horizontal bands to show layers a call passes through. Before: 6 thin layers each doing nothing. After: 1 thick band labelled with the consolidated responsibility.

### Mass diagram (good for "interface as wide as implementation")

Two rectangles per module — one for interface surface area, one for implementation. Before: interface rectangle is nearly as tall as the implementation rectangle (shallow). After: interface rectangle is short, implementation rectangle is tall (deep).

### Call-graph collapse

Before: a tree of function calls rendered as nested boxes. After: the same tree collapsed into one box, with the now-internal calls shown faded inside it.

## Style guidance

- Lean editorial, not corporate-dashboard. Generous whitespace. A serif stack for headings works well against stone/slate tones.
- Colour sparingly: one accent (emerald or indigo) plus red for leakage and amber for warnings.
- Keep diagrams ~320px tall so before/after sits comfortably side by side without scrolling.
- Use the `.label` treatment (small caps, tracked out) for module labels inside diagrams — they should read as schematic, not as UI.
- No scripts, no interactivity, no external fonts or images. The report is a static document; everything it needs travels inside the one file.

## Top recommendation section

One larger card. Candidate name, one sentence on why, anchor link to its card. That's it.

## Tone

Plain English, concise — but the architectural nouns and verbs come straight from [../codebase-design/SKILL.md](../codebase-design/SKILL.md). Concision is not an excuse to drift. Domain names come from the project's SDD-defined terms: if the SDD defines "Order," talk about "the Order intake module" — not "the FooBarHandler," and not "the Order service."

**Use exactly:** module, interface, implementation, depth, deep, shallow, seam, adapter, leverage, locality.

**Never substitute:** component, service, unit (for module) · API, signature (for interface) · boundary (for seam) · layer, wrapper (for module, when you mean module).

**Phrasings that fit the style:**

- "Order intake module is shallow — interface nearly matches the implementation."
- "Pricing leaks across the seam."
- "Deepen: one interface, one place to test."
- "Two adapters justify the seam: HTTP in prod, in-memory in tests."

**Wins bullets** name the gain in glossary terms: *"locality: bugs concentrate in one module"*, *"leverage: one interface, N call sites"*, *"interface shrinks; implementation absorbs the wrappers"*. Don't write *"easier to maintain"* or *"cleaner code"* — those terms aren't in the glossary and don't earn their place.

No hedging, no throat-clearing, no "it's worth noting that…". If a sentence could be a bullet, make it a bullet. If a bullet could be cut, cut it. If a term isn't in the [../codebase-design/SKILL.md](../codebase-design/SKILL.md) glossary, reach for one that is before inventing a new one.
