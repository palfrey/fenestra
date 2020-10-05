from enum import Enum
import subprocess
from typing import Optional
import pyudev


class Keyboard(Enum):
    MAC = 1
    PC = 2


class Plugin:
    keyboard_state: Optional[Keyboard] = None

    def __init__(self, parent):
        self.parent = parent
        self.udev_context = pyudev.Context()
        self.set_keyboard_state()

    def set_keyboard_state(self):
        for device in self.udev_context.list_devices(subsystem="usb"):
            if (
                device.properties.get("ID_VENDOR_ID") == "05ac"
                and device.properties.get("ID_MODEL_ID") == "0250"
            ):
                # Matias keyboard
                if self.keyboard_state != Keyboard.MAC:
                    print("Setting keyboard state to Mac")
                    subprocess.check_call(
                        [
                            "setxkbmap",
                            "-model",
                            "macbook79",
                            "-layout",
                            "gb",
                            "-verbose",
                            "10",
                        ]
                    )
                    self.keyboard_state = Keyboard.MAC
                    self.parent.on_change()
                break
        else:
            if self.keyboard_state != Keyboard.PC:
                # Default laptop keyboard
                print("Setting keyboard state to PC")
                subprocess.check_call(
                    ["setxkbmap", "-model", "pc104", "-layout", "gb", "-verbose", "10"]
                )
                self.keyboard_state = Keyboard.PC
                self.parent.on_change()

    def log_usb_event(self, action, device):
        self.set_keyboard_state()

    def create(self):
        monitor = pyudev.Monitor.from_netlink(self.udev_context)
        monitor.filter_by("usb")
        observer = pyudev.MonitorObserver(monitor, self.log_usb_event)
        observer.start()
        return observer
