import asyncio
import os
import re
from datetime import datetime
from time import time, strftime

from discord import Client, Message

class RemindMeManager:
    def __init__(self, client: Client, path_to_tracking: str):
        self.client = client
        self.path_to_tracking = path_to_tracking

    async def new_tracker(self, message: Message):
        msg_spl = [x.strip() for x in message.content.split(" ") if x]
        if len(msg_spl) >= 2:
            syntax = msg_spl[1]
            if re.search(r"^\d{2}:\d{2}$", syntax):
                H, M = (int(x) for x in syntax.split(":"))
                if 0 <= H <= 23 and 0 <= M <= 59:
                    with open(f"{self.path_to_tracking}\\{message.author.id}.{message.channel.id}", "w") as fptr:
                        fptr.write(syntax)
                    await message.channel.send(f"Torkan sind {syntax}")
                    return
            elif re.search(r"^\d+[ms]$", syntax):
                time_units = int(syntax[:-1])
                multiplier = 60 if syntax[-1] == "m" else 1
                future = int(time() + time_units * multiplier)
                with open(f"{self.path_to_tracking}\\{message.author.id}.{message.channel.id}", "w") as fptr:
                    fptr.write(str(future))
                await message.channel.send(f"Torkan sind {syntax} pärast")
                return

        out = ["remindme [süntaks]"]
        out.append("võimalikud süntaksid:")
        out.append("H:M - näiteks 16:30 või 05:00 - torkab sind sellel kellaajal")
        out.append("(number)s - näiteks 50s või 120s - torkab sind kui nii mitu sekundit on möödunud")
        out.append("(number)m - näiteks 50m või 120m - torkab sind kui nii mitu minutit on möödunud")
        await message.channel.send("\n".join(out))

    async def end_tracker(self, filename: str):
        user_id, channel_id = (int(x) for x in filename.split("."))
        user = self.client.get_user(user_id)
        channel = self.client.get_channel(channel_id)
        for _ in range(3):
            await channel.send(user.mention)
        os.remove(f"{self.path_to_tracking}\\{filename}")

    async def loop(self):
        await self.client.wait_until_ready()
        while not self.client.is_closed():
            for filename in os.listdir(self.path_to_tracking):
                with open(f"{self.path_to_tracking}\\{filename}", "r") as fptr:
                    contents = fptr.read()
                if re.search(r"^\d{2}:\d{2}$", contents):
                    current_H, current_M = (int(x) for x in strftime("%H:%M").split(":"))
                    future_H, future_M = (int(x) for x in contents.split(":"))
                    if future_H <= current_H and future_M <= current_M:
                        await self.end_tracker(filename)
                else:
                    future_ctime = int(contents)
                    now_ctime = time()
                    if future_ctime <= now_ctime:
                        await self.end_tracker(filename)
            await asyncio.sleep(1)
