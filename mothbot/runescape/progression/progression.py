import asyncio

from discord import Client
from mothtypes import UserCollection, User
from runescape.rstypes import RunescapeType, StatCollection, Stat
from typing import List

class ProgressManager:
    def __init__(self, user_collection: UserCollection, datapath_osrs: str, datapath_rs3: str):
        self.user_collection = UserCollection()
        self.datapath_osrs = datapath_osrs
        self.datapath_rs3 = datapath_rs3

    async def loop(self, client: Client, channel_id: int, interval_seconds: int = 60) -> None:
        await client.wait_until_ready()
        while not client.is_closed():
            out = list()
            for user in self.user_collection.runescapers[RunescapeType.OSRS]:
                old = StatCollection(f"{self.datapath_osrs}\\{user.name}.json")
                new = StatCollection(user.runescape.url)
                delta = new.delta(old)
                if not delta.empty:
                    out.append(delta.build_delta_string(old, str(user)))
                new.write(f"{self.datapath_osrs}\\{user.name}.json")

            if len(out):
                await client.get_channel(channel_id).send("\n\n".join(out))   
            await asyncio.sleep(interval_seconds)
