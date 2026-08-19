#=================================================================================
# Form widgets: recursively build an editable GUI from a JSON value.
# 
# This mirrors the logic of the original VS Code extension's WebView frontend,
# but implemented with Tkinter/ttk widgets instead of HTML.
# 
# Widget classes:
#   - PrimitiveField: editable input with a live type badge.
#   - ObjectEditor:   collapsible section of labeled fields.
#   - ArrayEditor:    collapsible section of repeatable items.
#=================================================================================

import re
import tkinter as tk
from tkinter import ttk
from . import theme

# Matches the JSON number grammar (keeps int vs float distinct).
_NUMBER_RE = re.compile(r'^-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?$')

# Type badge foreground colors.
_TYPE_COLORS = {
    'string': 'string',
    'number': 'number',
    'boolean': 'boolean',
    'null': 'null',
}

# ---------------------------------------------------------------------------
# Type helpers
# ---------------------------------------------------------------------------

def json_type(value):
    """Return the JSON type name of a Python value."""
    if value is None:
        return 'null'
    if isinstance(value, bool):
        return 'boolean'
    if isinstance(value, (int, float)):
        return 'number'
    if isinstance(value, list):
        return 'array'
    if isinstance(value, dict):
        return 'object'
    return 'string'

def literal_text(value, type_):
    """Return the canonical literal representation for a value."""
    if type_ == 'null':
        return 'null'
    if type_ == 'boolean':
        return 'true' if value else 'false'
    return str(value)

def detect_typed_value(text):
    """Auto-detect the type of a user-entered string.

    Returns a (type, value) tuple, coercing:
      'true'  -> ('boolean', True)
      'false' -> ('boolean', False)
      'null'  -> ('null', None)
      '123'   -> ('number', 123)
      '1.5'   -> ('number', 1.5)
      else    -> ('string', text)
    """
    trimmed = text.strip()
    if trimmed == 'true':
        return 'boolean', True
    if trimmed == 'false':
        return 'boolean', False
    if trimmed == 'null':
        return 'null', None
    if trimmed == '':
        return 'string', ''
    if _NUMBER_RE.match(trimmed):
        if '.' in trimmed or 'e' in trimmed or 'E' in trimmed:
            return 'number', float(trimmed)
        return 'number', int(trimmed)
    return 'string', text

def default_new_item(arr):
    """Pick a sensible default for a newly added array item."""
    if not arr:
        return None
    first = arr[0]
    if isinstance(first, list):
        return []
    if isinstance(first, dict):
        return {key: None for key in first}
    return first

# ---------------------------------------------------------------------------
# Widgets
# ---------------------------------------------------------------------------

class PrimitiveField(ttk.Frame):
    """Editable primitive value with a live type badge."""

    def __init__(self, master, value, colors)->None:
        super().__init__(master)
        self._colors = colors
        self.original_value = value
        self.original_type = json_type(value)
        self.original_text = literal_text(value, self.original_type)
        self._badge = ttk.Label(self, text=self.original_type, style='Type.TLabel')
        self._badge.pack(side='left', padx=(0, 6))
        self._entry = ttk.Entry(self)
        self._entry.insert(0, self.original_text)
        self._entry.pack(side='left', fill='x', expand=True)
        self._entry.bind('<KeyRelease>', self._on_change)
        self._refresh_badge(self.original_type)

    def _on_change(self, _event)->None:
        text = self._entry.get()
        if text == self.original_text:
            current_type = self.original_type
        else:
            current_type, _ = detect_typed_value(text)
        self._refresh_badge(current_type)

    def _refresh_badge(self, type_)->None:
        self._badge.configure(text=type_)
        color_key = _TYPE_COLORS.get(type_, 'null')
        self._badge.configure(foreground=self._colors[color_key])

    def get_value(self):
        text = self._entry.get()
        if text == self.original_text:
            return self.original_value
        _, value = detect_typed_value(text)
        return value

