
import momoui as ui

title = ui.Label("This is a test momo program", font_size=28, text_color="#0FF0FF")

name_input = ui.Input(hint="Enter your name", font_size=18, text_color="#FFFFFF")

greeting = ui.Label("", font_size=20, text_color="#FCAF50")

button = ui.Button("Greet me", font_size=18, text_color="#FFFFFF")
button.bg_color = "#2196F3"


@button.on_click
def _pressed():
    name = name_input.text.strip()
    greeting.text = f"Hi, {name}!" if name else "Type your name first!"


root = ui.Column([title, name_input, button, greeting])
root.bg_color = "#111111"

ui.show(root)

