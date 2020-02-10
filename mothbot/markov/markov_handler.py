import os
import markovify
import random
import asyncio
import requests

from discord import Client

emoji_of = {
    "oll": "<:thinkingoll:458291587441754122>",
    "nipz": "<:bigpp:667842460382134273>",
    "sann": ("<:sann:446325162393206814>", "<:Baldy_MK2:496345452325896192>"),
    "nugi": ("<:nugi:418542605350076428>", "<:kekn:667842037814525954>")
}

class GoogleTranslateException(Exception):
    pass

class MarkovHandler:
    MAX_GEN_AT_ONCE = 5

    def __init__(self, path_to_models: str):
        self.models = dict()
        for filename in os.listdir(path_to_models):
            name = filename.split(".")[0]
            with open(f"{path_to_models}\\{filename}", "r", encoding="utf-8") as fptr:
                self.models[name] = markovify.NewlineText.from_json(fptr.read())
        self.err_msg = f"imiteeri [{'|'.join(self.models)}]"

    def translate_string(self, q: str, source: str = "en", target: str = "et"):
        q = requests.utils.quote(q) # URI encode
        response = requests.get(f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={source}&tl={target}&dt=t&q={q}")
        if response.status_code != 200:
            raise GoogleTranslateException(f"Return code {response.status_code}")
        return response.json()[0][0][0]

    def generate_sentence(self, name: str, prefix_name=False) -> str:
        name = name.lower()
        if name not in self.models:
            return self.err_msg

        s = None
        while s is None:
            s = self.models[name].make_sentence()
        if name == "trump":
            s = self.translate_string(s)
        if prefix_name:
            if name in emoji_of:
                if type(emoji_of[name]) == str:
                    s = f"{emoji_of[name]}: {s}"
                else:
                    s = f"{random.choice(emoji_of[name])}: {s}"
            else:
                s = f"{name}: {s}"

        return s

    def generate_sentences(self, name: str, count: int, prefix_names=False) -> list:
        name = name.lower()
        if name not in self.models:
            return [self.err_msg]
        
        if count > MarkovHandler.MAX_GEN_AT_ONCE:
            count = MarkovHandler.MAX_GEN_AT_ONCE
        elif count < 1:
            count = 1

        sentences = []
        while len(sentences) < count:
            sentences.append(self.generate_sentence(name, prefix_names))
        
        return sentences

    async def chatroom_loop(self, client: Client, channel_id: int, path_to_interval: str):
        await client.wait_until_ready()
        names = tuple(self.models)
        while not client.is_closed():
            with open(path_to_interval, "r") as fptr:
                a, b = (int(x) for x in fptr.read().split(","))
            interval_range = range(a, b)
            s = self.generate_sentence(random.choice(names), True)
            await client.get_channel(channel_id).send(s)
            await asyncio.sleep(random.choice(interval_range))
