import difflib
import importlib
import os
import pathlib
import shutil
import subprocess
import sys
from typing import cast

from jinja2 import Template

current_directory = pathlib.Path(__file__).parent

command_cache: dict[str, str] = {}


def find_command(name: str) -> str:
    if name not in command_cache:
        output = shutil.which(name)
        assert output is not None
        command_cache[name] = output

    return command_cache[name]


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
        for f in sorted(current_directory.joinpath("polybar").iterdir()):
            if f.is_dir():
                continue
            elif f.name.startswith("."):
                continue
            if f.name.endswith(".ini"):
                config += f.read_text() + "\n\n"
            elif f.name.endswith(".ini.jinja"):
                template = Template(f.read_text())
                output = template.render(**self.config)
                assert output is not None
                config += output + "\n\n"
            else:
                raise Exception(f)

        polybar_config_folder = pathlib.Path("~/.config/polybar").expanduser()
        polybar_config_folder.mkdir(exist_ok=True)
        self.change_config(polybar_config_folder.joinpath("config.ini"), config)

        script = sys.argv[0]

        services = {
            "fenestra": {
                "command": f"{find_command('python')} {script}",
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
                            "dropbox",
                            "redshift",
                            "feh",
                        ]
                    ]
                },
            },
            "udiskie": {
                "command": find_command("udiskie") + " --automount --notify --tray",
            },
            "blueman": {
                "command": find_command("blueman-applet"),
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
                "command": find_command("feh")
                + " --bg-max /home/palfrey/Dropbox/Tom/Photos/backgrounds/squirrels.jpg",
                "service_config": {"Type": "oneshot"},
            },
            "redshift": {
                "command": find_command("redshift") + " -l -0.14:51.33 -v -m randr"
            },
        }

        for output in self.config["screen"].outputs:
            name = f"polybar-{output.name}"
            services[name] = {
                "command": f"{find_command('polybar')} --reload {output.name}"
            }
            services["fenestra"]["unit_config"]["Wants"].append(f"{name}.service")

        service_changed = False
        for name, data in services.items():
            if "service_config" not in data:
                data["service_config"] = {}
            if "unit_config" not in data:
                data["unit_config"] = {}
            if "installs" not in data:
                data["installs"] = {}
            with current_directory.joinpath(
                "systemd.service.jinja"
            ).open() as service_template:
                service_changed = (
                    self.change_config(
                        pathlib.Path(
                            f"~/.config/systemd/user/{name}.service"
                        ).expanduser(),
                        cast(
                            str,
                            Template(service_template.read()).render(
                                description=name, **data
                            ),
                        ),
                    )
                    or service_changed
                )
        if service_changed:
            subprocess.run([find_command("systemctl"), "--user", "daemon-reload"])

        for plugin in self.plugins.values():
            if hasattr(plugin, "on_change"):
                plugin.on_change()

    def __init__(self):
        self.plugins = {}
        self.config = {"script_folder": current_directory.as_posix()}
        self.ready = False

        for fname in current_directory.joinpath("plugins").glob("*.py"):
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


def start():
    main = Fenestra()
    main.run()
