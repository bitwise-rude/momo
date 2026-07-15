"""
momoui - Beginning of my own ui system for momo

The public API in `momoui.widgets` never touches JNI directly. It talks to
whatever backend module is available under the name `_backend`, and only
ever calls this 7-function surface for now:

    ui_create_label(text)                -> handle
    ui_create_button(text)               -> handle
    ui_create_layout(orientation)        -> handle   # "vertical" | "horizontal"
    ui_set_text(handle, text)
    ui_set_onclick(handle, callback)
    ui_add_view(parent_handle, child_handle)
    ui_show(handle)

For android look at glue.c for other systems I am yet to write :(
"""

import android as _backend  

from .widgets import Label, Button, Column, Row, show

__all__ = ["Label", "Button", "Column", "Row", "show"]
