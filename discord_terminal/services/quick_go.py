class QuickGoService:
    def __init__(self, client):
        self.client = client
        self.last_results = []

    def destinations(self):
        entries = []
        for guild in self.client.guilds:
            for channel in guild.text_channels:
                entries.append(
                    {
                        "label": "{} / #{}".format(guild.name, channel.name),
                        "search": "{} {} {}".format(
                            guild.name,
                            channel.name,
                            channel.id,
                        ).lower(),
                        "channel": channel,
                    }
                )
        for channel in self.client.private_channels:
            name = str(channel)
            recipient = getattr(channel, "recipient", None)
            username = getattr(recipient, "name", None)
            label = "DM / @{}".format(username or name)
            entries.append(
                {
                    "label": label,
                    "search": "{} {} {}".format(
                        label,
                        name,
                        channel.id,
                    ).lower(),
                    "channel": channel,
                }
            )
        return sorted(entries, key=lambda item: item["label"].lower())

    def search(self, query):
        entries = self.destinations()
        words = query.lower().split()
        if words:
            entries = [
                entry
                for entry in entries
                if all(word in entry["search"] for word in words)
            ]
        exact = [
            entry
            for entry in entries
            if entry["label"].lower() == query.lower()
        ]
        if exact:
            entries = exact
        self.last_results = entries[:20]
        return self.last_results

    def numbered(self, number):
        if number < 1 or number > len(self.last_results):
            return None
        return self.last_results[number - 1]

    async def go(self, entry):
        channel = entry["channel"]
        self.client.current_channel = channel
        self.client.current_guild = getattr(channel, "guild", None)
        self.client.history_offset = 0
        await self.client.refresh_history()
