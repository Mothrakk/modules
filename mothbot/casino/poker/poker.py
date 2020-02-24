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
        self.rounds_per_blind_raise = len(poker_players)
        self.button_idx = 0

    async def start_session(self) -> None:
        self.poker_players.deduct_tokens(self.buy_in)
        self.poker_players.set_chips(self.buy_in)
        await self.table.send(f"Alustame mänguga, mängus on {', '.join((str(player) for player in self.poker_players))}")
        await self.start_round()

    async def end_session(self) -> None:
        assert len(self.poker_players) == 1
        winner = self.poker_players[0]
        await self.table.send(f"{str(winner)} võitis pokkerimängu! {self.grand_prize} tokenit :small_orange_diamond:")
        winner.tokens_account.change(self.grand_prize)
        self.table.session = None

    async def start_round(self) -> None:
        self.deck = Deck()
        self.contributors = set()
        self.current_idx = self.button_idx
        self.needs_to_act = set(self.poker_players)
        self.folded = set()
        self.all_in = set()
        self.community_cards = list()
        self.poker_players.reset_contributions()
        self.poker_players.deal_hands(self.deck)
        await self.table.send(f"Round {self.round_counter}")
        await self.poker_players.dm_hands()
        await self.deduct_blinds()
        await self.send_current_player()

    async def end_round(self) -> None:
        if len(self.poker_players) > 1:
            self.button_idx = (self.button_idx + 1) % len(self.poker_players)
            if not self.button_idx:
                self.large_blind *= 2
                self.small_blind *= 2
            self.round_counter += 1
            await self.start_round()
        else:
            await self.end_session()

    async def progress(self) -> None:
        raise NotImplementedError

    async def handle_input(self, msg_spl: List[str]):
        cmd = msg_spl[0]
        current = self.current_player
        options = current.options

        assert current in self.needs_to_act

        if (cmd not in options) or (type(options[cmd]) is range and not (len(msg_spl) > 1 and msg_spl[1].isnumeric() and (arg := int(msg_spl[1])) in options[cmd])):
            await self.table.send(f"{current.mentionable} halb valik - sinu valikud on {current.options_string}")
            return

        if cmd == "fold":
            self.folded.add(current)
        elif cmd == "check":
            pass
        else:
            self.contributors.add(current)
            amount = arg if type(options[cmd]) is range else options[cmd]
            current.contribute(amount)
            self.needs_to_act = set(self.poker_players).difference(self.folded).difference(self.all_in)
            if not current.chips:
                self.all_in.add(current)
            await self.table.send(f"{str(current)}: {cmd} {amount} :small_orange_diamond:")
        self.needs_to_act.remove(current)

        await self.progress()

    async def deduct_blinds(self) -> None:
        for player, blind in zip((self.small_blind_player, self.large_blind_player),
                                 (self.small_blind, self.large_blind)):
            if player.chips > blind:
                player.contribute(blind)
                await self.table.send(f"{player.mentionable} maksis blindi: {blind} :small_orange_diamond:")
            else:
                player.contribute(player.chips)
                await self.table.send(f"{player.mentionable} pidi blindi ({blind} :small_orange_diamond:) tõttu minema all-in")
            self.contributors.add(player)

    async def send_current_player(self) -> None:
        await self.table.send(f"Hetkel mängib {self.current_player.mentionable}: {self.current_player.options_string(self.contributors)}")

    @property
    def current_player(self) -> PokerPlayer:
        assert len(self.needs_to_act)
        while self.poker_players[self.current_idx] not in self.needs_to_act:
            self.current_idx = (self.current_idx + 1) % len(self.poker_players)
        return self.poker_players[self.current_idx]

    @property
    def button_player(self) -> PokerPlayer:
        return self.poker_players[self.button_idx]

    @property
    def small_blind_player(self) -> PokerPlayer:
        return self.poker_players[(self.button_idx + 1) % len(self.poker_players)]

    @property
    def large_blind_player(self) -> PokerPlayer:
        return self.poker_players[(self.button_idx + 2) % len(self.poker_players)]

    @property
    def pot(self) -> int:
        return sum((p.contributions for p in self.poker_players))

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

        if self.session is not None and cmd in PokerTable.VALID_COMMANDS:
            if poker_player == self.session.current_player:
                await self.session.handle_input(msg_spl)
            else:
                await self.session.send_current_player()

        elif cmd == "chips" and self.session is not None and poker_player in self.session.poker_players:
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
