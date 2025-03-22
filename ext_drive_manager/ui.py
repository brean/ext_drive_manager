from textual.app import App, ComposeResult
from textual.containers import HorizontalGroup
from textual.widgets import Header, Label, ListView, ListItem, ProgressBar
from .devices_wrapper import get_device_info


def format_size(size_bytes: int):
    """Convert a size in bytes to a human-readable format."""
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
    index = 0
    while size_bytes >= 1024 and index < len(units) - 1:
        size_bytes /= 1024.0
        index += 1
    return f"{size_bytes:.2f} {units[index]}"


class DriveItem(ListItem):
    def __init__(self, dev):
        super().__init__()
        self.dev = dev

    def compose(self) -> ComposeResult:
        """Entry for one drive."""
        lbl = f"{self.dev['vendor']} {self.dev['model']} "
        if self.dev.get('size', 0) > 0:
            lbl += f"({format_size(self.dev['size'])}) "
        part = 0
        if self.dev.get('children', None):
            part = len([
                c for c in self.dev.get('children')
                if c['type'] == 'part'])
        yield HorizontalGroup(
            Label(lbl, id="drive_name"),
            Label(f'{part} partitions', id="num_parts"),
            ProgressBar(total=100, show_eta=False),
            
        )

    def update_progress(self, progress) -> None:
        self.query_one(ProgressBar).update(progress=progress)


class ExternalDriveManager(App):
    """A Textual app to manage external drives like SD-cards or USB-Sticks."""

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        drive_list = [DriveItem({'vendor': 'all', 'model': 'devices'})]
        devices = get_device_info()
        for dev in devices.get('blockdevices', []):
            if not dev.get('rm'):
                continue
            if dev.get('size', 0) == 0:
                continue
            drive_list.append(DriveItem(dev))
        yield ListView(*drive_list)


def main():
    app = ExternalDriveManager()
    app.run()


if __name__ == "__main__":
    main()
