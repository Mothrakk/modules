from mothtypes import User
from discord import Client, TextChannel

class Table:
    def __init__(self, client: Client, channel_id: int):
        self.client = client
        self.channel_id = channel_id

    async def send(self, msg: str) -> None:
        await self.channel.send(msg)

    async def send_dm(self, user: User, msg: str) -> None:
        user = self.client.get_user(user.id)
        await user.send(msg)

    @property
    def channel(self) -> TextChannel:
        return self.client.get_channel(self.channel_id)

