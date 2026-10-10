# File-system template

A Python CLI tool skeleton. argparse for sub-commands, pytest for
tests, zero web framework. Local-first.

## What's inside

```
my-tool/
├── README.md
├── AGENTS.md
├── pyproject.toml          # project metadata
├── cli.py                   # the CLI entry point
├── my_tool/                 # the actual package
│   └── __init__.py
├── tests/
│   ├── __init__.py
│   └── test_smoke.py
├── requirements.txt
└── bin/start
```

## How it works

The CLI is a single `cli.py` with argparse sub-commands. Add new
sub-commands by appending to the parser. Tests live in `tests/` and
run with `pytest`.

## Run

```bash
./bin/start --help            # show help
./bin/start hello             # run the 'hello' sub-command
./bin/start --version
```

For development:

```bash
python3 -m pytest tests/ -v
```

## Extend

| Owner says... | You do |
|---|---|
| "Add a 'convert' sub-command" | Append a new sub-parser to `cli.py`. |
| "Read a config file" | Add a `--config FILE` flag, parse with `tomllib` or `yaml`. |
| "Run as a daemon" | Wrap the core logic in a `while True` loop with signal handling. |
| "Publish to PyPI" | Fill in `pyproject.toml`, run `python3 -m build && twine upload dist/*`. |

## Don't

- Don't pull in `click` or `typer` unless the owner asks — argparse is enough.
- Don't add a web layer — this is a CLI tool.
- Don't hide exceptions — fail loudly so the owner can see what's wrong.
