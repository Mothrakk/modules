import os
import markovify
import random
import asyncio
import requests

from mothtypes import UserCollection
from discord import Client

class GoogleTranslateException(Exception):
    pass

class MarkovHandler:
    MAX_GEN_AT_ONCE = 5
    NAMES_TO_TRANSLATE = {"trump"}

    def __init__(self, path_to_module: str, user_collection: UserCollection):
        self.user_collection = user_collection
        self.models = dict()
        self.path_to_interval = f"{path_to_module}\\interval.txt"
        for filename in os.listdir(f"{path_to_module}\\markov_models"):
            name = filename.split(".")[0]
            with open(f"{path_to_module}\\markov_models\\{filename}", "r", encoding="utf-8") as fptr:
                self.models[name] = markovify.NewlineText.from_json(fptr.read())
        self.err_msg = f"imiteeri [{'|'.join(self.models)}]"

    def translate_string(self, q: str, source: str = "en", target: str = "et"):
        q = requests.utils.quote(q) # URI encode
        response = requests.get(f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={source}&tl={target}&dt=t&q={q}")
        if response.status_code != 200:
            raise GoogleTranslateException(f"Return code {response.status_code}")
        return response.json()[0][0][0]

    def generate_sentence(self, name: str, prefix_name: bool = False) -> str:
        name = name.lower()
        if name not in self.models:
            return self.err_msg

        s = None
        while s is None:
            s = self.models[name].make_sentence()
        if name in MarkovHandler.NAMES_TO_TRANSLATE:
            s = self.translate_string(s)
        if prefix_name:
            s = f"{self.user_collection.get(name).prefix}: {s}"

        return s

    def generate_sentences(self, name: str, count: int, prefix_names: bool = False) -> list:
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

    async def chatroom_loop(self, client: Client, channel_id: int):
        await client.wait_until_ready()
        names = tuple(self.models)
        while not client.is_closed():
            if not random.randint(0, 999): # EASTER EGG
                await client.get_channel(channel_id).send("<:haiii:490615218033131530>: ...")
            else:
                with open(self.path_to_interval, "r") as fptr:
                    a, b = (int(x) for x in fptr.read().split(","))
                s = self.generate_sentence(random.choice(names), True)
                await client.get_channel(channel_id).send(s)

            await asyncio.sleep(random.choice(range(a, b)))
