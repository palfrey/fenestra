import xcffib
import time
import os
import pathlib

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

def assemble_polybar():
    config = ""
    for f in sorted(pathlib.Path("polybar").iterdir()):
        config += f.read_text() + "\n\n"
    pathlib.Path("~/.config/polybar/config").expanduser().write_text(config)

def configure():
    for output in xr.get_connected_outputs():
        print(output.name, output.display.edid, output.crtc)
    assemble_polybar()

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