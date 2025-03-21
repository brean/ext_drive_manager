from textual.app import App, ComposeResult
from textual.containers import HorizontalGroup
from textual.widgets import Button, Header, Label, ListView, ListItem
from .devices_wrapper import get_device_info


class DriveItem(ListItem):
    def __init__(self, dev):
        super().__init__()
        self.dev = dev

    """Entries for one drive."""
    def compose(self) -> ComposeResult:
        """Create child widgets of a stopwatch."""
        yield Label(
            f"{self.dev['vendor']} {self.dev['model']}",
            id="overwrite")


class ExternalDriveManager(App):
    """A Textual app to manage external drives like SD-cards or USB-Sticks."""

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        drive_list = []
        devices = get_device_info()
        for dev in devices.get('blockdevices', []):
            if not dev.get('rm'):
                continue
            drive_list.append(DriveItem(dev))
        yield ListView(*drive_list)


def main():
    app = ExternalDriveManager()
    app.run()


if __name__ == "__main__":
    main()
