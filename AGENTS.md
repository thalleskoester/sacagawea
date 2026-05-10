# AGENTS.md

Guidance for AI agents working in this repository.

## Project Purpose

`sacagawea` is a Python backend library for parsing and evaluating a small
filter language. The v1 goal is to let Python developers parse filter strings
into a pure abstract syntax tree and evaluate that tree against in-memory
`list[dict]` data.

Treat those documents as the source of truth until the feature moves out of
`.wip/`. Do not replace settled contract decisions with ad hoc implementation
choices.

## Project Structure

Expected structure as implementation proceeds:

```text
.
|-- .docs/
|   |-- AGENTS.md
|   `-- features/
|       |-- .wip/
|       `-- [feature-name]/        # Completed feature docs
|-- src/
|   `-- sacagawea/                 # Library package, to be added
|-- tests/                         # Pytest suite, to be added
|-- storage/
|   |-- cache/                     # Tool caches; do not hand-edit
|   |-- logs/
|   `-- tmp/                       # Test temp output
|-- pyproject.toml
|-- ruff.base.toml
|-- uv.lock
`-- uv.toml
```

Do not treat files under `storage/cache/` or `.venv/` as project source.

## Development Commands

Use `uv` for dependency and command execution:

- `uv sync`
- `uv add [package]`
- `uv run pytest`
- `uv run ruff check .`
- `uv run ruff format .`
- `uv run ty check`

For docs-only changes, a syntax or formatting check is usually enough if no code
was changed. For code changes, run the narrowest relevant tests first, then the
full quality gates before handoff when feasible.

## Coding Guidelines

- Use TDD for implementation work.
- Keep modules small and direct.
- Prefer immutable or mutation-safe public contract objects.
- Keep parsing, AST contracts, runtime value modeling, interpretation, and
  exceptions separated enough that future interpreters can consume the same AST.
- Use structured exceptions for user-caused failures. Do not leak raw parser,
  regex, datetime, or Python runtime exceptions through public APIs.
- Use standard-library parsing for v1. Do not add a parser dependency unless the
  plan/spec is explicitly revised.
- Keep dependencies minimal. Add dependencies only when they materially simplify
  implementation and fit the feature contract.
- Update docs when public APIs, commands, configuration, package layout, or
  safety-limit defaults change.

## Formatting And Linting

Ruff configuration is split between `pyproject.toml` and `ruff.base.toml`.
Project formatting expectations include:

- Line length: `120`
- Double quotes
- Space indentation
- Docstring code formatting enabled
- Strict docstring rules are enabled for source code

Tests have relaxed annotation and docstring rules through Ruff per-file ignores.

## Git Commit Guidelines

Use Conventional Commits:

```text
[type]: [description]

[optional body]

[optional footer(s)]
```

Common types:

- `build`: build system or dependency changes
- `ci`: CI configuration or scripts
- `docs`: documentation-only changes
- `feat`: new feature behavior
- `fix`: bug fix
- `perf`: performance improvement
- `refactor`: code change that neither fixes a bug nor adds a feature
- `style`: formatting-only change
- `test`: tests only

For breaking changes, append `!` after the type and include a
`BREAKING CHANGE:` footer.

## Before Finishing Work

Before handing off, check the relevant source of truth:

- If changing contract behavior, update the spec or asset file that owns that
  contract.
- If changing public API or usage, update README/docs once those files exist.
- Run the relevant checks and report any checks you could not run.
