import subprocess

from ._common import UdevPlugin


class Plugin(UdevPlugin):
    def __init__(self, parent):
        UdevPlugin.__init__(self, parent, "usb")

    def setup(self):
        self.run_xrandr()

    def run_xrandr(self):
        subprocess.check_call(["xrandr", "--auto"])

    def log_event(self, action, device):
        self.run_xrandr()

    def on_change(self):
        self.run_xrandr()
