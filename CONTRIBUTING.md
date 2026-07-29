# Contributing

Thank you for considering a contribution to this project. This repository is
maintained as a portfolio-quality reference implementation, but contributions,
bug reports, and suggestions are welcome.

## Getting started

1. Fork the repository and clone your fork:
   ```bash
   git clone https://github.com/MrBoyard7/invoice-ocr-erp-automation-agent.git
   cd invoice-ocr-erp-automation-agent
   ```
2. Create a virtual environment and install the project in editable mode with
   the development dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   ```
3. Create a feature branch:
   ```bash
   git checkout -b feature/my-improvement
   ```

## Development workflow

- Format code with `black`:
  ```bash
  make format
  ```
- Lint the code with `ruff`:
  ```bash
  make lint
  ```
- Run the test suite with coverage:
  ```bash
  make test
  ```
- Make sure `make check` passes before opening a pull request; it runs
  formatting checks, linting, and the full test suite.

## Commit and pull request guidelines

- Keep commits focused and use descriptive messages.
- Add or update tests for any behavioral change.
- Update `README.md` and `CHANGELOG.md` when the change is user-facing.
- Ensure the CI workflow passes on your pull request.

## Code style

- All code, comments, docstrings, and identifiers must be written in English.
- Follow [PEP 8](https://peps.python.org/pep-0008/); `black` and `ruff` enforce
  this automatically.
- Prefer explicit, well-typed function signatures (this project targets
  Python 3.9+, so use `typing.Optional` / `typing.List` style annotations).
