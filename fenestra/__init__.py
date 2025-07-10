import difflib
import importlib
import os
import pathlib
import shutil
import subprocess
import sys

from jinja2 import Template


class Fenestra:
    def change_config(self, path: pathlib.Path, content: str) -> bool:
        if path.exists():
            old_content = path.read_text()
            diff = difflib.unified_diff(old_content.splitlines(), content.splitlines())
            items = list(diff)
            if len(items) == 0:
                return False
            print(f"Diff for {path} is")
            for item in items:
                print(item, end=None)
        path.write_text(content)
        return True

    def on_change(self):
        if not self.ready:
            return
        config = ""
        # print("Updating config", ppretty(self.config))
        for f in sorted(pathlib.Path("polybar").iterdir()):
            if f.is_dir():
                continue
            elif f.name.startswith("."):
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

        script = sys.argv[0]

        services = {
            "fenestra": {
                "command": f"{shutil.which('python')} {script}",
                "service_config": {
                    "Environment": f"PATH={os.getenv('PATH')}",
                    "WorkingDirectory": pathlib.Path(script)
                    .absolute()
                    .parent.as_posix(),
                },
                "installs": {
                    "WantedBy": ["graphical.target"],
                },
                "unit_config": {
                    "Wants": [
                        f"{x}.service"
                        for x in [
                            "udiskie",
                            "blueman",
                            "albert",
                            "dropbox",
                            "redshift",
                            "feh",
                        ]
                    ]
                },
            },
            "udiskie": {
                "command": "/bin/udiskie --automount --notify --tray",
            },
            "blueman": {
                "command": "/bin/blueman-applet",
            },
            "albert": {
                "command": "/bin/albert",
            },
            "dropbox": {
                "command": "%h/.dropbox-dist/dropboxd",
                "service_config": {
                    "Type": "simple",
                    "Restart": "on-failure",
                    "RestartSec": 1,
                },
            },
            "feh": {
                "command": "feh --bg-max /home/palfrey/Dropbox/Tom/Photos/backgrounds/squirrels.jpg",
                "service_config": {"Type": "oneshot"},
            },
            "redshift": {"command": "redshift -l -0.14:51.33 -v -m randr"},
        }

        for output in self.config["screen"].outputs:
            name = f"polybar-{output.name}"
            services[name] = {"command": f"/bin/polybar --reload {output.name}"}
            services["fenestra"]["unit_config"]["Wants"].append(f"{name}.service")

        service_changed = False
        for name, data in services.items():
            if "service_config" not in data:
                data["service_config"] = {}
            if "unit_config" not in data:
                data["unit_config"] = {}
            if "installs" not in data:
                data["installs"] = {}
            service_changed = (
                self.change_config(
                    pathlib.Path(f"~/.config/systemd/user/{name}.service").expanduser(),
                    Template(open("systemd.service.jinja").read()).render(
                        description=name, **data
                    ),
                )
                or service_changed
            )
        if service_changed:
            subprocess.run(["systemctl", "--user", "daemon-reload"])

        for plugin in self.plugins.values():
            if hasattr(plugin, "on_change"):
                plugin.on_change()

    def __init__(self):
        self.plugins = {}
        self.config = {}
        self.ready = False

        for fname in pathlib.Path(__file__).parent.joinpath("plugins").glob("*.py"):
            base = fname.stem
            plugin = importlib.import_module(f"fenestra.plugins.{base}")
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
