<#
make_installer.ps1 - helper to build a single-file exe using PyInstaller
Run: powershell -NoProfile -ExecutionPolicy Bypass -File make_installer.ps1
#>

$python = "C:\Users\sgran\code1\.venv\Scripts\python.exe"
if (-not (Test-Path -Path $python)) {
    Write-Error "Python executable not found at $python. Activate your environment or edit this script."
    exit 1
}

# Ensure PyInstaller is installed
& $python -m pip show pyinstaller > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller not found - installing..."
    & $python -m pip install pyinstaller
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to install PyInstaller."
        exit 1
    }
}

# Run PyInstaller
& $python -m PyInstaller --onefile --name simple_text_editor main.py
if ($LASTEXITCODE -eq 0) {
    Write-Host "Build complete. See .\dist\simple_text_editor.exe"
    exit 0
}
else {
    Write-Error "PyInstaller failed"
    exit $LASTEXITCODE
}
