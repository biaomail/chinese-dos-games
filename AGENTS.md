# AGENTS.md

This repository focuses on curating and managing Chinese DOS games. Code contributions are minimal; most logic is in `download_data.py` or maintenance scripts.

## Build/Lint/Test
- Download game files: `python download_data.py`
- No formal tests present; scripts should be checked manually for correct behavior.
- For any future tests, use standard pytest pattern:
  - All test scripts should be named `test_*.py` and be runnable with `pytest test_script.py`.
- No linting enforced, but use `flake8 *.py` if adding Python code.

## Code Style Guidelines
- Use PEP8 for Python code: 4-space indents, snake_case names, spaces around operators.
- Place imports at the top of files, one module per line.
- Type hints are recommended for new code (PEP484).
- Prefer explicit error handling (try/except) rather than catch-all exceptions.
- Use descriptive variables, function names, and docstrings for scripts/applications.
- Keep code/data edits atomic and well-commented for clarity.
- When modifying `games.json`, follow existing conventions and key usage as documented in CONTRIBUTING.md.

## Misc
- No Cursor or Copilot rules present as of this writing.
- See README.md and CONTRIBUTING.md for data and PR specifics.
