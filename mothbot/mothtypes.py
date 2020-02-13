import random

from runescape.rstypes import RunescapeType, OSRS, RS3
from typing import Union, Tuple

class User:
    def __init__(self,
                 name: str,
                 emojis: Union[Tuple, str] = None,
                 runescape: RunescapeType = None,
                 can_evaluate: bool = False):
        self.name = name
        self.emojis = emojis
        self.runescape = runescape
        self.can_evaluate = can_evaluate
        
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
        self.name_to_userobj = dict()
        for user in self.users:
            self.name_to_userobj[user.name] = user
            if isinstance(user.runescape, RunescapeType):
                self.runescapers[user.runescape.type].append(user)
    
    def get(self, name: str) -> User:
        return self.name_to_userobj[name]

def build_userbase() -> Tuple[User]:
    return (
        User(
            "moth",
            runescape=OSRS("https://secure.runescape.com/m=hiscore_oldschool_ironman/hiscorepersonal?user1=extra%20nice"),
            can_evaluate=True
        ),
        User(
            "oll",
            emojis="<:thinkingoll:458291587441754122>",
            runescape=RS3("https://apps.runescape.com/runemetrics/profile/profile?user=dj ollu&activities=5")
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
            runescape=RS3("https://apps.runescape.com/runemetrics/profile/profile?user=hinric")
        )
    )