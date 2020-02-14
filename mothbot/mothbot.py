# https://discordpy.readthedocs.io/en/latest/#documentation-contents

from sys import argv, path
path.append("\\".join(argv[0].split("\\")[:-2]))

import discord
import requests
import asyncio
import json
import re
import random
import os
import traceback
import math

import PyBoiler
from TTS import TTS
from runescape.lootsim.lootsim import LootSimManager
from markov.markov_handler import MarkovHandler
from mothtypes import UserCollection, Channel
from runescape.progression.progression import ProgressManager

class Reactable:
    def __init__(self,
                 returnable: str,
                 re_pattern: str = "",
                 must_not_contain: list = []):
        self.returnable = returnable
        self.re_pattern = re_pattern
        self.must_not_contain = must_not_contain

    def __str__(self) -> str:
        return self.returnable

    def match(self, to_test: str) -> str:
        if self.re_pattern and not re.search(self.re_pattern, to_test):
            return False
        if any((x in to_test for x in self.must_not_contain)):
            return False
        return True

my = PyBoiler.Boilerplate()

if not os.path.exists(my.m_path("token.txt")):
    print("Missing token. Place token into the 'token.txt' file.")
    exit(-1)

client = discord.Client()

macros = {
    "bruh.mp4":"https://www.youtube.com/watch?v=2ZIpFytCSVc",
    "amazin":"https://youtu.be/hC6CZKkEh4A",
    "true": """True and yeah that's pretty true that's true and yeah that's true that's true that's true that's pretty true that's pretty true I mean that's true yeah that's true that's true that's fucking true amm that's how it is dude"""
}

reactables = [
    Reactable(":COOM:675430755350085706", r"c[ou]{2,}m")
]

class MothBot:
    def __init__(self):
        self.user_collection = UserCollection()
        PyBoiler.Log("Building Markov chains").to_larva()
        self.markov_handler = MarkovHandler(my.m_path("markov"))
        PyBoiler.Log("Building lootsim handler").to_larva()
        self.lootsim_handler = LootSimManager(my.m_path("runescape\\lootsim\\lootsim_data"))
        PyBoiler.Log("Building progress manager").to_larva()
        self.progress_manager = ProgressManager(self.user_collection,
                                                my.m_path("runescape\\data\\osrs"),
                                                my.m_path("runescape\\data\\rs3"))
        self.cmds = {
            "eval":self.evaluate,
            "imiteeri":self.markov_generate,
            "tts":self.tts,
            "lootsim":self.lootsim,
            "jututuba":self.chatroom_change_interval
        }
        self.logging = True
    
    async def handle_message(self, message) -> None:
        first_word = message.content.split(" ")[0].lower()

        for r in reactables:
            if r.match(message.content.lower()):
                await message.add_reaction(str(r))
        
        if message.content in macros:
            await message.channel.send(macros[message.content])
        elif first_word in self.cmds:
            await self.handle_command(first_word, message)
        else:
            for fname in os.listdir(my.m_path("macros")):
                if message.content == fname.split(".")[0]:
                    await message.channel.send(file=discord.File(my.m_path(f"macros\\{fname}")))
                    break
    
    async def handle_command(self, cmd: str, message) -> bool:
        try:
            await self.cmds[cmd](message)
        except:
            error_msg = f"```\n{traceback.format_exc()}\n```"
            await message.channel.send(error_msg)

        if self.logging:
            PyBoiler.Log(f"{message.author.name}: {message.content}").to_larva()

    async def evaluate(self, message):
        if message.author.id in self.user_collection.can_evaluate:
            r = eval(" ".join(message.content.split(" ")[1:]))
        else:
            r = "Ei :)"
        await message.channel.send(r)

    async def markov_generate(self, message):
        spl = message.content.split(" ")
        if len(spl) < 2:
            await message.channel.send(self.markov_handler.err_msg)
        else:
            count = int(spl[2]) if len(spl) > 2 and spl[2].isnumeric() else 1
            results = self.markov_handler.generate_sentences(spl[1], count, True)
            await message.channel.send("\n".join(results))

    async def tts(self, message):
        tts = TTS(message, my.m_path("temp.wav"))
        await tts.work()

    async def lootsim(self, message):
        messages_to_send = self.lootsim_handler.handle(message)
        for m in messages_to_send:
            await message.channel.send(m)
    
    async def chatroom_change_interval(self, message):
        msg_split = message.content.split(" ")
        if len(msg_split) >= 2:
            arg = msg_split[1]
            if re.search(r"^\d+,\d+$", arg):
                x, y = (int(x) for x in arg.split(","))
                if 2 <= y <= 600 and 1 <= x < y:
                    with open(my.m_path("markov\\interval.txt"), "w") as fptr:
                        fptr.write(f"{x},{y}")
                    await message.channel.send(f"intervall nüüd {x}-{y}")
                    return
        await message.channel.send("jututuba x,y -- säti intervall sekundites, kus 2 <= y <= 600 ja 1 <= x < y")              

mothbot = MothBot()

@client.event
async def on_ready():
    PyBoiler.Log("online").to_larva()

@client.event
async def on_message(message):
    if message.channel.id == Channel.Send_To_Grupiteraapia:
        await client.get_channel(Channel.Grupiteraapia).send(message.content)
    elif message.author.id != client.user.id:
        await mothbot.handle_message(message)


with open(my.m_path("token.txt"), "r") as fptr:
    token = fptr.read().strip()

try:
    client.loop.create_task(mothbot.progress_manager.loop(client, Channel.Grupiteraapia))
    client.loop.create_task(mothbot.markov_handler.chatroom_loop(client, Channel.Jututuba))
    client.run(token)
except discord.errors.LoginFailure:
    print("Connection to the Discord API was disrupted. Bad token?")
