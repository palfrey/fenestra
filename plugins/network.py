import pyudev


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


class Plugin:
    def __init__(self, parent):
        self.parent = parent        
        self.udev_context = pyudev.Context()

    def log_net_event(self, action, device):
        self.devices = [DeviceWrapper(d) for d in self.udev_context.list_devices(subsystem="net")]
        self.parent.on_change()

    def create(self):
        self.log_net_event(None, None)
        monitor = pyudev.Monitor.from_netlink(self.udev_context)
        monitor.filter_by("net")
        observer = pyudev.MonitorObserver(monitor, self.log_net_event)
        observer.start()        
        return observer

if __name__ == "__main__":
    plugin = Plugin(None)
    thread = plugin.create()
    for d in plugin.devices:
        print(list(d.device.properties.items()))
    thread.join()
