from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import HorizontalGroup
from textual.widgets import \
    Header, Label, ListItem, ListView, ProgressBar, Footer

from .devices_wrapper import get_device_info, drives_to_table_data
from .screens.select_action import SelectAction

from textual.css.query import NoMatches

class ListHeader(ListItem):
    def __init__(self):
        super().__init__(disabled=True)
        self.drive_select = True

    def compose(self) -> ComposeResult:
        """Entry for one drive."""
        yield HorizontalGroup(
            Label('Device name', id="drive_name"),
            Label('Size', id="size"),
            Label('Used', id="used"),
            Label('Pa', id="partition"),
            Label('Action', id="action"),
            Label('Progress', id="progress"),
        )


class DriveItem(ListItem):

    def __init__(self, drives):
        super().__init__()
        self.drives = drives
        self.drive_select = True

    def compose(self) -> ComposeResult:
        """Entry for one drive."""
        if len(self.drives) == 1:
            dev = self.drives[0]
            yield HorizontalGroup(
                Label(dev.name, id="drive_name"),
                Label(dev.size_str, id="size"),
                Label(dev.used_str, id="used"),
                Label(str(len(dev.partitions)), id="partition"),
                Label(dev.action, id="action"),
                ProgressBar(total=100, show_eta=False, id="progress"),
            )
        else:
            num = len(self.drives)
            yield HorizontalGroup(
                Label(f'all {num} devices', id="drive_name"),
                Label('-', id="size"),
                Label('-', id="used"),
                Label('-', id="partition"),
                Label('-', id="action"),
                Label('-', id="progress"),
            )

    def update_progress(self) -> None:
        if len(self.drives) == 1:
            dev = self.drives[0]
            self.query_one(ProgressBar).update(progress=dev.progress)


class ExternalDriveManager(App):
    MODES = {
        "select_action": SelectAction,
    }
    CSS_PATH = 'ui.tcss'
    BINDINGS = [
        Binding(key="q", action="quit", description="Quit"),
        Binding(key="u", action="unmount()", description="sync and Unmount")
    ]
    """A Textual app to manage external drives like SD-cards or USB-Sticks."""
    def __init__(self):
        super().__init__()
        self.drives = []

    def action_unmount(self) -> None:
        try:
            list_view = self.query_one("#dev_list")
        except NoMatches:
            return
        if not list_view.index or list_view.index <= 0:
            self.notify(
                'No Device selected',
                title='Unmount failed',
                severity='warning')
            return
        index = 0 if len(self.drives) == 1 else list_view.index - 1
        if len(self.drives) > 1 and index == 0:
            # unomunt all drives
            for drive in self.drives:
                drive.unmount()
            self.notify(
                'All drives unmounted',
                title='Success',
                severity='information')
        else:
            drive = self.drives[index]
            drive.unmount()
            self.notify(
                f'{drive.name} ({drive.kname}) unmounted',
                title='Success',
                severity='information')

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield ListView(id="dev_list")
        yield Footer()

    def update_devices(self) -> None:
        try:
            list_view = self.query_one("#dev_list")
        except NoMatches:
            return
        drives = get_device_info()

        if drives == self.drives:
            return
        list_view.clear()
        if len(drives) == 0:
            return
        list_view.append(ListHeader())
        if len(drives) > 1:
            list_view.append(DriveItem(drives))
        for dev in drives:
            list_view.append(DriveItem([dev]))
        list_view.index = 1
        self.drives = drives

    def on_mount(self) -> None:
        self.update_devices()
        self.set_interval(1, self.update_devices)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if hasattr(event.item, 'drive_select'):
            self.push_screen(SelectAction(event.item.drives))


def main():
    app = ExternalDriveManager()
    app.run()


if __name__ == "__main__":
    main()
