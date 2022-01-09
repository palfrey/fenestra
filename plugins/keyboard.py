import subprocess
from enum import Enum

from ._common import UdevPlugin


class Keyboard(Enum):
    MAC = 1
    PC = 2
    UNKNOWN = 3


class Plugin(UdevPlugin):
    keyboard_state: Keyboard = Keyboard.UNKNOWN

    def __init__(self, parent):
        UdevPlugin.__init__(self, parent, "usb")

    def setup(self):
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
                    try:
                        subprocess.check_output(
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
                    except subprocess.CalledProcessError as e:
                        print("Can't currently set keyboard as setxkbmap failed")
                        print(e.output)
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

    def log_event(self, action, device):
        self.set_keyboard_state()

    def on_change(self):
        self.set_keyboard_state()
