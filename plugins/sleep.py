from threading import Thread

from gi.repository import GLib
from pydbus import SystemBus


class Plugin(Thread):
    def handle_sleep(self, mode: bool):
        if mode:
            print("Sleep")
        else:
            print("Resume")
        self.parent.on_change()

    def __init__(self, parent):
        Thread.__init__(self)
        self.parent = parent
        self.bus = SystemBus()
        login_dev = self.bus.get(".login1")[".Manager"]
        login_dev.PrepareForSleep.connect(self.handle_sleep)

    def create(self):
        self.start()
        return self

    def run(self):
        GLib.MainLoop().run()


if __name__ == "__main__":

    class Parent:
        def on_change(self):
            pass

    plugin = Plugin(Parent())
    thread = plugin.create()
    thread.join()
