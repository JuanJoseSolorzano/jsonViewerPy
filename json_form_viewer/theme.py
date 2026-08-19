#================================================================
#Light and dark theme definitions for the JSON Form Viewer GUI.
# Author: Juan Jose Solorzano / deepseek-v4-pro
#================================================================

import tkinter.font as tkfont

LIGHT = {
    'name': 'Light',
    'bg': '#ffffff',
    'fg': '#1f1f1f',
    'panel': '#f3f3f3',
    'button_bg': '#e5e5e5',
    'hover': '#d4d4d4',
    'entry_bg': '#ffffff',
    'entry_fg': '#1f1f1f',
    'border': '#c8c8c8',
    'key': '#0451a5',
    'accent': '#0066b8',
    'string': '#a31515',
    'number': '#098658',
    'boolean': '#0000ff',
    'null': '#767676',
    'status_fg': '#767676',
    'error': '#e51400',
}

DARK = {
    'name': 'Dark',
    'bg': '#1e1e1e',
    'fg': '#d4d4d4',
    'panel': '#252526',
    'button_bg': '#3c3c3c',
    'hover': '#4a4a4a',
    'entry_bg': '#3c3c3c',
    'entry_fg': '#cccccc',
    'border': '#3c3c3c',
    'key': '#9cdcfe',
    'accent': '#0e639c',
    'string': '#ce9178',
    'number': '#b5cea8',
    'boolean': '#569cd6',
    'null': '#808080',
    'status_fg': '#808080',
    'error': '#f14c4c',
}

THEMES = {'light': LIGHT, 'dark': DARK}

def _section_title_font(root):
    """Pick a cross-platform font for section titles."""
    preferred = [
        'Segoe UI',      # Windows 11
        'Noto Sans',     # Debian (GNOME)
        'DejaVu Sans',   # Debian (generic)
        'Cantarell',     # Debian (GNOME)
        'Helvetica',     # macOS
    ]
    available = set(tkfont.families(root))
    for name in preferred:
        if name in available:
            return (name, 9, 'bold')
    return ('TkDefaultFont', 9, 'bold')


def apply_theme(root, style, colors):
    """Apply the given color palette to the root window and ttk styles."""
    try:
        style.theme_use('clam')
    except Exception:
        pass

    c = colors
    root.configure(bg=c['bg'])

    style.configure('.', background=c['bg'], foreground=c['fg'])
    style.configure('TFrame', background=c['bg'])
    style.configure('TLabel', background=c['bg'], foreground=c['fg'])

    # Toolbar / panels
    style.configure('Panel.TFrame', background=c['panel'])
    style.configure('Toolbar.TLabel', background=c['panel'], foreground=c['fg'])

    # Section headers
    style.configure(
        'SectionTitle.TLabel',
        background=c['bg'],
        foreground=c['accent'],
        font=_section_title_font(root),
    )
    style.configure(
        'Key.TLabel',
        background=c['bg'],
        foreground=c['key'],
    )
    style.configure('Type.TLabel', background=c['bg'], padding=(4, 1))
    style.configure('Index.TLabel', background=c['bg'], foreground=c['status_fg'])

    # Buttons
    style.configure(
        'TButton',
        background=c['button_bg'],
        foreground=c['fg'],
        borderwidth=0,
        focusthickness=0,
        padding=(8, 3),
    )
    style.map(
        'TButton',
        background=[('active', c['hover']), ('pressed', c['hover'])],
    )
    style.configure('Toggle.TButton', padding=(4, 0), width=2)
    style.configure(
        'Add.TButton',
        background=c['button_bg'],
        foreground=c['accent'],
    )
    style.map(
        'Add.TButton',
        background=[('active', c['hover']), ('pressed', c['hover'])],
    )
    style.configure(
        'Danger.TButton',
        background=c['button_bg'],
        foreground=c['error'],
        padding=(4, 0),
    )
    style.map(
        'Danger.TButton',
        background=[('active', c['hover']), ('pressed', c['hover'])],
    )

    # Entries
    style.configure(
        'TEntry',
        fieldbackground=c['entry_bg'],
        foreground=c['entry_fg'],
        insertcolor=c['fg'],
        bordercolor=c['border'],
    )
