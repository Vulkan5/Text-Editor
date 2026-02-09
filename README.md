# Simple Text Editor

A minimal cross-platform text editor built with Tkinter.

## Requirements
- Python 3.7+ (Tkinter included in standard library)

## Run
From the project folder, run:

```powershell
python main.py
```

## Features
- New/Open/Save/Save As
- Undo/Redo, Cut/Copy/Paste, Select All
- Basic keyboard shortcuts (Ctrl+N/O/S/A/Z/Y)

## Additional Features Added
- Autosave: editor saves to `.autosave.txt` every 30 seconds when there are unsaved changes.
- Find/Replace dialog available from `Tools -> Find/Replace` or `Ctrl+F`.
- Create Installer: `Tools -> Create Installer...` will run `make_installer.ps1` to build a single-file executable using PyInstaller (PowerShell required).

## Building an installer (optional)
1. Ensure `pyinstaller` is installed in your Python environment:

```powershell
C:/Users/sgran/code1/.venv/Scripts/python.exe -m pip install pyinstaller
```

2. Run the installer script (PowerShell):

```powershell
powershell -ExecutionPolicy Bypass -File make_installer.ps1
```

The script will create a `dist` folder containing `main.exe` (Windows).
