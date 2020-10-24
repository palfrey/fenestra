from threading import Thread

import pyudev
from ppretty import ppretty


class PluginBase:
    def __init__(self, parent):
        self.parent = parent
        self._setup = False
        self.check_setup()

    @property
    def name(self):
        return self.__module__

    def check_setup(self):
        if self._setup:
            return True
        try:
            self.setup()
            print(f"Setup of {self.name} complete")
            self._setup = True
            return True
        except Exception as e:
            print(f"Error running setup for {self.name}")
            print(str(e))
            return False

    def setup(self):
        raise NotImplementedError

    def __str__(self):
        return ppretty(self)


class ThreadedPlugin(PluginBase, Thread):
    def __init__(self, parent):
        Thread.__init__(self)
        PluginBase.__init__(self, parent)

    def create(self):
        self.start()
        return self


class UdevPlugin(PluginBase):
    def __init__(self, parent, filter):
        self.udev_context = pyudev.Context()
        self.filter = filter
        PluginBase.__init__(self, parent)

    def log_event(self, action, device):
        raise NotImplementedError

    def create(self):
        self.log_event(None, None)
        monitor = pyudev.Monitor.from_netlink(self.udev_context)
        monitor.filter_by(self.filter)
        observer = pyudev.MonitorObserver(monitor, self.log_event)
        observer.start()
        return observer
