$ErrorActionPreference = "Stop"

& ".\.venv\Scripts\python.exe" -m pip install --timeout 180 --retries 5 pyinstaller
& ".\.venv\Scripts\python.exe" -m PyInstaller `
  --noconfirm `
  --clean `
  --name BuildQuarry `
  --windowed `
  --paths src `
  src\buildquarry\main.py

Write-Host "Portable build created at dist\BuildQuarry\BuildQuarry.exe"
