# https://discordpy.readthedocs.io/en/latest/#documentation-contents

import sys
boiler_path = "\\".join(sys.argv[0].split("\\")[:-2])
sys.path.append(boiler_path)

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
import TTS
from lootsim import lootsim
from markov import MarkovHandler
import hiscores_parsing

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
        if self.re_pattern and not re.findall(self.re_pattern, to_test):
            return False
        if any((x in to_test for x in self.must_not_contain)):
            return False
        return True

my = PyBoiler.Boilerplate()

client = discord.Client()

users = {
    "moth": 127858900933279745
}

osrs_players = {
    "moth": "https://secure.runescape.com/m=hiscore_oldschool_ironman/hiscorepersonal?user1=extra%20nice"
}

shitrs_players = {
    "oliver": {
        "hiscores": "https://secure.runescape.com/m=hiscore/compare?user1=Dj+Ollu",
        "runemetrics": r"https://apps.runescape.com/runemetrics/profile/profile?user=dj%20ollu&activities=5",
        "emoji": "<:thinkingoll:458291587441754122>"
    },
    "tann": {
        "hiscores": "https://secure.runescape.com/m=hiscore/compare?user1=Hinric",
        "runemetrics": r"https://apps.runescape.com/runemetrics/profile/profile?user=Hinric&activities=5",
        "emoji": "<:bigpp:667842460382134273>"
    }
}

channels = {
    "grupiteraapia": 111523110892617728,
    "send_to_grupiteraapia": 652606290467487795,
    "jututuba": 653970599521026050
}

macros = {
    "bruh.mp4":"https://www.youtube.com/watch?v=2ZIpFytCSVc",
    "amazin":"https://youtu.be/hC6CZKkEh4A",
    "true": """True and yeah that's pretty true that's true and yeah that's true that's true that's true that's pretty true that's pretty true I mean that's true yeah that's true that's true that's fucking true amm that's how it is dude"""
}

reactables = [
    Reactable(":COOM:675430755350085706", r"c[ou]+m", [".com"])
]

rs_skill_to_emoji = {
    "Overall": ":bar_chart:",
    "Attack": ":crossed_swords:",
    "Defence": ":shield:",
    "Strength": ":fist:",
    "Hitpoints": ":heart:",
    "Constitution": ":heart:",
    "Ranged": ":bow_and_arrow:",
    "Prayer": ":star:",
    "Magic": ":man_mage:",
    "Cooking": ":cooking:",
    "Woodcutting": ":axe:",
    "Fletching": ":dagger:",
    "Fishing": ":fishing_pole_and_fish:",
    "Firemaking": ":fire:",
    "Crafting": ":tools:",
    "Smithing": ":hammer:",
    "Mining": ":pick:",
    "Herblore": ":smoking:",
    "Agility": ":man_running_tone5:",
    "Thieving": ":man_detective_tone5:",
    "Slayer": ":skull_crossbones:",
    "Farming": ":seedling:",
    "Runecrafting": ":congratulations:",
    "Runecraft": ":congratulations:",
    "Hunter": ":rabbit2:",
    "Construction": ":moneybag: :fire:",
    "Summoning": ":ghost:",
    "Dungeoneering": ":mountain_snow:",
    "Divination": ":regional_indicator_g: :regional_indicator_a: :regional_indicator_y:",
    "Invention": ":wrench:"
}

allowed_to_evaluate = {users["moth"]}

class MothBot:

    def __init__(self):
        PyBoiler.Log("Building Markov chains").to_larva()
        self.markov_handler = MarkovHandler.MarkovHandler(my.m_path("markov\\markov_models"))
        PyBoiler.Log("Building lootsim handler").to_larva()
        self.lootsim_handler = lootsim.LootSimManager(my.m_path("lootsim\\lootsim_data"))
        self.cmds = {
            "eval":self.evaluate,
            "imiteeri":self.markov_generate,
            "tts":self.tts,
            "lootsim":self.lootsim
        }
        self.client = client
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
        r = eval(" ".join(message.content.split(" ")[1:])) if message.author.id in allowed_to_evaluate else "Ei :)"
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
        tts = TTS.TTS(message, my.m_path("temp.wav"))
        await tts.work()

    async def lootsim(self, message):
        messages_to_send = self.lootsim_handler.handle(message)
        for m in messages_to_send:
            await message.channel.send(m)

    async def rs_levels_checking(self):
        await client.wait_until_ready()
        while not client.is_closed():
            new_unionized_data = hiscores_parsing.hiscores_osrs(osrs_players)
            # new_unionized_data.update(hiscores_parsing.hiscores_shitrs(shitrs_players))

            for user, stats in new_unionized_data.items():
                p = my.m_path(f"rs_levels_trackers\\{user}.json")

                if os.path.exists(p):
                    msg_to_send = list()
                    with open(p, "r") as fptr:
                        old_data = json.load(fptr)

                    for skill_name, skill_data in stats.items():
                        if type(old_data[skill_name]["level"]) == int:
                            if skill_name != "Overall" and skill_data["level"] > old_data[skill_name]["level"]:
                                msg_to_send.append(f"{user.capitalize()} sai leveli skillis {skill_name}! {rs_skill_to_emoji[skill_name]}")
                                for kw in ("level", "xp", "rank"):
                                    msg_to_send.append(f"{kw}: {old_data[skill_name][kw]} -> {skill_data[kw]}")
                                    
                                if old_data[skill_name]["rank"] < skill_data["rank"]:
                                    msg_to_send[-1] += " :chart_with_downwards_trend:\n"
                                elif old_data[skill_name]["rank"] > skill_data["rank"]:
                                    msg_to_send[-1] += " :chart_with_upwards_trend:\n"

                    if len(msg_to_send):
                        msg_to_send.append("Overall :bar_chart:")
                        for kw in ("level", "xp", "rank"):
                            msg_to_send.append(f"{kw}: {old_data['Overall'][kw]} -> {stats['Overall'][kw]}")
                        
                        if old_data["Overall"]["rank"] < stats["Overall"]["rank"]:
                            msg_to_send[-1] += " :chart_with_downwards_trend:"
                        elif old_data["Overall"]["rank"] > stats["Overall"]["rank"]:
                            msg_to_send[-1] += " :chart_with_upwards_trend:"
                            
                        await client.get_channel(channels["grupiteraapia"]).send("\n".join(msg_to_send))
                        if self.logging:
                            PyBoiler.Log(f"{user} levelled up").to_larva()

                with open(p, "w") as fptr:
                    json.dump(stats, fptr)
            
            for m in hiscores_parsing.runemetrics_shitrs(shitrs_players, my.m_path("rs_activities_tracking")):
                PyBoiler.Log("Runemetrics uuendus").to_larva()
                await client.get_channel(channels["grupiteraapia"]).send(" ".join(m.split()))

            await asyncio.sleep(100)
                                

mothbot = MothBot()

@client.event
async def on_ready():
    PyBoiler.Log("online").to_larva()

@client.event
async def on_message(message):
    if message.channel.id == channels["send_to_grupiteraapia"]:
        await client.get_channel(channels["grupiteraapia"]).send(message.content)
    elif message.author.id != client.user.id:
        await mothbot.handle_message(message)

with open(my.m_path("token.txt"), "r") as fptr:
    token = fptr.read().strip()

client.loop.create_task(mothbot.rs_levels_checking())
client.loop.create_task(mothbot.markov_handler.chatroom_loop(client,
                                                             channels["jututuba"],
                                                             range(60, 120)))
client.run(token)
