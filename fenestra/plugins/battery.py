from pathlib import Path

from ._common import UdevPlugin


class Plugin(UdevPlugin):
    def __init__(self, parent):
        UdevPlugin.__init__(self, parent, "power_supply")

    def setup(self):
        self.batteries: list[str] = []
        for power_supply in Path("/sys/class/power_supply").glob("BAT*"):
            self.batteries.append(power_supply.name)

    def log_event(self, action, device):
        print("battery", action, device)
