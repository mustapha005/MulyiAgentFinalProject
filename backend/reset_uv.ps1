# Fix local uv environment and force public PyPI resolution.
# Run from the backend folder in PowerShell:
#   .\reset_uv.ps1

if (Test-Path .venv) {
  Remove-Item -Recurse -Force .venv
}
if (Test-Path uv.lock) {
  Remove-Item -Force uv.lock
}

$env:UV_DEFAULT_INDEX = "https://pypi.org/simple"
uv python install 3.12
uv python pin 3.12
uv sync --refresh
