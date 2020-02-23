from casino.cards import Deck, Card, Hand
from casino.table import Table
from casino.poker.poker_player import PokerPlayer, PokerPlayerCollection
from mothtypes import UserCollection, User

from discord import Client, TextChannel, Message

from typing import List, Union, Dict, Set

class PokerSession:
    VALID_COMMANDS = {"fold", "check", "call", "bet", "raise", "allin"}

    def __init__(self, table: "PokerTable", poker_players: PokerPlayerCollection, buy_in: int):
        self.table = table
        self.poker_players = poker_players
        self.buy_in = buy_in
        self.grand_prize = len(poker_players) * buy_in

class PokerTable(Table):
    VALID_COMMANDS = {"poker", "chips"}.union(PokerSession.VALID_COMMANDS)
    MIN_BUY_IN = 2000


    def __init__(self, client: Client, channel_id: int, user_collection: UserCollection):
        super().__init__(client, channel_id)
        self.user_collection = user_collection
        self.session: PokerSession = None

    async def handle_input(self, message: Message):
        if message.channel.id != self.channel_id:
            return

        if (user := self.user_collection.get(message.author)) is None:
            await self.send(f"{message.author.name}: sa ei või kasiinos osaleda")
            return

        poker_player = PokerPlayer(user)

        msg_spl = [x.strip() for x in message.strip().split(" ") if x]
        cmd = msg_spl[0].lower()

        if cmd == "chips" and self.session is not None and poker_player in self.session.poker_players:
            await self.send(f"{poker_player.mentionable} {poker_player.chips} :small_orange_diamond:")

        elif cmd == "poker":
            if self.session is not None:
                await self.send(f"{poker_player.mentionable} mäng juba käib")
            else:
                pass

        raise NotImplementedError