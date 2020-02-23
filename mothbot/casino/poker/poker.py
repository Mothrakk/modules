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
        self.round_counter = 1
        self.large_blind = self.grand_prize // 100
        self.small_blind = self.large_blind // 2

    async def start_session(self) -> None:
        self.poker_players.deduct_tokens(self.buy_in)
        await self.table.send(f"Alustame mänguga, mängus on {', '.join((str(player) for player in self.poker_players))}")
        await self.start_round()

    async def start_round(self) -> None:
        self.deck = Deck()
        out = [f"Round {self.round_counter}"]
        await self.poker_players.deal_hands(self.deck)


class PokerTable(Table):
    VALID_COMMANDS = {"poker", "chips"}.union(PokerSession.VALID_COMMANDS)
    MIN_BUY_IN = 2000
    GENERIC_ERR = f"poker (buyin) (@mängija1) (@mängija2) ...\nBuy-in miinimum {MIN_BUY_IN} ja peab jaguma 1000-ga"

    def __init__(self, client: Client, channel_id: int, user_collection: UserCollection):
        super().__init__(client, channel_id)
        self.user_collection = user_collection
        self.session: PokerSession = None

    @staticmethod
    def is_valid_buy_in(amount: int) -> bool:
        return amount >= PokerTable.MIN_BUY_IN and not amount % 1000

    async def handle_input(self, message: Message):
        if message.channel.id != self.channel_id:
            return

        if (user := self.user_collection.get(message.author)) is None:
            await self.send(f"{message.author.name}: sa ei või kasiinos osaleda")
            return

        poker_player = PokerPlayer(user)

        msg_spl = [x.strip() for x in message.strip().split(" ") if x]
        cmd = msg_spl[0].lower()
        assert cmd in PokerTable.VALID_COMMANDS

        if cmd == "chips" and self.session is not None and poker_player in self.session.poker_players:
            await self.send(f"{poker_player.mentionable} {poker_player.chips} :small_orange_diamond:")

        elif cmd == "poker":
            if self.session is not None:
                await self.send(f"{poker_player.mentionable} mäng juba käib")
            else:
                if len(msg_spl) >= 2 and msg_spl[1].isnumeric() and PokerTable.is_valid_buy_in((buy_in := int(msg_spl[1]))):
                    discord_users = {message.author.id: message.author}
                    for m in message.mentions:
                        discord_users[m.id] = m
                    if len(discord_users) >= 2:
                        poker_players = PokerPlayerCollection.convert(discord_users.values(), self.user_collection, buy_in)
                        if type(poker_players) is str:
                            await self.send(poker_players)
                        else:
                            self.session = PokerSession(self, poker_players, buy_in)
                            await self.session.start_session()
                    else:
                        await self.send(PokerTable.GENERIC_ERR)
                else:
                    await self.send(PokerTable.GENERIC_ERR)
