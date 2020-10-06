import difflib
import importlib
import os
import pathlib
import shutil
import subprocess
import sys
from pathlib import Path

from jinja2 import Template
from ppretty import ppretty


class Fenestra:
    def change_config(self, path: pathlib.Path, content: str):
        if path.exists():
            old_content = path.read_text()
            diff = difflib.unified_diff(old_content.splitlines(), content.splitlines())
            items = list(diff)
            if len(items) == 0:
                return
            print(f"Diff for {path} is")
            for item in items:
                print(item, end=None)
        path.write_text(content)

    def on_change(self):
        if not self.ready:
            return
        config = ""
        # print("Updating config", ppretty(self.config))
        for f in sorted(pathlib.Path("polybar").iterdir()):
            if f.name.startswith("."):
                continue
            if f.name.endswith(".ini"):
                config += f.read_text() + "\n\n"
            elif f.name.endswith(".ini.jinja"):
                template = Template(f.read_text())
                output = template.render(**self.config)
                config += output + "\n\n"
            else:
                raise Exception(f)

        self.change_config(
            pathlib.Path("~/.config/polybar/config").expanduser(), config
        )
        supervisor_conf = pathlib.Path(
            "~/.config/supervisor/supervisor.conf"
        ).expanduser()
        self.change_config(
            supervisor_conf,
            Template(open("supervisor.conf.jinja").read()).render(
                config_folder=pathlib.Path("~/.config/supervisor").expanduser(),
                **self.config,
            ),
        )

        script = sys.argv[0]
        self.change_config(
            pathlib.Path("~/.config/systemd/user/fenestra.service").expanduser(),
            Template(open("systemd.service.jinja").read()).render(
                script_path=script,
                python=shutil.which("python"),
                path=os.getenv("PATH"),
                script_folder=pathlib.Path(script).absolute().parent.as_posix(),
            ),
        )

        subprocess.run(
            ["supervisorctl", "-c", supervisor_conf.absolute().as_posix(), "update"]
        )
        subprocess.run(
            [
                "supervisorctl",
                "-c",
                supervisor_conf.absolute().as_posix(),
                "start",
                "all",
            ]
        )

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
