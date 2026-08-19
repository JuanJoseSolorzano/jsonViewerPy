#==================================================================================
# JSON Form Viewer - main application window.
#
# A standalone Tkinter/ttk desktop app that renders a JSON file as an editable
# form and saves edits back to disk. Intended to be packaged as a Windows .exe
# with PyInstaller.
#==================================================================================

import json
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from . import renderer, theme
from . import __version__, __title__

def sanitize_jsonc(text: str)->tuple[str,bool]:
    """Convert JSONC (JSON with // or /* */ comments and trailing commas)
    into strict JSON while preserving string literals.

    Returns a (sanitized_text, modified) tuple. The second element is True if
    any comment or trailing comma was removed.
    """
    output = []
    modified = False
    in_string = False
    line_comment = False
    block_comment = False
    i = 0
    n = len(text)

    while i < n:
        ch = text[i]
        nxt = text[i + 1] if i + 1 < n else ''

        if line_comment:
            if ch == '\n':
                line_comment = False
                output.append(ch)
            else:
                modified = True
            i += 1
            continue

        if block_comment:
            if ch == '*' and nxt == '/':
                block_comment = False
                output.append(' ')
                modified = True
                i += 2
                continue
            if ch == '\n':
                output.append(ch)
            else:
                modified = True
            i += 1
            continue

        if in_string:
            output.append(ch)
            if ch == '\\' and i + 1 < n:
                output.append(text[i + 1])
                i += 2
                continue
            if ch == '"':
                in_string = False
            i += 1
            continue

        if ch == '"':
            in_string = True
            output.append(ch)
            i += 1
            continue

        if ch == '/' and nxt == '/':
            line_comment = True
            output.append(' ')
            modified = True
            i += 2
            continue

        if ch == '/' and nxt == '*':
            block_comment = True
            output.append(' ')
            modified = True
            i += 2
            continue

        # Trailing comma immediately before a closing bracket or brace.
        if ch == ',':
            j = i + 1
            while j < n and text[j] in ' \t\r\n':
                j += 1
            if j < n and text[j] in ']}':
                modified = True
                i += 1
                continue

        output.append(ch)
        i += 1

    return ''.join(output), modified

def _system_prefers_dark()->bool:
    """Best-effort detection of the OS dark-mode preference."""
    if sys.platform == 'win32':
        return _windows_prefers_dark()
    if sys.platform.startswith('linux'):
        return _linux_prefers_dark()
    return False

def _windows_prefers_dark()->bool:
    """Detect Windows dark mode via the registry."""
    try:
        import ctypes
        key = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        handle = ctypes.windll.advapi32.RegOpenKeyExW
        query = ctypes.windll.advapi32.RegGetValueW

        HKEY_CURRENT_USER = 0x80000001
        KEY_READ = 0x20019
        phkey = ctypes.c_void_p()
        if handle(HKEY_CURRENT_USER, key, 0, KEY_READ, ctypes.byref(phkey)) != 0:
            return False
        try:
            value = ctypes.c_uint32()
            size = ctypes.c_uint32(4)
            result = query(phkey, None, "AppsUseLightTheme", 0, None, ctypes.byref(value), ctypes.byref(size))
            if result == 0:
                return value.value == 0
        finally:
            ctypes.windll.advapi32.RegCloseKey(phkey)
    except Exception:
        return False
    return False

def _linux_prefers_dark()->bool:
    """Detect GNOME dark mode via gsettings (best-effort)."""
    try:
        import subprocess
        result = subprocess.run(['gsettings', 'get', 'org.gnome.desktop.interface', 'color-scheme'],capture_output=True, text=True, timeout=2)
        return 'prefer-dark' in result.stdout.lower()
    except Exception:
        return False

