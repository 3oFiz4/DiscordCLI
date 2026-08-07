import json
from pathlib import Path


class JsonStore:
    def __init__(self, path, default):
        self.path = Path(path)
        self.default = default
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def read(self):
        if not self.path.exists():
            return self._fresh_default()
        try:
            with self.path.open("r", encoding="utf-8") as file:
                return json.load(file)
        except (OSError, ValueError):
            return self._fresh_default()

    def write(self, value):
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        with temporary.open("w", encoding="utf-8") as file:
            json.dump(value, file, ensure_ascii=False, indent=2)
        temporary.replace(self.path)

    def _fresh_default(self):
        if isinstance(self.default, dict):
            return dict(self.default)
        if isinstance(self.default, list):
            return list(self.default)
        return self.default


class RecordStore:
    def __init__(self, path, key):
        self.store = JsonStore(path, {key: []})
        self.key = key

    def all(self):
        return self.store.read().get(self.key, [])

    def replace(self, records):
        self.store.write({self.key: records})

    def append_unique(self, record, unique_key):
        records = self.all()
        value = str(record.get(unique_key))
        if any(str(item.get(unique_key)) == value for item in records):
            return False
        records.append(record)
        self.replace(records)
        return True

    def remove_at(self, index):
        records = self.all()
        if index < 0 or index >= len(records):
            return False
        records.pop(index)
        self.replace(records)
        return True

    def clear(self):
        self.replace([])

