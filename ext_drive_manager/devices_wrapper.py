import json
import subprocess


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
    return devices_info


if __name__ == "__main__":
    devices = get_device_info()
    print("Device Information:")
    for device in devices.get('blockdevices', []):
        if not device.get('rm'):
            continue
        print(
            f"Device: {device.get('kname', 'N/A')}, "
            f"Type: {device.get('type', 'N/A')}, "
            f"Removable: {device.get('rm', 'N/A')}, "
            f"Read-Only: {device.get('ro', 'N/A')}, "
            f"Size: {device.get('size', 'N/A')} bytes, "
            f"Mount Point: {device.get('mountpoint', 'N/A')}, "
            f"Label: {device.get('label', 'N/A')}, "
            f"Vendor: {device.get('vendor', 'N/A')}, "
            f"Model: {device.get('model', 'N/A')}")
