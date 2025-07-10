from ._common import UdevPlugin


class DeviceWrapper:
    def __init__(self, device):
        self.device = device

    def __getitem__(self, name):
        if name in self.device.properties:
            return self.device.properties[name]
        elif name in dir(self.device):
            return getattr(self.device, name)
        else:
            raise KeyError


class Plugin(UdevPlugin):
    def __init__(self, parent):
        UdevPlugin.__init__(self, parent, "net")

    def setup(self):
        pass

    def log_event(self, action, device):
        self.devices = [
            DeviceWrapper(d) for d in self.udev_context.list_devices(subsystem="net")
        ]
        self.parent.on_change()


if __name__ == "__main__":

    class Parent:
        def on_change(self):
            pass

    plugin = Plugin(Parent())
    thread = plugin.create()
    for d in plugin.devices:
        print(list(d.device.properties.items()))
    print(plugin)
    thread.join()
