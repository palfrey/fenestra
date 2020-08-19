from typing import List
from randrctl.model import XrandrConnection
import xcffib
import time
import pathlib
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

conn = xcffib.connect()
setup = conn.get_setup()
# setup.roots holds a list of screens (just one in our case) #
root = setup.roots[0]

configure()
run()