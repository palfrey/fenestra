from enum import Enum
import subprocess
from typing import List, Optional
from randrctl.model import XrandrConnection
import xcffib
import time
import pathlib
import pyudev
from jinja2 import Template

from randrctl.xrandr import Xrandr
import xcffib.randr as RandR
from xcffib.randr import NotifyMask

xr = Xrandr(None, None)


def startup():
    """Hook up XCB_RANDR_NOTIFY_MASK_SCREEN_CHANGE"""
    # In the xcb.randr module, the result of
    # key = xcb.ExtensionKey('RANDR')
    # xcb._add_ext(key, randrExtension, _events, _errors)
    # is stored in xcb.randr.key and retrieved in some very odd manner =>
    randr = conn(RandR.key)
    randr.SelectInput(root.root, NotifyMask.ScreenChange | NotifyMask.OutputChange)
    # may as well flush()
    conn.flush()


class Keyboard(Enum):
    MAC = 1
    PC = 2


class Info:
    outputs: List[XrandrConnection]
    keyboard_state: Optional[Keyboard] = None

    def __init__(self):
        self.udev_context = pyudev.Context()

    def assemble_configs(self):
        config = ""
        for f in sorted(pathlib.Path("polybar").iterdir()):
            if f.name.endswith(".ini"):
                config += f.read_text() + "\n\n"
            elif f.name.endswith(".ini.jinja"):
                template = Template(f.read_text())
                output = template.render(outputs=self.outputs)
                config += output + "\n\n"
            else:
                raise Exception(f)
        pathlib.Path("~/.config/polybar/config").expanduser().write_text(config)
        pathlib.Path("~/.config/supervisor/supervisor.conf").expanduser().write_text(
            Template(open("supervisor.conf.jinja").read()).render(
                config_folder=pathlib.Path("~/.config/supervisor").expanduser(),
                outputs=self.outputs,
            )
        )

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
                    keyboard_state = Keyboard.MAC
                break
        else:
            if self.keyboard_state != Keyboard.PC:
                # Default laptop keyboard
                print("Setting keyboard state to PC")
                subprocess.check_call(
                    ["setxkbmap", "-model", "pc104", "-layout", "gb", "-verbose", "10"]
                )
                self.keyboard_state = Keyboard.PC

    def update_outputs(self):
        self.outputs = xr.get_connected_outputs()

    def log_event(action, device):
        info.set_keyboard_state()
        info.assemble_configs()

    def listen_usb(self):
        usb_monitor = pyudev.Monitor.from_netlink(self.udev_context)
        usb_monitor.filter_by("usb")
        observer = pyudev.MonitorObserver(usb_monitor, self.log_event)
        observer.start()


info = Info()


def configure():
    info.update_outputs()
    info.assemble_configs()


def run():
    startup()

    while True:
        try:
            event = conn.poll_for_event()
            if event == None:
                time.sleep(1)
                continue
        except xcffib.ProtocolException as error:
            print("Protocol error %s received!" % error.__class__.__name__)
            break
        except Exception as error:
            print("Unexpected error received: %s" % error.message)
            break

        configure()


info.set_keyboard_state()
info.listen_usb()

conn = xcffib.connect()
setup = conn.get_setup()
# setup.roots holds a list of screens (just one in our case) #
root = setup.roots[0]

configure()
run()
