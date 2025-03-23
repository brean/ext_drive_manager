from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Label, ListItem, ListView, Header


class SelectAction(ModalScreen):
    CSS_PATH = 'select_action.tcss'

    def __init__(self, data):
        super().__init__()
        self.data = data

    def compose(self) -> ComposeResult:
        items = [ListItem(Label("Back"), id="back")]
        if not self.data[5]:
            items.append(ListItem(Label("Save drive/partition"), id='save'))
            items.append(ListItem(
                Label("Write drive/partition"),
                id='write', classes="warning"))
        else:
            items.append(ListItem(
                Label("Write drives"),
                id='write', classes="warning"))
        yield ListView(*items, id="dialog")

    def on_mount(self) -> None:
        self.query_one(ListView).border_title = self.data[0]

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.item.id == "back":
            self.app.pop_screen()
