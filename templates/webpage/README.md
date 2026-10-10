# Webpage template

A static HTML/CSS/JS site. No build step. Run with `python -m
http.server` or any static host.

## What's inside

```
my-site/
├── README.md
├── AGENTS.md
├── index.html           # the page
├── style.css            # hairline, MoMA-adjacent
├── script.js            # vanilla JS, no framework
└── bin/start            # local dev: python -m http.server
```

## How it works

It's a folder of static files. Drop in more `.html`, more `.css`,
more `.js`. The `bin/start` script serves them on
`http://127.0.0.1:8000` for local preview.

For deployment, drop the folder on any static host: GitHub Pages,
Netlify, Cloudflare Pages, S3 + CloudFront. No build needed.

## Run

```bash
./bin/start
# open http://127.0.0.1:8000
```

## Extend

| Owner says... | You do |
|---|---|
| "Add a new page" | Create `about.html`, link from `index.html`. |
| "Make it dark mode" | Add a `prefers-color-scheme` block in `style.css`. |
| "Add a contact form" | Wire `script.js` to POST to `/api/...` — the form needs a backend; consider `templates/chatbot/` for that. |
| "Add a blog" | Add a `posts/` folder with one `.md` per post; render with a tiny Python script that emits HTML. |
| "Deploy" | See kit-level `knowledge/patterns/deployment.md`. |

## Don't

- Don't add a build step unless the owner asks for React/Vue/Svelte.
- Don't pull in npm packages. The whole point is zero deps.
- Don't read secrets into the page. Anything sensitive belongs in an API.
