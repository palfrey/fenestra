import os
import importlib
import pathlib

from jinja2 import Template


class Fenestra:
    def on_change(self):
        config = ""
        print(self.config)
        for f in sorted(pathlib.Path("polybar").iterdir()):
            if f.name.endswith(".ini"):
                config += f.read_text() + "\n\n"
            elif f.name.endswith(".ini.jinja"):
                template = Template(f.read_text())
                output = template.render(**self.config)
                config += output + "\n\n"
            else:
                raise Exception(f)
        pathlib.Path("~/.config/polybar/config").expanduser().write_text(config)
        pathlib.Path("~/.config/supervisor/supervisor.conf").expanduser().write_text(
            Template(open("supervisor.conf.jinja").read()).render(
                config_folder=pathlib.Path("~/.config/supervisor").expanduser(),
                **self.config
            )
        )
    
    def __init__(self):
        self.plugins = {}
        self.config = {}

        for fname in os.listdir("plugins"):
            base, ext = os.path.splitext(fname)
            if ext != ".py":
                continue
            plugin = importlib.import_module(f"plugins.{base}")
            if "Plugin" in dir(plugin):
                self.plugins[base] = plugin
    
    def run(self):
        threads = []
        for name, plugin in self.plugins.items():
            print(f"Running {plugin}")
            instance = plugin.Plugin(self)
            self.config[name] = instance
            threads.append(instance.create())
        
        for thread in threads:
            thread.join()
        
main = Fenestra()
main.run()