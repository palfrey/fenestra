import importlib
import os
import pathlib
import subprocess

from jinja2 import Template
from ppretty import ppretty


class Fenestra:
    def on_change(self):
        if not self.ready:
            return
        config = ""
        # print("Updating config", ppretty(self.config))
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
        supervisor_conf = pathlib.Path(
            "~/.config/supervisor/supervisor.conf"
        ).expanduser()
        supervisor_conf.write_text(
            Template(open("supervisor.conf.jinja").read()).render(
                config_folder=pathlib.Path("~/.config/supervisor").expanduser(),
                **self.config,
            )
        )
        subprocess.check_output(
            ["supervisorctl", "-c", supervisor_conf.absolute().as_posix(), "update"]
        )
        try:
            subprocess.check_output(
                [
                    "supervisorctl",
                    "-c",
                    supervisor_conf.absolute().as_posix(),
                    "start",
                    "all",
                ]
            )
        except subprocess.CalledProcessError as e:
            print(e.stdout, e.stderr)
            raise

    def __init__(self):
        self.plugins = {}
        self.config = {}
        self.ready = False

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

        self.ready = True
        self.on_change()

        for thread in threads:
            thread.join()


main = Fenestra()
main.run()
