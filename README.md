# JSON Form Viewer (Desktop)

A standalone Python desktop app that renders JSON files as an editable,
form-based GUI - the same behavior as the
[json-form-viewer VS Code extension](../json_viewer), but packaged as a native
Windows `.exe`.

- **Objects** render as labeled fields.
- **Nested objects and arrays** render as collapsible sections (click the ▸/▾ toggle).
- **Arrays** render as repeatable items with an **+ Add Item** button and a
  per-item ✕ remove button.
- **Primitive values** (`string`, `number`, `boolean`, `null`) render as editable
  inputs with a live type badge.
- **Auto type coercion**: `true` -> boolean, `123` -> number, `null` -> null,
  anything else -> string.
- **Toolbar** with Open, Save, Expand All, Collapse All, and a Light/Dark theme
  toggle (defaults to the Windows system theme).
- No third-party runtime libraries - only the Python standard library (`tkinter`).

## Project structure

```
json-form-viewer-py/
├── main.py                    # Entry point: python main.py [file.json]
├── requirements.txt           # Build dependency (PyInstaller)
├── JsonFormViewer.spec        # PyInstaller spec (single-file, windowed .exe)
├── build.bat                  # One-click Windows build script
├── sample.json                # Example file for testing
└── json_form_viewer/
    ├── __init__.py            # Package metadata
    ├── __main__.py            # python -m json_form_viewer
    ├── app.py                 # Main window, toolbar, file IO, theme
    ├── renderer.py            # Form widgets + type detection + serialization
    └── theme.py               # Light/dark color palettes
```

## Requirements

- Python 3.9+ (3.10+ recommended).
- `tkinter`:
  - **Windows 11** - bundled with the official Python installer by default.
  - **Debian** - install with `sudo apt install python3-tk`.

## Run from source

Windows (Command Prompt / PowerShell):

```bat
python main.py sample.json
```

Debian / Linux:

```bash
sudo apt install python3-tk
python3 main.py sample.json
# or
python3 -m json_form_viewer sample.json
```

Keyboard shortcuts: `Ctrl+O` open, `Ctrl+S` save.

## Build an executable

### Windows 11 (.exe)

Double-click `build.bat`, or run:

```bat
python -m pip install -r requirements.txt
python -m PyInstaller --clean --noconfirm JsonFormViewer.spec
```

Output: `dist\JsonFormViewer.exe` - a single, self-contained file with **no
console window** and no Python installation required on the target machine.

### Debian / Linux (native binary)

```bash
python3 -m pip install -r requirements.txt
./build.sh
```

Output: `dist/JsonFormViewer` - a single, self-contained ELF binary.

### Optional: associate `.json` with the app

1. Right-click a `.json` file -> **Open with** -> **Choose another app**.
2. Browse to `dist\JsonFormViewer.exe` and enable "Always use this app".
   The app accepts a file path as its first command-line argument, so
   double-clicking a `.json` file opens it directly.

## Notes

- Only valid JSON can be saved; invalid or empty input shows an inline message.
- Saved files use 2-space indentation, UTF-8 encoding, and preserve non-ASCII
  characters (no `\uXXXX` escaping).
- On Windows 11 dark mode is detected via the registry; on Debian/GNOME it is
  detected via `gsettings`. Other environments default to the light theme.
  A manual Light/Dark toggle is always available in the toolbar.

## License

MIT
