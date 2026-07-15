import momoui as ui

label = ui.Label("Hello Momo")
button = ui.Button("Press me")


@button.on_click
def _pressed():
    label.text = "Clicked!"


ui.show(ui.Column([label, button]))

