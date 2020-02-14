import random

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
        
    def __str__(self) -> str:
        return self.name.capitalize()
    
    @property
    def emoji(self) -> str:
        if type(self.emojis) is str:
            return self.emojis
        if hasattr(self.emojis, "__iter__"):
            return random.choice(self.emojis)

class UserCollection:
    def __init__(self):
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
        )
    )