from mothtypes import User
from casino.cards import Hand, Deck

from typing import List, Dict, Union

class PokerPlayer(User):
    def __init__(self, user: User):
        self.id = user.id
        self.name = user.name
        self.tokens_account = user.tokens_account
        self.hand: Hand = None
        self.chips: int = None

    def can_buy_in(self, proposed_buy_in: int) -> bool:
        return self.tokens_account.amount >= proposed_buy_in

    async def dm_hand(self) -> None:
        await self.dm(str(self.hand))
    
class PokerPlayerCollection:
    def __init__(self, poker_players: List[PokerPlayer]):
        self.poker_players = poker_players

    def __iter__(self):
        return iter(self.poker_players)

    def deduct_tokens(self, amount: int) -> None:
        for player in self.poker_players:
            player.tokens_account.change(-amount)

    def deal_hands(self, deck: Deck) -> None:
        for player in self.poker_players:
            player.hand = [deck.draw(), deck.draw()]
    
    async def dm_hands(self) -> None:
        for player in self.poker_players:
            await player.dm_hand()
