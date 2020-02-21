from casino.cards import Deck, Card
from casino.table import Table
from mothtypes import UserCollection, User

from discord import User as dUser
from discord import Client, TextChannel, Message

from typing import List, Union, Dict, Set

class PokerSession:
    VALID_COMMANDS = {"fold", "check", "call", "bet", "raise", "allin"}

    def __init__(self, table: "PokerTable", players: List[User], buy_in: int):
        self.table = table
        self.players = players
        self.buy_in = buy_in

        self.prize = buy_in * len(players)
        self.chips = dict.fromkeys(players, buy_in)
        self.round_counter = 1

        self.button_idx = 0
        self.big_blind_amount = self.prize // 1000
        self.small_blind_amount = self.big_blind_amount // 2

    def __str__(self) -> str:
        out = [f"Pot: {sum((sum(stack) for stack in self.stacks.values()))}"]
        out.append("Ühiskaardid laual:")
        out += [str(card) for card in self.community_cards]
        return "\n".join(out)

    def deduct_buyins(self) -> None:
        for player in self.players:
            player.tokens_account.change(-self.buy_in)

    async def deal_cards_to(self, player: User) -> None:
        out = [f"Hand {self.round_counter}"]
        cards = [self.deck.draw(), self.deck.draw()]
        self.player_hands[player] = cards
        out += [str(card) for card in cards]
        await self.table.send_dm(player, "\n".join(out))

    async def setup(self) -> None:
        #self.deduct_buyins()
        out = ["Alustame mänguga"]
        out.append(f"Laual mängivad {', '.join((str(p) for p in self.players))}")
        out.append(f"Igaühel on {self.buy_in} chipi, mängus on kokku on {self.prize} - winner takes all")
        await self.table.send("\n".join(out))
        await self.start_round()

    async def start_round(self) -> None:
        # 1. Initialize/re-initialize variables.

        out = [f"Round {self.round_counter}"]
        self.deck = Deck()
        self.player_hands = dict()
        self.community_cards = list()
        self.folded_players = set()
        self.needs_to_act = set(self.players)
        self.turn_idx = (self.button_idx + 3) % len(self.players)
        self.stacks = dict()
        for player in self.players:
            self.stacks[player] = list()

        # 2. Deal cards to players.
        for player in self.players:
            await self.deal_cards_to(player)

        # 3. Handle blinds.
        for player, amount in zip((self.small_blind_player, self.big_blind_player),
                                  (self.small_blind_amount, self.big_blind_amount)):
            if self.chips[player] <= amount:
                out.append(f"Mängija {str(player)} peab blindi tõttu all-in minema. Sellest ilmselt tekib side-pot.")
                self.stacks[player].append(self.chips[player])
                self.chips[player] = 0
            else:
                out.append(f"{str(player)} maksis blindi: {amount}")
                self.chips[player] -= amount
                self.stacks[player].append(amount)

        out.append(f"Hetkel mängib {self.current_turn_player}: {self.current_turn_player_options_str}")
        await self.table.send("\n".join(out))

    async def process(self, msg_spl: List[str], player: User) -> None:
        cmd = msg_spl[0].lower()
        options = self.current_turn_player_options

        if cmd not in options:
            return
        if cmd in {"bet", "raise"}:
            if len(msg_spl) < 2 or not msg_spl[1].isnumeric():
                return
            arg = int(msg_spl[1])
            if arg not in options[cmd]:
                return

        if cmd == "check":
            await self.table.send(f"{self.current_turn_player}: check")
        

        self.needs_to_act.remove(player)

    @property
    def small_blind_player(self) -> User:
        return self.players[(self.button_idx + 1) % len(self.players)]

    @property
    def big_blind_player(self) -> User:
        return self.players[(self.button_idx + 2) % len(self.players)]

    @property
    def button_player(self) -> User:
        return self.players[self.button_idx]

    @property
    def current_turn_player(self) -> User:
        return self.players[self.turn_idx]

    @property
    def current_turn_player_options_str(self) -> str:
        options = list()
        for k, v in self.current_turn_player_options.items():
            if type(v) is None:
                options.append(k)
            elif type(v) is int:
                options.append(f"{k} ({v})")
            else: # range
                options.append(f"{k} ({v.start} - {v.stop - 1})")
        return ", ".join(sorted(options))

    @property
    def current_turn_player_options(self) -> Dict[str, Union[int, range, None]]:
        player = self.current_turn_player
        largest_player_stack = max((sum(stack) for stack in self.stacks.values()))
        player_stack = self.stacks[player]
        player_stack_sum = sum(player_stack)
        player_chips = self.chips[player]

        if player_stack_sum == largest_player_stack:
            return {
                "fold": None,
                "check": None,
                "bet": range(1, player_chips + 1),
                "allin": player_chips
            }
        
        debt = largest_player_stack - player_stack_sum
        if debt >= player_chips:
            return {
                "fold": None,
                "allin": player_chips
            }
        
        return {
            "fold": None,
            "call": debt,
            "raise": range(debt + 1, player_chips + 1),
            "allin": player_chips
        }

