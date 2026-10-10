# AGENTS.md — for THIS webpage project

You are an agent working inside a project generated from the
`webpage` template. The kit's entry contract is in
`<kit-root>/AGENTS.md`. **This file overrides it where they conflict.**

## Read order

1. **This file.**
2. `index.html` — the page structure.
3. `style.css` — the visual language (MoMA-adjacent: hairline borders, mono type, single accent).
4. `script.js` — any client-side behaviour.

## The webpage's contract

1. **Zero build step.** No npm, no bundler, no transpiler. Drop a
   new `.html` file in the folder and it's live.
2. **Vanilla JS only.** No frameworks unless the owner asks.
3. **Hairline visual language.** The starter uses 0.5px borders,
   one accent color, mono type for numbers. Keep it.
4. **No backend.** This is a static site. Anything that needs a
   server (auth, forms with state, dynamic data) is a different
   template — start a sibling project from `chatbot/` or
   `dashboard/`.

## How to extend

| Owner says... | You do |
|---|---|
| "Add a contact form" | Tell the owner: needs a backend. Point at `templates/chatbot/`. |
| "Add a new page" | Create `about.html` (or whatever), link from `index.html`. |
| "Make it pretty" | Adjust `--accent` in `style.css`. Don't add a framework. |
| "Add a blog" | Drop `.md` files in `posts/`, write a tiny Python script that emits HTML. |
| "Deploy" | See kit-level `knowledge/patterns/deployment.md`. |

## Don't

- Don't add a build step.
- Don't pull in npm.
- Don't add dynamic state — this is a static site.
