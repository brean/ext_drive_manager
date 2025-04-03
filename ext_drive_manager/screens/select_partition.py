from textual.app import ComposeResult
from textual.containers import HorizontalGroup
from textual.screen import ModalScreen
from textual.widgets import \
    Label, ListItem, ListView

from ..devices_wrapper import Device


class ListHeader(ListItem):
    def __init__(self):
        super().__init__(disabled=True)
        self.drive_select = True

    def compose(self) -> ComposeResult:
        """Entry for one drive."""
        yield HorizontalGroup(
            Label('Partition', id="part_name"),
            Label('Mount Point', id="part_mountpoint"),
            Label('Size', id="part_size"),
            Label('Used', id="part_used")
        )


class ParitionItem(ListItem):
    def __init__(self, part, device):
        super().__init__()
        self.part = part
        self.device = device

    def compose(self) -> ComposeResult:
        """Entry for one partition."""
        if self.part:
            yield HorizontalGroup(
                Label(self.part.kname, id="part_name"),
                Label(self.part.mountpoint, id="part_mountpoint"),
                Label(self.part.size_str, id="part_size"),
                Label(self.part.used_str, id="part_used"),
            )
        else:
            yield HorizontalGroup(
                Label('All partitions', id="part_name"),
                Label('-', id="part_mountpoint"),
                Label(self.device.size_str, id="part_size"),
                Label(self.device.used_str, id="part_used")
            )


class SelectPartition(ModalScreen):
    CSS_PATH = 'select_partition.tcss'

    def __init__(self, device: Device):
        super().__init__()
        self.device = device

    def compose(self) -> ComposeResult:
        yield ListView(id="dialog")

    def on_mount(self) -> None:
        list_view = self.query_one(ListView)
        list_view.append(ListHeader())
        list_view.append(ParitionItem(None, self.device))
        for part in self.device.partitions:
            list_view.append(ParitionItem(part, None))
        list_view.index = 1
        list_view.border_title = f'Save partition from {self.device.name}'

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self.app.pop_screen()
        # kname = event.item.part.kname
        # TODO: open filename/folder selection dialog
        # TODO: generate .iso-file and yaml-config
