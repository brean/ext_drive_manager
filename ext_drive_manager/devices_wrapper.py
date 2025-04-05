import json
import subprocess
import shutil
import signal
import time
from dataclasses import dataclass


SYNC = shutil.which('sync')
DD_PATH = shutil.which('dd')
LSBLK_PATH = shutil.which('lsblk')
UDISKCTRL = shutil.which('udisksctl')


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
        mount = dev['mountpoint']
        if not mount.startswith('/dev') and '[SWAP]' != mount:
            _, used, _ = shutil.disk_usage(mount)
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
        if self.mountpoint and self.mountpoint != '[SWAP]':
            _, used, _ = shutil.disk_usage(self.mountpoint)
            self.used = used


@dataclass
class Device:
    # kernel name, e.g. sdX or nvmeX
    kname: str = ''
    vendor: str = 'unknown'
    model: str = 'unknown'
    # Human readable Vendor and Model name or number
    name: str = 'unknown drive'
    # number of the device
    num: int = 0
    # full device size in byte
    size: int = 0
    # used space on device in byte
    used: int = 0
    partitions: list | None = None
    # if the device is removable and hotplugable and has a size bigger than 0
    is_external_drive: bool = False
    # File system type e.g. vfat or ext4
    fs_type: str | None = None
    # device instance
    dev: dict | None = None
    # Name of current action
    action: str = '(idle)'
    # progress from 0-100
    progress: int = 0

    def __post_init__(self):
        self.update_dev()

    def update_dev(self):
        """update device information from json-data provided by lsblk."""
        dev = self.dev
        if not dev:
            return
        self.kname = dev['kname']
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

    def finish_task(self):
        self.action = '(idle)'
        self.progress = 0

    def unmount(self):
        subprocess.run(
            [SYNC], check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)
        self.action = 'unmount'
        self.progress = 0
        for part in self.partitions:
            if not part.mountpoint or part.mountpoint == '':
                continue
            cmd = [UDISKCTRL, 'unmount', '-b', part.kname,]
            subprocess.run(
                cmd, check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL)
        self.finish_task()

    def start_backup(self, partition: Partition, out_file: str, bs=2048):
        cmd = [
            DD_PATH, f"if={partition['kname']}", f"of={out_file}", f"bs={bs}",
            "status=progress"]
        dd = subprocess.Popen(cmd, stderr=subprocess.PIPE)
        line = ''
        self.action = 'dd'
        while dd.poll() is None:
            # this should run in a thread btw
            time.sleep(.33333)
            dd.send_signal(signal.SIGUSR1)
            if dd.returncode:
                _, err = dd.communicate()
                # probably "Permission denied"
                if err:
                    print(err.decode('utf-8')[:-1])
                self.finish_task()
                return
            while True:
                read_line = dd.stderr.readline()
                if not read_line:
                    break
                line = read_line.decode('utf-8')
                if 'bytes' in line:
                    progress = int(line.split(' ')[0])
                    print(progress)
                    break
        # DONE!
        self.finish_task()


def get_device_info():
    try:
        # Run the lsblk command to get device information in JSON format
        # based on https://github.com/raspberrypi/rpi-imager/blob/qml/src/
        # linux/linuxdrivelist.cpp
        result = subprocess.run([
            LSBLK_PATH,
            '--exclude', '7', '--tree', '--paths', '--json', '--bytes',
            '--output', 'name,kname,type,subsystems,ro,rm,hotplug,size,'
            'phy-sec,log-sec,label,vendor,model,mountpoint,fstype'],
            capture_output=True, text=True, check=True
        )
        devices_info = json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running lsblk: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return []
    block_devices = []
    for device in devices_info.get('blockdevices', []):
        if not device.get('mountpoint'):
            block_devices.append(device)
        elif device['mountpoint'] != '[SWAP]':
            block_devices.append(device)
    print('x'*20)
    for d in block_devices:
        print(d['kname'], d['mountpoint'])
    print('*'*20)
    all_devices = [
        Device(dev=d, num=num) for num, d in enumerate(block_devices)]
    return [d for d in all_devices if d.is_external_drive]


def drives_to_table_data(devices: list):
    """create a table from device list."""
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
    _devices = get_device_info()
    print("Device Information:")
    for _device in drives_to_table_data(_devices):
        print(_device)
