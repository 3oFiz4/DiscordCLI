import json
from copy import deepcopy
from pathlib import Path


class Configuration:
    def __init__(self, path):
        self.path = Path(path)
        with self.path.open("r", encoding="utf-8") as file:
            self.data = json.load(file)

    @property
    def command_key(self):
        return self.data["cmdKey"]

    @property
    def commands(self):
        return self.data["commands"]

    @property
    def settings(self):
        return self.data["settings"]

    @property
    def events(self):
        return self.data["events"]

    @property
    def theme(self):
        from rich.theme import Theme

        return Theme(self.data["pallete"])

    def command(self, name):
        return self.commands.get(name, {})

    def aliases(self, name):
        return self.command(name).get("aliases", [])

    def log(self, command, name):
        return self.command(command).get("logs", {}).get(name, "")

    def get(self, *keys, default=None):
        current = self.data
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return default
            current = current[key]
        return current

    def clone(self):
        return deepcopy(self.data)

    def save(self):
        content = json.dumps(self.data, indent=2, ensure_ascii=False)
        self.path.write_text(content + "\n", encoding="utf-8")
