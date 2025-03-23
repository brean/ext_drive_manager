from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Grid
from textual.widgets import Button, Label


class SelectPartition(ModalScreen):
    CSS_PATH = 'select_partition.tcss'

    def compose(self) -> ComposeResult:
        yield Grid(
            Label('Question', id="question"),
            Button("Start", variant="warning", id="confirm"),
            Button("Cancel", variant="default", id="cancel"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.app.pop_screen()
