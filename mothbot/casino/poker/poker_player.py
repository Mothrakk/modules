from mothtypes import User, UserCollection
from casino.cards import Hand, Deck, Card

from discord import User as DiscordUser
from typing import List, Dict, Union, Set

class PokerPlayer(User):
    def __init__(self, user: User):
        self.id = user.id
        self.name = user.name
        self.tokens_account = user.tokens_account
        self.hand: Hand = None
        self.chips: int = None
        self.contributions: int = None

    def can_buy_in(self, proposed_buy_in: int) -> bool:
        return self.tokens_account.amount >= proposed_buy_in

    async def dm_hand(self) -> None:
        await self.dm(str(self.hand))

    def contribute(self, amount: int) -> None:
        assert self.chips >= amount
        self.contributions += amount
        self.chips -= amount

    def options(self, contributors: Set[PokerPlayer]) -> Dict[str, Union[int, range, None]]:
        options = {"fold": None, "allin": self.chips}
        largest_contribution = max((p.contributions for p in contributors))
        if self.contributions == largest_contribution:
            options["check"] = None
            options["bet"] = range(1, self.chips + 1)
        elif self.contributions < largest_contribution:
            debt = largest_contribution - self.contributions
            if self.chips >= debt:
                options["call"] = debt
                if self.chips > debt:
                    options["raise"] = range(debt, self.chips + 1)
        return options

    def options_string(self, contributors: Set[PokerPlayer]) -> str:
        out = list()
        for option, v in self.options(contributors).items():
            if v is None:
                out.append(option)
            elif type(v) is int:
                out.append(f"{option} ({v})")
            else: # range
                out.append(f"{option} ({v.start}-{v.stop - 1})")
        return ", ".join(out)
    
class PokerPlayerCollection:
    def __init__(self, poker_players: List[PokerPlayer] = []):
        self.poker_players = poker_players

    def __iter__(self):
        return iter(self.poker_players)

    def add_player(self, player: PokerPlayer):
        self.poker_players.append(player)

    @staticmethod
    def convert(discord_users: List[DiscordUser], user_collection: UserCollection, buy_in: int) -> Union["PokerPlayerCollection", str]:
        poker_players = list()
        for discord_user in discord_users:
            if (user := user_collection.get(discord_user)) is not None:
                poker_player = PokerPlayer(user)
                if poker_player.can_buy_in(buy_in):
                    poker_players.append(poker_player)
                else:
                    return f"{str(poker_player)} pole piisavalt tokeneid (tal on {poker_player.tokens_account.amount})"
            else:
                return f"{discord_user.name} ei saa kasiinost osa võtta"
        return PokerPlayerCollection(poker_players)

    def deduct_tokens(self, amount: int) -> None:
        for player in self.poker_players:
            player.tokens_account.change(-amount)

    def set_chips(self, amount: int) -> None:
        for player in self.poker_players:
            player.chips = amount

    def deal_hands(self, deck: Deck) -> None:
        for player in self.poker_players:
            player.hand = Hand([deck.draw(), deck.draw()])

    def reset_contributions(self) -> None:
        for player in self.poker_players:
            player.contributions = 0
    
    async def dm_hands(self) -> None:
        for player in self.poker_players:
            await player.dm_hand()
