# Contributing to nucosObs

Thanks for contributing. Bug reports, focused fixes, tests, documentation, and
small examples are all useful contributions.

## Development Setup

1. Use Python 3.11, 3.12, or 3.13.
2. Create and activate a virtual environment.
3. Install the project and test dependencies with `pip install -e ".[test]"`.
4. Run the complete suite with `python -m pytest`.

## Pull Requests

- Start from the current default branch and keep a pull request focused.
- Add or update tests for every behavior change or bug fix.
- Update `README.md` and `docs/CHANGELOG.md` when a change affects users.
- Ensure `python -m pytest` passes before requesting review.
- Explain the problem, solution, and verification in the pull request.

## Reporting Bugs

Use the bug report template and include the Python version, package version,
minimal reproduction, expected behavior, and observed behavior. Do not report
security vulnerabilities in public issues; follow `SECURITY.md` instead.