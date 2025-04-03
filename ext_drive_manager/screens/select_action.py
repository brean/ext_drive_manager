from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Label, ListItem, ListView, Header
from .select_partition import SelectPartition


class SelectAction(ModalScreen):
    CSS_PATH = 'select_action.tcss'

    def __init__(self, devices: list):
        super().__init__()
        self.devices = devices

    def compose(self) -> ComposeResult:
        items = [ListItem(Label("Back"), id="back")]
        if len(self.devices) == 1:
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
        num_dev = len(self.devices)
        if num_dev == 1:
            self.query_one(ListView).border_title = self.devices[0].name
        else:
            self.query_one(ListView).border_title = f'{num_dev} devices'

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self.app.pop_screen()
        if event.item.id == "save":
            # Show select partition dialog
            self.app.push_screen(SelectPartition(self.devices[0]))