class ScrollableFrame(ttk.Frame):
    """A vertically scrollable frame hosting the form content."""

    def __init__(self, master)->None:
        super().__init__(master)
        self.canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0)
        self.vsb = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)

        self.vsb.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)

        self.inner = ttk.Frame(self.canvas)
        self._window = self.canvas.create_window((0, 0), window=self.inner, anchor='nw')

        self.inner.bind( '<Configure>',lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>',lambda e: self.canvas.itemconfigure(self._window, width=e.width))

        # Mouse wheel scrolling (Windows <MouseWheel>; Linux <Button-4/5>).
        self.canvas.bind('<MouseWheel>', self._on_mousewheel)
        self.canvas.bind('<Button-4>', lambda _e: self.canvas.yview_scroll(-3, 'units'))
        self.canvas.bind('<Button-5>', lambda _e: self.canvas.yview_scroll(3, 'units'))

    def _on_mousewheel(self, event)->None:
        # Windows reports delta in multiples of 120 per notch; macOS/Linux
        # report small per-event deltas.
        delta = event.delta
        if sys.platform == 'win32':
            delta = delta // 120
        self.canvas.yview_scroll(-delta * 3, 'units')

    def set_bg(self, color)->None:
        self.canvas.configure(background=color)

class App:

    def __init__(self, root, file_path=None)->None:

        self.root = root
        self.file_path = file_path
        self.current_value = None
        self.parse_error = None
        self.form_widget = None
        self._status_after_id = None
        self.sanitized_jsonc = False

        self.colors = theme.DARK if _system_prefers_dark() else theme.LIGHT
        self.style = ttk.Style(root)

        self._build_ui()
        self.apply_theme()

        if file_path:
            self.load_file(file_path)
        else:
            self._show_empty('No file open. Use File > Open (Ctrl+O) to load a JSON file.')

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self)->None:
        self.root.title('%s' % __title__)
        self.root.geometry('900x700')
        self.root.minsize(500, 400)
        self._build_menu()
        self._build_toolbar()

        self.scroll = ScrollableFrame(self.root)
        self.scroll.pack(fill='both', expand=True, padx=8, pady=(0, 4))

        self.empty_label = ttk.Label(self.scroll.inner,text='',justify='left')
        self.empty_label.pack(anchor='nw', pady=8)

        self.status = ttk.Label(self.root, text='', anchor='w')
        self.status.pack(side='bottom', fill='x', padx=8, pady=(2, 4))

        self.root.bind('<Control-o>', lambda _e: self.open_dialog())
        self.root.bind('<Control-s>', lambda _e: self.save())

    def _build_menu(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label='Open...', accelerator='Ctrl+O', command=self.open_dialog)
        file_menu.add_command(label='Save', accelerator='Ctrl+S', command=self.save)
        file_menu.add_separator()
        file_menu.add_command(label='Exit', command=self.root.destroy)
        menubar.add_cascade(label='File', menu=file_menu)

        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label='Expand All', command=lambda: self.set_all_collapsed(False))
        view_menu.add_command(label='Collapse All', command=lambda: self.set_all_collapsed(True))
        view_menu.add_separator()
        view_menu.add_command(label='Toggle Theme', command=self.toggle_theme)
        menubar.add_cascade(label='View', menu=view_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(
            label='About',
            command=lambda: messagebox.showinfo(
                __title__,
                '%s v%s\n\nRender and edit JSON files as a form.\nPackaged with PyInstaller.'
                % (__title__, __version__),
            ),
        )
        menubar.add_cascade(label='Help', menu=help_menu)
        self.root.configure(menu=menubar)

    def _build_toolbar(self)->None:
        bar = ttk.Frame(self.root, style='Panel.TFrame')
        bar.pack(side='top', fill='x')
        ttk.Button(bar, text='Open', command=self.open_dialog).pack(side='left', padx=(6, 2), pady=4)
        ttk.Button(bar, text='Save', command=self.save).pack(side='left', padx=2, pady=4)
        ttk.Button(bar, text='Expand All', command=lambda: self.set_all_collapsed(False)).pack(side='left', padx=2, pady=4)
        ttk.Button(bar, text='Collapse All', command=lambda: self.set_all_collapsed(True)).pack(side='left', padx=2, pady=4)
        self.theme_button = ttk.Button(bar, text='Dark', command=self.toggle_theme)
        self.theme_button.pack(side='right', padx=(2, 6), pady=4)

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def apply_theme(self)->None:
        theme.apply_theme(self.root, self.style, self.colors)
        self.scroll.set_bg(self.colors['bg'])
        self.theme_button.configure(text='Light' if self.colors is theme.DARK else 'Dark')
        self.empty_label.configure(foreground=self.colors['status_fg'])

    def toggle_theme(self)->None:
        self.colors = theme.LIGHT if self.colors is theme.DARK else theme.DARK
        self.apply_theme()
        # Re-render to apply type-badge colors.
        if self.current_value is not None and self.parse_error is None:
            self._render(self.current_value)

    # ------------------------------------------------------------------
    # File IO
    # ------------------------------------------------------------------

    def open_dialog(self)->None:
        path = filedialog.askopenfilename(title='Open JSON file',filetypes=[('JSON files', '*.json'), ('All files', '*.*')])
        if path:
            self.load_file(path)

    def load_file(self, path)->None:
        try:
            with open(path, 'r', encoding='utf-8') as handle:
                text = handle.read()
        except OSError as err:
            self._show_empty('Could not open file:\n%s' % err)
            return

        self.file_path = path
        self.root.title('%s - %s' % (__title__, os.path.basename(path)))

        if not text.strip():
            value = None
            self.sanitized_jsonc = False
        else:
            try:
                value = json.loads(text)
                self.sanitized_jsonc = False
            except json.JSONDecodeError:
                sanitized, modified = sanitize_jsonc(text)
                try:
                    value = json.loads(sanitized)
                    self.sanitized_jsonc = modified
                except json.JSONDecodeError as err:
                    self.parse_error = err
                    self.current_value = None
                    self._show_empty('Invalid JSON:\n%s' % err)
                    return

        self.parse_error = None
        self._render(value)
        if self.sanitized_jsonc:
            self.set_status('Loaded %s (JSONC: comments/trailing commas removed for editing)' % path)
        else:
            self.set_status('Loaded %s' % path)

    def _render(self, value)->None:
        self._clear_form()
        self.current_value = value
        if value is None:
            self._show_empty('Empty document - nothing to display.')
            return
        self._hide_empty()
        self.form_widget = renderer.build_form(self.scroll.inner, value, self.colors)
        self.form_widget.pack(fill='both', expand=True)

    def save(self)->None:
        if self.parse_error is not None:
            self.set_status('Cannot save: JSON is invalid.', error=True)
            return
        if self.form_widget is None:
            self.set_status('Nothing to save.', error=True)
            return

        value = self.form_widget.get_value()
        text = json.dumps(value, indent=2, ensure_ascii=False) + '\n'

        path = self.file_path
        if not path:
            path = filedialog.asksaveasfilename(title='Save JSON file',defaultextension='.json',filetypes=[('JSON files', '*.json'), ('All files', '*.*')])
            if not path:
                return
            self.file_path = path
            self.root.title('%s - %s' % (__title__, os.path.basename(path)))

        try:
            with open(path, 'w', encoding='utf-8') as handle:
                handle.write(text)
        except OSError as err:
            self.set_status('Save failed: %s' % err, error=True)
            return
        if self.sanitized_jsonc:
            self.set_status('Saved %s (comments/trailing commas removed)' % path)
        else:
            self.set_status('Saved %s' % path)

    # ------------------------------------------------------------------
    # Form control
    # ------------------------------------------------------------------

    def set_all_collapsed(self, collapsed)->None:
        if self.form_widget is None:
            return
        for widget in renderer.walk_collapsibles(self.form_widget):
            widget.set_expanded(not collapsed)

    def _clear_form(self)->None:
        if self.form_widget is not None:
            self.form_widget.destroy()
            self.form_widget = None

    def _show_empty(self, message):
        self._clear_form()
        self.empty_label.configure(text=message)
        self.empty_label.pack(anchor='nw', pady=8)

    def _hide_empty(self):
        self.empty_label.pack_forget()

    def set_status(self, message, error=False):
        if self._status_after_id is not None:
            self.root.after_cancel(self._status_after_id)
        self.status.configure(text=message,foreground=self.colors['error'] if error else self.colors['status_fg'])
        self._status_after_id = self.root.after(4000, self._clear_status)

    def _clear_status(self):
        self.status.configure(text='')
        self._status_after_id = None

def main():
    root = tk.Tk()
    path = sys.argv[1] if len(sys.argv) > 1 else None
    App(root, file_path=path)
    root.mainloop()

if __name__ == '__main__':
    main()
