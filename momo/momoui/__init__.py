"""
momoui — a small, platform-agnostic UI layer for Momo apps.

The public API in `momoui.widgets` never touches JNI directly. It talks to
whatever backend module is available under the name `_backend`, and only
ever calls this backend surface:

    ui_create_label(text)                -> handle
    ui_create_button(text)               -> handle
    ui_create_input(hint)                -> handle
    ui_create_layout(orientation)        -> handle   # "vertical" | "horizontal"
    ui_set_text(handle, text)
    ui_get_text(handle)                  -> text
    ui_set_text_size(handle, size_sp)
    ui_set_text_color(handle, color_str)
    ui_set_bg_color(handle, color_str)
    ui_set_onclick(handle, callback)
    ui_add_view(parent_handle, child_handle)
    ui_show(handle)

On Android this is the embedded `android` C extension (see native-lib.c).
To port momoui to a new platform, implement those functions against that
platform's native UI toolkit and point `_backend` at it — nothing in
widgets.py needs to change.
"""
import android as _backend  # the embedded C extension from native-lib.c

from .widgets import Label, Button, Input, Column, Row, show

__all__ = ["Label", "Button", "Input", "Column", "Row", "show"]
