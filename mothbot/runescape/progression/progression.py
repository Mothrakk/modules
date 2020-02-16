import asyncio

from discord import Client
from mothtypes import UserCollection, User
from runescape.rstypes import RunescapeType, StatCollection, Stat, ActivityFeed
from typing import List

class ProgressManager:
    def __init__(self, user_collection: UserCollection, datapath_osrs: str, datapath_rs3: str):
        self.user_collection = user_collection
        self.datapath_osrs = datapath_osrs
        self.datapath_rs3 = datapath_rs3

    def check_osrs_progress(self) -> List[str]:
        out = list()
        for user in self.user_collection.runescapers[RunescapeType.OSRS]:
            old = StatCollection(f"{self.datapath_osrs}\\{user.name}.json")
            new = StatCollection(user.runescape.url)
            delta = new.delta(old)
            if not delta.empty:
                out.append(delta.build_delta_string(old, str(user)))
                new.write(f"{self.datapath_osrs}\\{user.name}.json")
        return out

    def check_rs3_progress(self) -> List[str]:
        out = list()
        for user in self.user_collection.runescapers[RunescapeType.RS3]:
            old = ActivityFeed(f"{self.datapath_rs3}\\{user.name}.txt")
            new = ActivityFeed(user.runescape.url)
            delta = new.difference(old)
            if not delta.empty():
                out.append(delta.to_string(user.prefix))
                new.write(f"{self.datapath_rs3}\\{user.name}.txt")
        return out

    async def loop(self, client: Client, channel_id: int, interval_seconds: int = 60) -> None:
        await client.wait_until_ready()
        while not client.is_closed():
            out = self.check_osrs_progress() + self.check_rs3_progress()
            if len(out):
                await client.get_channel(channel_id).send("\n\n".join(out))   
            await asyncio.sleep(interval_seconds)
