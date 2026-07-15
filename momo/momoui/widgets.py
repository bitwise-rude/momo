from . import _backend


class Widget:
    """Base class for anything backed by a native widget handle."""
    def __init__(self, handle):
        self._handle = handle


class Label(Widget):
    def __init__(self, text=""):
        super().__init__(_backend.ui_create_label(text))
        self._text = text

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value
        _backend.ui_set_text(self._handle, value)


class Button(Widget):
    def __init__(self, text="", on_click=None):
        super().__init__(_backend.ui_create_button(text))
        self._text = text
        self._on_click = None
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

        Will mostly be used as a decorator?

            button = ui.Button("Go")

            @button.on_click
            def _pressed():
                ...
        """
        self._on_click = fn
        _backend.ui_set_onclick(self._handle, fn)
        return fn


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
