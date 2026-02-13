# Contributing

Thanks for contributing to SQLStratum. This is a small but ambitious foundation library, so clarity,
discipline, and real-world feedback are the most helpful.

## How To Contribute
- Fork the repo and create a branch
- Use the branch naming convention: `release/0.1.x-<short-name>`
- Keep PRs small and focused (one feature or bug fix per branch)
- Open a GitHub PR with a clear description and tests

## Dev Setup
- Create and activate a virtualenv
- Install in editable mode
- Run tests

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .
python -m unittest
```

## Valuable Contributions
- Real app prototypes (Flask/FastAPI or similar) that stress joins, pagination, search, aggregates,
  transactions, and hydration
- DX feedback on the query DSL and runner ergonomics
- Bug reports with minimal repro cases and compiled SQL output

## AI-Assisted Contributions
Using AI tools is encouraged for stress-testing API design by building working app codebases. Feel free
to ask your own agentic coder to provide extensive feedback on developer experience and improvement
ideas. Human review is still expected; AI-generated contributions must be reviewed and tested.

## Guidelines
- No raw SQL string interpolation; use parameters exclusively
- Tests are required for every change
- Be cautious about backward compatibility