class PokerTable(Table):
    VALID_COMMANDS = {"poker", "chips"}.union(PokerSession.VALID_COMMANDS)
    MIN_BUY_IN = 2000
    GENERIC_ERR = f"poker (buy_in) (@mängija1) (@mängija2)\nbuy_in peab olema minimaalselt {MIN_BUY_IN} ja jaguma 1000-ga"

    def __init__(self, client: Client, channel_id: int, user_collection: UserCollection):
        self.client = client
        self.channel_id = channel_id
        self.user_collection = user_collection
        self.session = None # one session at a time

    def build_table_players(self, message: Message, buy_in: int) -> Union[List[User], str]:
        players = [self.user_collection.get(message.author.id)]
        for d_user in message.mentions:
            if (user := self.user_collection.get(d_user.id)) is not None:
                if user.tokens_account.amount >= buy_in:
                    players.append(user)
                else:
                    return f"{str(user)} puudub buy-in tokenite arv (tal on {user.tokens_account.amount})"
            else:
                return f"{d_user.name} ei ole kasiinos lubatud"
        if len(players) < 2:
            return PokerTable.GENERIC_ERR
        return players

    async def handle_input(self, message: Message) -> None:
        msg_split = [w for w in [w.strip() for w in message.content.strip().split(" ")] if w]
        cmd = msg_split[0].lower()
        assert cmd in PokerTable.VALID_COMMANDS

        if message.channel.id != self.channel_id:
            return

        if (user := self.user_collection.get(message.author.id)) is None:
            await self.send(f"{message.author.name} - sa ei saa kasiinost osa võtta")
            return

        if cmd == "poker":
            if self.session is None:
                if len(msg_split) >= 2 and msg_split[1].isnumeric() and PokerTable.is_valid_buyin(buy_in := int(msg_split[1])):
                    if type(table_players := self.build_table_players(message, buy_in)) is not str:
                        self.session = PokerSession(self, table_players, buy_in)
                        await self.session.setup()
                    else:
                        await self.send(table_players)
                else:
                    await self.send(PokerTable.GENERIC_ERR)
            else:
                await self.send(f"{str(user)} - mäng juba käib")

        elif self.session is not None:
            if user in self.session.players:
                if cmd == "chips":
                    await self.send(f"{str(user)} - sul {self.session.chips[user]} chipi")
                elif self.session.current_turn_player is user:
                    self.session.process(cmd, user)
                else:
                    await self.send(f"Praegu on {self.session.current_turn_player} kord")
            else:
                await self.send(f"{str(user)} - sa ei ole praeguses pokkerimängus")

    @staticmethod
    def is_valid_buyin(buy_in: int) -> bool:
        return buy_in >= PokerTable.MIN_BUY_IN and not buy_in % 1000
