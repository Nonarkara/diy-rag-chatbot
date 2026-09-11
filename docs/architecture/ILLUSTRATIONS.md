# Illustrations

The visuals for this repo use a deliberate fusion: **Japanese manga
passionate style** for the linework, characters, and energy —
combined with **MoMA rules** for the discipline: hairline frames,
single amber accent, mono type, dense info strips, bracket
terminators.

## The set

| File | What | Use it for |
|---|---|---|
| [`hero.svg`](hero.svg) | The orchestrator as a manga-passionate figure with 6 persona echoes around and an amber verdict beam | README hero, project landing, social cards |
| [`wrong-vs-right.svg`](wrong-vs-right.svg) | Side-by-side manga panels: multi-bot Telegram chaos vs single-orchestrator harmony | README, AGENTS.md, the "why" conversation |
| [`the-five-stages.svg`](the-five-stages.svg) | A 5-panel manga page: each stage of the protocol as one panel | Architecture explainer, slide deck |
| [`why-this-wins.svg`](why-this-wins.svg) | 4-row comparison: single-LLM / multi-bot / RAG / this orchestrator | Architecture explainer, the pitch |
| [`flow-0xnyk-council.svg`](flow-0xnyk-council.svg) | Clean editorial flow diagram for the 0xNyk 5-stage protocol | Architecture explainer |
| [`flow-karpathy-council.svg`](flow-karpathy-council.svg) | Clean editorial flow diagram for the karpathy 3-stage protocol | Architecture explainer |
| [`flow-comparison.svg`](flow-comparison.svg) | Side-by-side flow comparison | Architecture explainer |

## Why this style

Manga is **informationally dense**. A single panel can carry emotion,
position, contradiction, and movement — at once. For an orchestrator
that does five stages and nineteen personas, that density is the
right surface.

MoMA is **disciplined**. Hairline frames, a single accent colour,
mono type for numbers, bracket terminators for sections, a
consistent data strip across the bottom — so the reader's eye
knows where the truth lives (the amber cell, the mono digits) and
where the noise lives (the rest).

The two together: cyberpunk-manga. The same vocabulary Rams would
have used if he had grown up reading Akira and Ghost in the Shell.

## Rendering

All SVGs are pure XML, no external assets. They render in:

- GitHub markdown (embed with `![alt](path.svg)`)
- Any modern browser
- VS Code preview
- Apple Keynote / Google Slides via drag-and-drop

Total size: ~76 KB for the seven illustrations.

## Editing

Each SVG is hand-coded but follows the same skeleton:

```
<svg viewBox="0 0 W H" font-family="...">
  <defs>
    <pattern id="halftone-..." />
    <style>.frame, .frame-hair, .frame-amber, .ink, .amber, ...</style>
  </defs>

  <!-- background paper -->
  <rect width="W" height="H" fill="#fafaf7"/>

  <!-- outer hairline frame -->
  <rect class="frame" x="20" y="20" .../>
  <rect class="frame-hair" x="28" y="28" .../>

  <!-- top MoMA strip: fig number + title + version -->
  <rect class="frame-hair" x="40" y="40" .../>
  <text class="text-tiny">fig 00 · ...</text>
  <text class="text-title">...</text>

  <!-- illustration body (manga characters, panels, etc.) -->

  <!-- bottom MoMA strip: operating metrics / caption -->
  <rect class="frame-hair" x="40" y="..." .../>
  <text class="text-tiny-amber">▶ operating</text>
  ...
</svg>
```

If you add a new illustration, copy the skeleton, change the body,
and keep the top + bottom strips consistent. That's the MoMA
discipline.

## Provenance

All illustrations in this folder are part of `diy-rag-chatbot`,
MIT-licensed by Non Arkaraprasertkul, except for the three upstream
flow diagrams (`flow-0xnyk-council.svg`, `flow-karpathy-council.svg`,
`flow-comparison.svg`) which are adapted from the vendored council
vendoring.
