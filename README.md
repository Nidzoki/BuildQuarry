# BuildQuarry

BuildQuarry is an open-source desktop tool for turning oversized software ideas into focused, achievable MVP plans.

It combines local deterministic planning with optional Gemini-assisted interpretation. Plans can be edited, stored locally, imported, and exported as Markdown.

## Development

Requires Python 3.11 or newer.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
buildquarry
```

If PyPI download times out, retry with a longer timeout:

```powershell
python -m pip install --timeout 180 --retries 5 -e .
```

The current prototype provides a local deterministic planner, optional Gemini planning, editable Markdown output, clipboard copy, Markdown export/import, and SQLite plan history. Gemini mode requires each user to provide their own API key, stored through the operating system keyring. The default Gemini model is `gemini-3.6-flash`.

Gemini plans include technical architecture, data model, API design, technical risks, and implementation notes. Manual plans remain concise and deterministic.

Gemini requests run off the UI thread. The app shows a generating state and lets users cancel the result; the in-flight network call may finish in the background before its result is discarded.

Run tests:

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Create a Windows portable build:

```powershell
.\build_windows.ps1
```

The executable is created at `dist\BuildQuarry\BuildQuarry.exe`. The first build may take several minutes while PyInstaller collects Qt dependencies.
