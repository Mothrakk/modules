import random
import re
import os

from enum import Enum
from runescape.rstypes import RunescapeType
from typing import Union, Tuple, List

class Channel(Enum):
    """Enum-like class for the relevant Discord channels' IDs."""
    Grupiteraapia = 111523110892617728
    Testing = 190793526072573952
    Send_To_Grupiteraapia = 652606290467487795
    Jututuba = 653970599521026050
    
class User:
    def __init__(self,
                 name: str,
                 emojis: Union[Tuple[str], str, None] = None,
                 runescape: Union[RunescapeType, None] = None,
                 id: Union[int, None] = None,
                 can_evaluate: bool = False,
                 make_tokens_account: bool = True):
        """Constructor for creating an User object.

        Parameters:\n
        `name`: name of the user.\n
        `emojis`: Emoji(s) for the user, if available. Can be either a single string or an iterable of strings if
        the user has multiple emojis. Set to `None` if there are no emojis.\n
        `runescape`: A `RunescapeType` object if the given user is a Runescape player.
        Set to `None` if not a Runescape player.\n
        `id`: Discord ID for the given user. `None` if not necessary to specify.\n
        `can_evaluate`: A boolean for determining if the given user can use the `eval` command. Only allow
        trusted users to do this as it can cause havoc.\n
        `make_tokens_account`: Boolean for determining if the user should get a tokens wallet/tokens account.
        Note that in order for this to actually be taken account, an `id` needs to be provided.
        """
        self.name = name
        self.emojis = emojis
        self.runescape = runescape
        self.can_evaluate = can_evaluate
        self.id = id
        if make_tokens_account and id is not None:
            self.tokens_account = TokensAccount(self)
        
    def __str__(self) -> str:
        """`str` representation of the User object, equal to `self.name.capitalize()`"""
        return self.name.capitalize()

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: "User") -> bool:
        return self.id == other.id
    
    @property
    def emoji(self) -> Union[str, None]:
        """Return an emoji string for the given user.
        
        If `self.emojis` is an iterable, selects one at random.\n
        If no emojis available, returns `None`.
        """
        if type(self.emojis) is str:
            return self.emojis
        if hasattr(self.emojis, "__iter__"):
            return random.choice(self.emojis)

    @property
    def prefix(self) -> str:
        """Returns a prefix-like string for the given user.
        
        If the user has an emoji, an emoji will be returned. Otherwise, the user's `__str__()` value will
        be returned.
        """
        pref = self.emoji
        if pref is None:
            pref = str(self)
        return pref

class TokensAccount:
    PATH_TO_TOKENS = "" # Assigned to in the init of UserCollection
    DEFAULT_TOKENS_COUNT = "3000"
    
    def __init__(self, user: User):
        """Helper class for interacting with the user's casino token count."""
        self.path = f"{TokensAccount.PATH_TO_TOKENS}\\{user.name}.txt"
        if not os.path.exists(self.path):
            with open(self.path, "w") as fptr:
                fptr.write(TokensAccount.DEFAULT_TOKENS_COUNT)

    def change(self, amount: int) -> None:
        """Add/subtract to/from the user's token count.
        
        Set `amount` to positive for incrementation and to negative for decrementation.
        """
        with open(self.path, "r+") as fptr:
            old = int(fptr.read())
            fptr.seek(0)
            fptr.write(str(old + amount))
            fptr.truncate()

    @property
    def amount(self) -> int:
        """Returns the current amount of tokens the user has, casted to `int`."""
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
        self.can_evaluate = set()
        for user in self.users:
            self.key_to_userobj[user.name] = user
            if user.id is not None:
                self.key_to_userobj[user.id] = user
            if user.can_evaluate:
                self.can_evaluate.add(user)
            if isinstance(user.runescape, RunescapeType):
                self.runescapers[user.runescape.type].append(user)
            
    def get(self, key: Union[str, int]) -> User:
        """Returns `User` object based on given `key`.
        
        `key` should be the user's name or ID. If no such `key` exists, returns `None`.
        """
        if self.has(key):
            return self.key_to_userobj[key]

    def has(self, key: Union[str, int]) -> bool:
        """Returns `True` if `key` is in the user lookup table, else `False`."""
        return key in self.key_to_userobj

class Reactable:
    def __init__(self,
                 returnable: str,
                 re_pattern: str = "",
                 must_not_contain: List[str] = []):
        """Constructor for creating a Reactable object.
        
        A Reactable is something to add as a reaction to a message if the conditionals pass.\n
        Parameters:\n
        `returnable`: the reaction emoji string. Returned on `str(Reactable)`\n
        `re_pattern`: A pattern the message content ought to contain.\n
        `must_not_contain`: An iterable of strings that must not be in the message content.
        """
        self.returnable = returnable
        self.re_pattern = re_pattern
        self.must_not_contain = must_not_contain

    def __str__(self) -> str:
        return self.returnable

    def match(self, to_test: str) -> str:
        if self.re_pattern and not re.search(self.re_pattern, to_test):
            return False
        return not any((x in to_test for x in self.must_not_contain))

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
            emojis="<:trump:676223879345340451>",
            make_tokens_account=False
        )
    )