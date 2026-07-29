import datetime
from zoneinfo import ZoneInfo


class Clock:
    def __init__(self, timezone_name, time_format, date_format):
        self.timezone = ZoneInfo(timezone_name)
        self.time_format = time_format
        self.date_format = date_format

    def now_utc(self):
        return datetime.datetime.now(datetime.timezone.utc)

    def iso_now(self):
        return self.now_utc().isoformat()

    def parse(self, value):
        if not value:
            return None
        parsed = datetime.datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=datetime.timezone.utc)
        return parsed.astimezone(datetime.timezone.utc)

    def display(self, value):
        if value.tzinfo is None:
            value = value.replace(tzinfo=datetime.timezone.utc)
        utc_value = value.astimezone(datetime.timezone.utc)
        local_value = utc_value.astimezone(self.timezone)
        age = self.now_utc() - utc_value
        if age.total_seconds() < 86400:
            return local_value.strftime(self.time_format)
        return local_value.strftime(self.date_format)


class SessionTracker:
    def __init__(self, store, clock):
        self.store = store
        self.clock = clock
        self.current_started_at = self.clock.iso_now()
        previous = self.store.read()
        self.previous_started_at = previous.get("started_at")
        self.store.write({"started_at": self.current_started_at})

    def scan_window(self):
        return (
            self.clock.parse(self.previous_started_at),
            self.clock.parse(self.current_started_at),
        )
