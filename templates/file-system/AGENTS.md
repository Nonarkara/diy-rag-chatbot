# AGENTS.md — for THIS file-system / CLI project

You are an agent working inside a project generated from the
`file-system` template. The kit's entry contract is in
`<kit-root>/AGENTS.md`. **This file overrides it where they conflict.**

## Read order

1. **This file.**
2. `cli.py` — the entry point.
3. `my_tool/` — the package.
4. `tests/` — the test suite.

## The CLI's contract

1. **`argparse` only.** No `click`, `typer`, `fire`. The starter
   is plain argparse.
2. **`--help` and `--version` work out of the box.** Don't break them.
3. **Sub-commands via sub-parsers.** Add new ones by appending.
4. **Errors go to stderr.** Exit codes: 0 ok, 1 user error, 2 internal error.
5. **Tests run with pytest.** Don't switch to unittest.

## How to extend

| Owner says... | You do |
|---|---|
| "Add a 'convert' sub-command" | Append a sub-parser to `cli.py`, implement the function in `my_tool/`. |
| "Read a config file" | Add a `--config FILE` flag, parse with `tomllib` (Py 3.11+) or add `tomli` to deps. |
| "Add a progress bar" | Use `tqdm` — small dep, widely used. |
| "Make it a daemon" | Wrap the core loop with `signal.signal(SIGTERM, ...)` + a PID file. |
| "Publish to PyPI" | Fill in `pyproject.toml`, run `python3 -m build && twine upload dist/*`. |

## Don't

- Don't add a web layer. This is a CLI tool.
- Don't hide exceptions.
- Don't add a build step — keep it `pip install -e .` friendly.
