# Council Demo Session Pack — RAG Edition

Sample prompts and expected output shapes for running a council on
decisions that show up in the **diy-rag-chatbot** project specifically.
For the upstream 3-pack (exploration / market-entry / ship-now) see
[`session-pack.md`](session-pack.md).

The project ships one extra persona: **`council-rag-curator`** (see
[`../agents/council-rag-curator.md`](../agents/council-rag-curator.md)).
It is auto-included on any question whose keywords match
`retrieval | knowledge | rag | embedding | faithfulness`, and it
forces the council to ground every claim in a real file under
`knowledge/`.

---

## Demo R1 — Should we swap `bge-m3` for a smaller embedding?

This is a real RAG/chatbot question. The persona set should include
the curator + an empirical ML lens + a shipping lens.

```bash
./bin/council --members karpathy,feynman,rag-curator,torvalds \
  "We are on bge-m3 (~570M params). Should we swap to bge-small (~33M)
   to halve the embedding latency? The knowledge folder is 412 files."
```

What good output looks like:
- **karpathy** grounds in observed retrieval quality, not theoretical
  embedding benchmarks
- **feynman** strips the latency claim to "where does the time actually
  go" and may discover embedding is not the bottleneck
- **rag-curator** opens a sample knowledge file and traces whether the
  smaller model still returns it for the queries the bot actually
  receives
- **torvalds** refuses to ship a change without a regression test on
  the existing 412-file corpus

Expected verdict sections: Problem, Council Composition, Evidence by
member (must include `EVIDENCED` / `MISSING` labels), Acceptable
Compromises, Kill Criteria, Concrete Next Step (a 30-line benchmark
script, NOT a swap), Unresolved Questions, Follow-Up.

---

## Demo R2 — Is the prompt under the 1,500-character LINE budget?

The bot must answer in ~1,500 characters for LINE. The prompt is the
"how the bot thinks" file, not the answer itself, but a too-long
prompt crowds out the retrieval context. Use a duo — Rams (user
clarity) and Torvalds (maintainability).

```bash
./bin/council --duo --members rams,torvalds \
  "Is the system prompt under 1,500 characters, and does it still
   tell the bot to refuse when the folder has nothing?"
```

What good output looks like:
- **rams** counts the actual character length, names the redundant
  lines, and proposes specific cuts ("delete the second
  'be helpful' clause — first one carries the meaning")
- **torvalds** refuses to cut the refusal rule, even at the cost of
  more characters
- The curator is NOT included here (this is a prompt-shape question,
  not a retrieval question) — but if either member's recommendation
  would change which knowledge files the bot sees, flag it as "needs
  curator review"

---

## Demo R3 — Should we drop the Smart City Thailand standards section?

A real call the owner has to make when the knowledge folder is
growing. This is a strategy question dressed as a knowledge question.

```bash
./bin/council --profile exploration-orthogonal --triad market-entry \
  "Our knowledge folder has 412 files. 80% of the questions we
   actually receive are about Line 1-5. Should we drop the
   Smart City Thailand standards section (28 files) to focus?"
```

What good output looks like:
- **sun-tzu** treats the standards section as terrain: "what
  credibility do you lose if a regulator asks and you don't have it?"
- **machiavelli** maps the actor incentives: "who benefits from
  those 28 files being there? drop them only if the answer is no one
  who pays you"
- **aurelius** checks the moral cost: "what kind of operator are
  you if you delete the standards to save embedding cost?"
- The curator, if pulled in, opens the standards folder, counts
  actual questions it has answered in the last 30 days, and labels
  `EVIDENCED` (asked N times) vs `ASSUMED` (might be asked)

---

## Demo R4 — A real user's question. The hardest one.

This is the canary: a question the bot might get on LINE, asked to
the council as a "should the bot be able to answer this" test.

```bash
./bin/council --members rag-curator,torvalds,karpathy \
  "User asks: 'My LINE OA keeps timing out when I ask long
   questions. Is this a LINE limit or my bot?' The knowledge folder
   has no line-rate-limit.md. Should the bot be allowed to answer?"
```

What good output looks like:
- **rag-curator** opens the knowledge folder, confirms
  `MISSING` for "line rate limits", labels everything
  `INFERRED` or `MISSING`, and says "the bot should refuse this
  question and tell the user where to find the LINE docs"
- **torvalds** agrees: refuse, point at the LINE docs, do not
  improvise
- **karpathy** adds the empirical test: "what fraction of incoming
  questions look like this? if 5%, refuse. if 30%, the knowledge
  folder is the wrong shape and we need a new section"

This is the demo that proves the curator is doing its job: when
the folder does not have it, the verdict is "refuse", not
"improvise plausibly".

---

## When NOT to use the council

A council is not free. The full 18-persona round takes 8–12 minutes
and burns tokens. Reserve it for:

- Decisions that are hard to reverse (delete a knowledge section,
  change the prompt, swap a model)
- Decisions where the owner is genuinely uncertain
- Decisions where one perspective is going to dominate and the owner
  wants the dissent on record

For everything else, ask the host directly. The host already knows
the project; the council is for when one head is not enough.
