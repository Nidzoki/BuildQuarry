# Copilot Instructions

## Repository status

BuildQuarry is an open-source PySide6 desktop tool that turns oversized software ideas into focused MVP plans. The current prototype has a Python package under `src/buildquarry/`, a local deterministic planner, optional Gemini planning, editable Markdown output, clipboard copy, Markdown export/import, and SQLite plan history.

## Build, test, and lint

Use Python 3.11+:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
buildquarry
```

Run tests with `.venv\Scripts\python.exe -m unittest discover -s tests -v`. Validate syntax with `python -m compileall src`.

Build a Windows portable executable with `.\build_windows.ps1`; output is `dist\BuildQuarry\BuildQuarry.exe`.

## Architecture

The application is a cross-platform PySide6 desktop app targeting Windows and Linux. Keep deterministic planning logic in `domain/`, application use cases in `application/`, infrastructure adapters in `infrastructure/`, and Qt code in `ui/`. Keep planner logic independent from the UI; AI may interpret user input, but application code validates output and enforces scope limits. Treat `README.md` as the product-level description and `LICENSE` as repository metadata.

## Repository conventions

- Keep product scope centered on turning broad project ideas into concrete, time-boxed MVP plans.
- Support both manual local planning and optional Gemini-assisted planning.
- Preserve user control: plans must be editable and support Markdown export/import and clipboard copy.
- Do not commit Gemini API keys. Show users that project data is sent to Gemini before the first AI request.
- Keep Gemini model choices configurable; current default is `gemini-3.6-flash`.
- Keep Gemini network work off the Qt UI thread; cancelled results must not update the UI.
- Prefer both platform installers and portable builds for distribution.
- Follow conventions established by future source files and tooling rather than introducing framework-specific assumptions.
- Update `README.md` and this file when the project gains executable workflows, supported commands, or architectural boundaries.
