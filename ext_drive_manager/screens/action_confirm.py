from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Grid
from textual.widgets import Button, Label


class ActionConfirm(ModalScreen):
    CSS_PATH = 'action_confirm.tcss'

    def __init__(self, data):
        super().__init__()
        self.data = data

    def compose(self) -> ComposeResult:
        yield Grid(
            Label(self.data['question'], id="question"),
            Button(
                self.get('Confirm', 'confirm'),
                variant="warning", id="confirm"),
            Button(
                self.get('Cancel', 'cancel'),
                variant="default", id="cancel"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.app.pop_screen()
