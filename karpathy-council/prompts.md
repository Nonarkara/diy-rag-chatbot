# 3-stage LLM Council — prompts

The three prompts below implement the karpathy LLM Council 3-stage
deliberation. They are the **design pattern**, lifted from the
upstream `backend/council.py` and rewritten as plain text so they
can be run inside Claude Code, OpenCode, Codex, or Gemini CLI.

To use these prompts with your host CLI, the wrapper
[`bin/llm-council`](../bin/llm-council) handles orchestration when
a running karpathy app is detected on `localhost:8001`. When the app
is **not** running, the wrapper falls back to the 0xNyk council
(vendored at [`../council/`](../council/)). See
[`BIN-LLM-COUNCIL.md`](BIN-LLM-COUNCIL.md).

## Stage 1 — First opinions

> You are one of several LLMs convened into a "Council" to answer a
> hard question. Each council member answers independently, without
> seeing the others' answers. Your response here is one of N
> independent first opinions.
>
> Question:
> ```
> {USER_QUERY}
> ```
>
> Constraints on your response:
> - Answer the question directly. Do not preamble.
> - State your assumptions, then your conclusion.
> - If the question is unanswerable from the data given, say so plainly.
> - Length: 200–400 words. No headers, no markdown — flowing prose.

## Stage 2 — Review (anonymized peer ranking)

> You are evaluating responses from a 3-stage LLM Council. Stage 1
> produced the responses below. Stage 2 (this prompt) asks you to
> rank them. **You do not know which model produced which response**
> — the labels are anonymized to prevent you from playing favorites.
>
> Original question:
> ```
> {USER_QUERY}
> ```
>
> Stage 1 responses (anonymized):
>
> {STAGE_1_RESPONSES}
>
> Your task:
> 1. For each response, explain what it does well and what it does
>    poorly. Be specific.
> 2. At the very end of your response, provide a final ranking in
>    EXACTLY this format:
>
> ```
> FINAL RANKING:
> 1. Response A
> 2. Response C
> 3. Response B
> ```
>
> - The line "FINAL RANKING:" must be all caps, with colon.
> - Each rank line is: number, period, space, ONLY the response label.
> - Do not add any other text after the ranking.

After all council members have produced rankings, the orchestrator
parses the `FINAL RANKING:` blocks and computes the average position
per model. This is the "aggregate ranking" shown to the user.

## Stage 3 — Chairman synthesis

> You are the Chairman of an LLM Council. Several AI models have
> answered the user's question independently, then ranked each
> other's answers. Your job is to synthesize everything into a
> single, accurate, well-reasoned final answer.
>
> Original question:
> ```
> {USER_QUERY}
> ```
>
> STAGE 1 — Individual responses (with model names now revealed):
>
> {STAGE_1_RESPONSES_NAMED}
>
> STAGE 2 — Peer rankings (anonymized labels, aggregate per model):
>
> {STAGE_2_AGGREGATE}
>
> As Chairman, produce the council's final answer. Consider:
> - The individual responses and their insights
> - The peer rankings and what they reveal about response quality
> - Any patterns of agreement or disagreement
>
> Your answer:
> - Lead with the council's conclusion.
> - Cite the strongest evidence in plain language.
> - Note any unresolved disagreements explicitly.
> - Length: 300–600 words. Prose, not a list.

---

## How to run the 3 stages manually

If you want to run this pattern by hand (no wrapper, no web app),
here is the sequence for a Claude Code or OpenCode session:

```text
1. Open your host CLI in this repo.
2. Paste Stage 1 prompt with your question.
3. Repeat Stage 1 N times (one per council model), ideally in
   separate sessions so they don't see each other.
4. In a fresh session, paste Stage 2 prompt with all Stage 1 answers.
5. Repeat Stage 2 N times, then parse the FINAL RANKING blocks.
6. In a final session, paste Stage 3 prompt with everything.
7. The Chairman's output is the council's final answer.
```

For multi-model routing (different LLMs in Stage 1), the upstream
karpathy app does this with OpenRouter. To do it with your host CLI,
use the host's provider-routing config or call each model
separately.

For most RAG/chatbot decisions in this repo, the **0xNyk council is
faster and cheaper** — it uses one model with 18 personas instead
of N models with one persona each. Reach for the 3-stage karpathy
pattern when you specifically need model-family diversity
("what would Claude, GPT, and Gemini each think of this?").

## Provenance

- Upstream: <https://github.com/karpathy/llm-council>
- File adapted from: `backend/council.py` (Stage 1, 2, 3 prompts)
- Author: Andrej Karpathy
- Local adaptation: prompts rewritten as plain text, MIT by
  Non Arkaraprasertkul.
