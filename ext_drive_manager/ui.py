from textual.app import App, ComposeResult
from textual.containers import HorizontalGroup
from textual.widgets import Header, Label, ListItem, ListView, ProgressBar

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

    def __init__(self, data):
        super().__init__()
        self.data = data

    def compose(self) -> ComposeResult:
        """Entry for one drive."""
        yield HorizontalGroup(
            Label(self.data[0], id="drive_name"),
            Label(self.data[1], id="size"),
            Label(self.data[2], id="partition"),
            Label(self.data[3], id="action"),
            ProgressBar(total=100, show_eta=False, id="progress"),
        )

    def update_progress(self) -> None:
        self.query_one(ProgressBar).update(progress=self.data[4])


def drives_to_table_data(devices):
    data = [('Device name', 'Size', 'Partitions', 'Action', 'Progress')]
    data.append(('all devices', '', '', '(none)', 0))
    for dev in devices.get('blockdevices', []):
        if not dev.get('rm'):
            continue
        if dev.get('size', 0) == 0:
            continue
        name = f"{dev['vendor']} {dev['model']}"
        size = ''
        if dev.get('size', 0) > 0:
            size = f" {format_size(dev['size'])}"
        part = '0'
        if dev.get('children', None):
            part = str(len([
                c for c in dev.get('children')
                if c['type'] == 'part']))
        data.append((name, size, part, '(none)', 0))
    return data


class ExternalDriveManager(App):
    CSS_PATH = 'ui.tcss'
    """A Textual app to manage external drives like SD-cards or USB-Sticks."""

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield ListView()

    def on_mount(self) -> None:
        devices = get_device_info()
        data = drives_to_table_data(devices)

        list_view = self.query_one(ListView)
        # list_view.append(DriveListHeader(data[0]))
        for row in data[1:]:
            list_view.append(DriveItem(row))


def main():
    app = ExternalDriveManager()
    app.run()


if __name__ == "__main__":
    main()
