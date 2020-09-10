from enum import Enum
import subprocess
from typing import List
from randrctl.model import XrandrConnection
import xcffib
import time
import pathlib
import pyudev
from jinja2 import Template

from randrctl.xrandr import Xrandr
import xcffib.randr as RandR
from xcffib.randr import NotifyMask, ScreenChangeNotifyEvent

xr = Xrandr(None, None)

def startup():
    """Hook up XCB_RANDR_NOTIFY_MASK_SCREEN_CHANGE"""
    # In the xcb.randr module, the result of
    # key = xcb.ExtensionKey('RANDR')
    # xcb._add_ext(key, randrExtension, _events, _errors)
    # is stored in xcb.randr.key and retrieved in some very odd manner =>
    randr = conn(RandR.key)
    randr.SelectInput(root.root, NotifyMask.ScreenChange | NotifyMask.OutputChange )
    # may as well flush()
    conn.flush()

def assemble_polybar(outputs: List[XrandrConnection]):
    config = ""
    for f in sorted(pathlib.Path("polybar").iterdir()):
        if f.name.endswith(".ini"):
            config += f.read_text() + "\n\n"
        elif f.name.endswith(".ini.jinja"):
            template = Template(f.read_text())
            output = template.render(outputs=outputs)
            config += output + "\n\n"
        else:
            raise Exception(f)
    pathlib.Path("~/.config/polybar/config").expanduser().write_text(config)
    pathlib.Path("~/.config/polybar/launch.sh").expanduser().write_text(Template(open("launch.sh.jinja").read()).render(outputs=outputs))

def configure():
    for output in xr.get_connected_outputs():
        print(output.name, output.display.edid, output.crtc)
    assemble_polybar(xr.get_connected_outputs())

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

udev_context = pyudev.Context()


class Keyboard(Enum):
    MAC = 1
    PC = 2

keyboard_state = None

def set_keyboard_state():
    global udev_context, keyboard_state
    for device in udev_context.list_devices(subsystem='usb'):
        if device.properties.get("ID_VENDOR_ID") == "05ac" and device.properties.get('ID_MODEL_ID') == "0250":
            # Matias keyboard
            if keyboard_state != Keyboard.MAC:
                print("Setting keyboard state to Mac")
                subprocess.check_call(["setxkbmap", "-model", "macbook79", "-layout", "gb", "-verbose", "10"])
                keyboard_state = Keyboard.MAC
            break
    else:
        if keyboard_state != Keyboard.PC:
            # Default laptop keyboard
            print("Setting keyboard state to PC")
            subprocess.check_call(["setxkbmap", "-layout", "gb", "-verbose", "10"])
            keyboard_state = Keyboard.PC

set_keyboard_state()

monitor = pyudev.Monitor.from_netlink(udev_context)
monitor.filter_by('usb')
def log_event(action, device):
    set_keyboard_state()

observer = pyudev.MonitorObserver(monitor, log_event)
observer.start()

conn = xcffib.connect()
setup = conn.get_setup()
# setup.roots holds a list of screens (just one in our case) #
root = setup.roots[0]

configure()
run()