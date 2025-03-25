import json
import subprocess
import shutil


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
    return devices_info.get('blockdevices', [])


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


def drives_to_table_data(devices):
    data = [(
        'Device name', 'Size', 'Used', 'Pa',
        'Action', 'Progress', 'All')]
    data.append(('all devices', '-', '-', '-', '(none)', 0, True))
    for num, dev in enumerate(devices):
        if not is_external_drive(dev):
            continue
        vendor = None
        model = None
        if dev['vendor']:
            vendor = dev['vendor']
        if dev['model']:
            model = dev['model']
        if vendor or model:
            name = f"{vendor} {model}"
        else:
            name = f'drive #{num+1}'
        size = ''
        if dev.get('size', 0) > 0:
            size = format_size(dev['size'])
        size = format_size(1024*1023.87)
        used = format_size(get_used(dev))
        part = '0'
        if dev.get('children', None):
            part = str(len([
                c for c in dev.get('children')
                if c['type'] == 'part']))
        data.append((name, size, used, part, '(none)', 0, False))
    return data


if __name__ == "__main__":
    devices = get_device_info()
    print("Device Information:")
    for device in drives_to_table_data(devices):
        print(device)
