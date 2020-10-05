import subprocess
import time
from threading import Thread
from typing import List

import xcffib
import xcffib.randr as RandR
from randrctl.model import XrandrConnection
from randrctl.xrandr import Xrandr
from xcffib.randr import NotifyMask


class Plugin(Thread):
    outputs: List[XrandrConnection]

    def __init__(self, parent):
        Thread.__init__(self)
        self.parent = parent
        self.xr = Xrandr(None, None)
        self.conn = xcffib.connect()
        setup = self.conn.get_setup()
        # setup.roots holds a list of screens (just one in our case) #
        self.root = setup.roots[0]
        """Hook up XCB_RANDR_NOTIFY_MASK_SCREEN_CHANGE"""
        # In the xcb.randr module, the result of
        # key = xcb.ExtensionKey('RANDR')
        # xcb._add_ext(key, randrExtension, _events, _errors)
        # is stored in xcb.randr.key and retrieved in some very odd manner =>
        randr = self.conn(RandR.key)
        randr.SelectInput(
            self.root.root, NotifyMask.ScreenChange | NotifyMask.OutputChange
        )
        # may as well flush()
        self.conn.flush()

    def create(self):
        self.start()
        return self

    def run(self):
        self.on_screen_change()
        while True:
            try:
                event = self.conn.poll_for_event()
                if event == None:
                    time.sleep(1)
                    continue
            except xcffib.ProtocolException as error:
                print("Protocol error %s received!" % error.__class__.__name__)
                break
            except Exception as error:
                print("Unexpected error received: %s" % error.message)
                break

            self.on_screen_change()

    def on_screen_change(self):
        self.outputs = self.xr.get_connected_outputs()
        subprocess.check_output(["randrctl", "auto"])
        self.parent.on_change()


if __name__ == "__main__":

    class Parent:
        def on_change(self):
            pass

    plugin = Plugin(Parent())
    thread = plugin.create()
    for o in plugin.outputs:
        print(o)
    thread.join()
