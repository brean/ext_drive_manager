import json
import subprocess
import shutil
from dataclasses import dataclass


def format_size(size_bytes: int):
    """Convert a size in bytes to a human-readable format."""
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
    index = 0
    while size_bytes >= 1024 and index < len(units) - 1:
        size_bytes /= 1024.0
        index += 1
    return f"{size_bytes:.2f}{units[index]}"


def is_external_drive(dev):
    return (
        # removeable or hotplug
        (dev.get('rm') or dev.get('hotplug')) and
        # ignore SD-card reader that show up as device but do not
        # have any card inserted, they show up with size 0
        # and we can't read/write devices with 0 size anyway
        dev.get('size', 0) > 0)


def get_used(dev):
    # We can only get used disk size from mounted devices.
    size = 0
    if dev.get('mountpoint'):
        _, used, _ = shutil.disk_usage(dev['mountpoint'])
        size += used
    if dev.get('children'):
        for child in dev['children']:
            size += get_used(child)
    return size


@dataclass
class Partition:
    kname: str = ''
    mountpoint: str = ''
    part: dict | None = None
    size: int = 0
    used: int = 0

    @property
    def size_str(self):
        return format_size(self.size)

    @property
    def used_str(self):
        return format_size(self.used)

    def __post_init__(self):
        self.kname = self.part.get('kname', '')
        self.mountpoint = self.part.get('mountpoint', '')
        self.size = self.part.get('size', 0)
        if self.mountpoint:
            _, used, _ = shutil.disk_usage(self.mountpoint)
            self.used = used


@dataclass
class Device:
    vendor: str = 'unknown'
    model: str = 'unknown'
    name: str = 'unknown drive'
    num: int = 0
    # size in byte
    size: int = 0
    used: int = 0
    paritions: list | None = None
    is_external_drive: bool = False
    # device instance
    dev: dict | None = None
    # Name of current action
    action: str = '(none)'
    # progress from 0-100
    progress: int = 0

    def __post_init__(self):
        self.update_dev()

    def update_dev(self):
        """update device information from json-data provided by lsblk."""
        dev = self.dev
        if not dev:
            return
        self.vendor = dev.get('vendor', self.vendor)
        self.model = dev.get('model', self.model)
        if self.vendor != 'unknown' or self.model != 'unknown':
            self.name = f"{self.vendor} {self.model}"
        else:
            self.name = f'drive #{self.num+1}'
        self.size = dev.get('size', 0)
        self.used = get_used(dev)
        if dev.get('children', None):
            self.partitions = [
                Partition(part=c) for c in dev['children']
                if c['type'] == 'part'
            ]
        self.is_external_drive = is_external_drive(dev)

    @property
    def partition_str(self):
        return str(len(self.partitions)) if self.partitions else '0'

    @property
    def size_str(self):
        return format_size(self.size)

    @property
    def used_str(self):
        return format_size(self.used)

    def start_backup(self, partition: str):
        pass


def get_device_info():
    try:
        # Run the lsblk command to get device information in JSON format
        # based on https://github.com/raspberrypi/rpi-imager/blob/qml/src/
        # linux/linuxdrivelist.cpp
        result = subprocess.run([
            'lsblk',
            '--exclude', '7', '--tree', '--paths', '--json', '--bytes',
            '--output', 'kname,type,subsystems,ro,rm,hotplug,size,'
            'phy-sec,log-sec,label,vendor,model,mountpoint'],
            capture_output=True, text=True, check=True
        )
        devices_info = json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running lsblk: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return []
    block_devices = devices_info.get('blockdevices', [])
    all_devices = [
        Device(dev=d, num=num) for num, d in enumerate(block_devices)]
    return [d for d in all_devices if d.is_external_drive]


def drives_to_table_data(devices):
    data = [(
        'Device name', 'Size', 'Used', 'Pa',
        'Action', 'Progress', 'Devices')]
    if len(devices) > 1:
        data.append((
            f'all {len(devices)} devices', '-', '-', '-',
            '-', sum([d.progress for d in devices]), devices))
    for dev in devices:
        data.append((
            dev.name, dev.size_str, dev.used_str, dev.partition_str,
            dev.action, dev.progress, [dev]))
    return data


if __name__ == "__main__":
    devices = get_device_info()
    print("Device Information:")
    for device in drives_to_table_data(devices):
        print(device)