class _Collapsible(ttk.Frame):
    """Base widget providing a collapsible header + body."""

    def __init__(self, master, title, colors, extra=None)->None:
        super().__init__(master)
        self._colors = colors
        self._expanded = True
        header = ttk.Frame(self)
        header.pack(fill='x')
        self._toggle = ttk.Button(header,text='\u25be', style='Toggle.TButton', command=self._on_toggle)
        self._toggle.pack(side='left')
        title_label = ttk.Label(header, text=title, style='SectionTitle.TLabel')
        title_label.pack(side='left', padx=(4, 0))
        if extra is not None:
            extra.pack(side='left', padx=(10, 0))
        self.body = ttk.Frame(self)
        self.body.pack(fill='both', expand=True, padx=(16, 0))

    def _on_toggle(self)->None:
        self.set_expanded(not self._expanded)

    def set_expanded(self, expanded)->None:
        self._expanded = expanded
        if expanded:
            self.body.pack(fill='both', expand=True, padx=(16, 0))
            self._toggle.configure(text='\u25be')  # ▾
        else:
            self.body.pack_forget()
            self._toggle.configure(text='\u25b8')  # ▸

class ObjectEditor(_Collapsible):
    """Collapsible object rendered as labeled fields."""

    def __init__(self, master, obj, colors)->None:
        super().__init__(master, 'object', colors)
        self._fields = []
        for key, value in obj.items():
            self._add_field(key, value)

    def _add_field(self, key, value)->None:
        row = ttk.Frame(self.body)
        row.pack(fill='x', pady=1)
        key_label = ttk.Label(row, text=key, style='Key.TLabel', anchor='w')
        key_label.pack(side='left', anchor='n', padx=(0, 8), pady=2)
        widget = build_form(row, value, self._colors)
        widget.pack(side='left', fill='x', expand=True)
        self._fields.append((key, widget))

    def get_value(self)->dict:
        return {key: widget.get_value() for key, widget in self._fields}

class ArrayEditor(_Collapsible):
    """Collapsible array rendered as repeatable items."""

    def __init__(self, master, arr, colors)->None:
        self._items = []
        self._default = default_new_item(arr)
        add_button = ttk.Button(master, text='+ Add Item', style='Add.TButton', command=self._on_add)
        # Build the header with the extra add button embedded in it.
        super().__init__(master, 'array', colors, extra=add_button)

        for value in arr:
            self._add_item(value)

    def _on_add(self)->None:
        self._add_item(self._default)

    def _add_item(self, value)->None:
        item_frame = ttk.Frame(self.body)
        item_frame.pack(fill='x', pady=1)
        index = ttk.Label(item_frame, text='[0]', style='Index.TLabel', width=4, anchor='e')
        index.pack(side='left', padx=(0, 6), pady=2)
        widget = build_form(item_frame, value, self._colors)
        widget.pack(side='left', fill='x', expand=True)
        remove = ttk.Button(item_frame,text='\u2715',style='Danger.TButton',command=lambda f=item_frame: self._remove_item(f))
        remove.pack(side='left', padx=(6, 0))
        self._items.append((item_frame, index, widget))
        self._reindex()

    def _remove_item(self, frame)->None:
        frame.destroy()
        self._items = [t for t in self._items if t[0] is not frame]
        self._reindex()

    def _reindex(self)->None:
        for n, (_, index, _widget) in enumerate(self._items):
            index.configure(text='[%d]' % n)

    def get_value(self)->list:
        return [widget.get_value() for _, _, widget in self._items]

def build_form(parent, value, colors):
    """Build (and return) the appropriate form widget for a JSON value."""
    type_ = json_type(value)
    if type_ == 'array':
        return ArrayEditor(parent, value, colors)
    if type_ == 'object':
        return ObjectEditor(parent, value, colors)
    return PrimitiveField(parent, value, colors)

def walk_collapsibles(widget)->list:
    """Return every _Collapsible descendant of ``widget`` (incl. itself)."""
    result = []
    if isinstance(widget, _Collapsible):
        result.append(widget)
    for child in widget.winfo_children():
        result.extend(walk_collapsibles(child))
    return result