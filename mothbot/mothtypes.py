import random
import re
import os

from runescape.rstypes import RunescapeType
from typing import Union, Tuple

class Channel:
    Grupiteraapia = 111523110892617728
    Testing = 190793526072573952
    Send_To_Grupiteraapia = 652606290467487795
    Jututuba = 653970599521026050

class User:
    def __init__(self,
                 name: str,
                 emojis: Union[Tuple, str] = None,
                 runescape: RunescapeType = None,
                 id: int = None,
                 can_evaluate: bool = False):
        self.name = name
        self.emojis = emojis
        self.runescape = runescape
        self.can_evaluate = can_evaluate
        self.id = id
        self.tokens_account = TokensAccount(self)
        
    def __str__(self) -> str:
        return self.name.capitalize()
    
    @property
    def emoji(self) -> str:
        if type(self.emojis) is str:
            return self.emojis
        if hasattr(self.emojis, "__iter__"):
            return random.choice(self.emojis)

    @property
    def prefix(self) -> str:
        pref = self.emoji
        if pref is None:
            pref = str(self)
        return pref

class TokensAccount:
    PATH_TO_TOKENS = "" # Assigned to in the init of UserCollection
    DEFAULT_TOKENS_COUNT = "3000"
    
    def __init__(self, user: User):
        self.path = f"{TokensAccount.PATH_TO_TOKENS}\\{user.name}.txt"
        if not os.path.exists(self.path):
            with open(self.path, "w") as fptr:
                fptr.write(TokensAccount.DEFAULT_TOKENS_COUNT)

    def change(self, amount: Union[str, int]) -> None:
        with open(self.path, "r") as fptr:
            old = int(fptr.read())
        with open(self.path, "w") as fptr:
            fptr.write(str(old + int(amount)))

    @property
    def amount(self) -> int:
        with open(self.path, "r") as fptr:
            return int(fptr.read())

class UserCollection:
    def __init__(self, path_to_casino_tokens: str):
        TokensAccount.PATH_TO_TOKENS = path_to_casino_tokens
        os.makedirs(path_to_casino_tokens, exist_ok=True)
        self.users = build_userbase()
        self.runescapers = {
            RunescapeType.RS3: list(),
            RunescapeType.OSRS: list()
        }
        self.key_to_userobj = dict()
        self.can_evaluate = list()
        for user in self.users:
            self.key_to_userobj[user.name] = user
            if user.id is not None:
                self.key_to_userobj[user.id] = user
            if user.can_evaluate:
                self.can_evaluate.append(user.id)
            if isinstance(user.runescape, RunescapeType):
                self.runescapers[user.runescape.type].append(user)
            
    
    def get(self, key: Union[str, int]) -> User:
        return self.key_to_userobj[key]

    def has(self, key: Union[str, int]) -> bool:
        return key in self.key_to_userobj

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

def build_userbase() -> Tuple[User]:
    return (
        User(
            "moth",
            runescape=RunescapeType("https://secure.runescape.com/m=hiscore_oldschool_ironman/hiscorepersonal?user1=extra%20nice"),
            id=127858900933279745,
            can_evaluate=True
        ),
        User(
            "oll",
            emojis="<:thinkingoll:458291587441754122>",
            runescape=RunescapeType("https://apps.runescape.com/runemetrics/profile/profile?user=dj ollu&activities=5")
        ),
        User(
            "sann",
            emojis=(
                "<:sann:446325162393206814>",
                "<:Baldy_MK2:496345452325896192>"
            )
        ),
        User(
            "maku",
            emojis="<:makuW:676220791649730590>"
        ),
        User(
            "nugi",
            emojis=(
                "<:kekn:667842037814525954>",
                "<:nugi:418542605350076428>"
            )
        ),
        User(
            "nipz",
            emojis="<:bigpp:667842460382134273>",
            runescape=RunescapeType("https://apps.runescape.com/runemetrics/profile/profile?user=hinric")
        ),
        User(
            "trump",
            emojis="<:trump:676223879345340451>"
        )
    )