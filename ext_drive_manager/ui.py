from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import HorizontalGroup
from textual.widgets import \
    Header, Label, ListItem, ListView, ProgressBar, Footer

from .devices_wrapper import get_device_info, drives_to_table_data
from .screens.select_action import SelectAction


class ListHeader(ListItem):
    def __init__(self, data):
        super().__init__(disabled=True)
        self.data = data
        self.drive_select = True

    def compose(self) -> ComposeResult:
        """Entry for one drive."""
        yield HorizontalGroup(
            Label(self.data[0], id="drive_name"),
            Label(self.data[1], id="size"),
            Label(self.data[2], id="used"),
            Label(self.data[3], id="partition"),
            Label(self.data[4], id="action"),
            Label(self.data[5], id="progress"),
        )


class DriveItem(ListItem):

    def __init__(self, data):
        super().__init__()
        self.data = data
        self.drives = self.data[6]
        self.drive_select = True

    def compose(self) -> ComposeResult:
        """Entry for one drive."""
        yield HorizontalGroup(
            Label(self.data[0], id="drive_name"),
            Label(self.data[1], id="size"),
            Label(self.data[2], id="used"),
            Label(self.data[3], id="partition"),
            Label(self.data[4], id="action"),
            ProgressBar(total=100, show_eta=False, id="progress"),
        )

    def update_progress(self) -> None:
        self.query_one(ProgressBar).update(progress=self.data[4])


class ExternalDriveManager(App):
    MODES = {
        "select_action": SelectAction,
    }
    CSS_PATH = 'ui.tcss'
    BINDINGS = [
        Binding(key="q", action="quit", description="Quit the app"),
    ]
    """A Textual app to manage external drives like SD-cards or USB-Sticks."""

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield ListView()
        yield Footer()

    def on_mount(self) -> None:
        devices = get_device_info()
        data = drives_to_table_data(devices)

        list_view = self.query_one(ListView)
        # list_view.append(DriveListHeader(data[0]))
        list_view.append(ListHeader(data[0]))
        for row in data[1:]:
            list_view.append(DriveItem(row))
        list_view.index = 1

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if hasattr(event.item, 'drive_select'):
            self.push_screen(SelectAction(event.item.drives))


def main():
    app = ExternalDriveManager()
    app.run()


if __name__ == "__main__":
    main()
