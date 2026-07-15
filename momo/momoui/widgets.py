from . import _backend


class Widget:
    """Base class for anything backed by a native widget handle."""

    def __init__(self, handle):
        self._handle = handle

    @property
    def bg_color(self):
        """Write-only in practice — we don't read colors back from the
        platform, just remember what was last set so it can be inspected
        from Python if needed."""
        return getattr(self, "_bg_color", None)

    @bg_color.setter
    def bg_color(self, value):
        _backend.ui_set_bg_color(self._handle, value)
        self._bg_color = value


class TextStyleMixin:
    """Shared font styling for any widget whose native view is a TextView
    (or subclass — Button and EditText both qualify). Mix this in alongside
    Widget; it assumes self._handle is already set.
    """

    @property
    def font_size(self):
        return getattr(self, "_font_size", None)

    @font_size.setter
    def font_size(self, sp):
        _backend.ui_set_text_size(self._handle, float(sp))
        self._font_size = sp

    @property
    def text_color(self):
        return getattr(self, "_text_color", None)

    @text_color.setter
    def text_color(self, value):
        _backend.ui_set_text_color(self._handle, value)
        self._text_color = value


class Label(Widget, TextStyleMixin):
    def __init__(self, text="", font_size=None, text_color=None):
        super().__init__(_backend.ui_create_label(text))
        self._text = text
        if font_size is not None:
            self.font_size = font_size
        if text_color is not None:
            self.text_color = text_color

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value
        _backend.ui_set_text(self._handle, value)


class Button(Widget, TextStyleMixin):
    def __init__(self, text="", on_click=None, font_size=None, text_color=None):
        super().__init__(_backend.ui_create_button(text))
        self._text = text
        self._on_click = None
        if font_size is not None:
            self.font_size = font_size
        if text_color is not None:
            self.text_color = text_color
        if on_click is not None:
            self.on_click(on_click)

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value
        _backend.ui_set_text(self._handle, value)

    def on_click(self, fn):
        """Register a zero-argument callable as the click handler.

        Can also be used as a decorator:
            button = ui.Button("Go")
            @button.on_click
            def _pressed():
                ...
        """
        self._on_click = fn
        _backend.ui_set_onclick(self._handle, fn)
        return fn


class Input(Widget, TextStyleMixin):
    """A single-line text field (backed by android.widget.EditText).

    `hint` is the greyed-out placeholder shown when empty. `text` is the
    actual editable content — read it after the user types to get what
    they entered.
    """

    def __init__(self, hint="", text="", font_size=None, text_color=None):
        super().__init__(_backend.ui_create_input(hint))
        self._hint = hint
        if text:
            _backend.ui_set_text(self._handle, text)
        if font_size is not None:
            self.font_size = font_size
        if text_color is not None:
            self.text_color = text_color

    @property
    def text(self):
        return _backend.ui_get_text(self._handle)

    @text.setter
    def text(self, value):
        _backend.ui_set_text(self._handle, value)

    @property
    def hint(self):
        return self._hint


class Container(Widget):
    def __init__(self, orientation, children=None):
        super().__init__(_backend.ui_create_layout(orientation))
        self._children = []
        for child in (children or []):
            self.add(child)

    def add(self, widget):
        _backend.ui_add_view(self._handle, widget._handle)
        self._children.append(widget)
        return self


class Column(Container):
    """Stacks children top to bottom."""

    def __init__(self, children=None):
        super().__init__("vertical", children)


class Row(Container):
    """Lays out children left to right."""

    def __init__(self, children=None):
        super().__init__("horizontal", children)


def show(root):
    """Make `root` (usually a Column/Row, but any widget works) the screen's content."""
    _backend.ui_show(root._handle)
