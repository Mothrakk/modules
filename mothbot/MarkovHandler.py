import os
import markovify
import urllib
import requests

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

    def translate_string(self, q: str, source="en", target="et"):
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
