import asyncio
import os

from mothtypes import User, UserCollection
from casino.cards import Deck, Card

from discord import Client, Message, TextChannel
from typing import List, Union

class Session:
    DEALER_WINS = False
    PLAYER_WINS = True
    TIE = None
    
    def __init__(self, table: "BlackjackTable", bet_amount: int, player: User):
        self.table = table
        self.bet_amount = bet_amount
        self.player = player
        self.deck = Deck()
        self.player_hand = Deck(False)
        self.dealer_hand = Deck(False)
        self.ongoing = True
        self.player_standing = False

    def __str__(self) -> str:
        out = list()
        out.append(f"{str(self.player)} käsi")
        out.append(str(self.player_hand))
        out.append("Diileri käsi")
        out.append(str(self.dealer_hand))
        return "\n".join(out)

    async def start_session(self) -> None:
        self.player.tokens_account.change(-self.bet_amount)
        await self.table.send(f"{str(self.player)} on mängus - valikud on (stand | hit | status)")
        await self.hit_dealer(False)
        await self.hit_player(False)
        await self.hit_dealer(False, hidden=True)
        await self.hit_player()

    async def end_session(self, ending: bool) -> None:
        if self.ongoing:
            self.ongoing = False
            await self.unhide_cards()
            if ending == Session.PLAYER_WINS:
                self.player.tokens_account.change(self.bet_amount * 2)
                await self.table.send(f"{str(self.player)} võitis {self.bet_amount * 2} tokenit")
                await self.table.test_achievement(self.player, self.bet_amount * 2, "Suurim võit")
            elif ending == Session.DEALER_WINS:
                await self.table.send(f"Diiler võitis ning {str(self.player)} kaotas {self.bet_amount} tokenit")
                await self.table.test_achievement(self.player, self.bet_amount, "Suurim kaotus")
            else:
                self.player.tokens_account.change(self.bet_amount)
                await self.table.send(f"Viik - {str(self.player)} sai enda tokenid tagasi")
            self.table.sessions.pop(self.player)

    async def unhide_cards(self) -> None:
        for card in self.dealer_hand.deck:
            if card.hidden:
                card.hidden = False
                await self.table.send(f"Diileri peidus kaart oli {str(card)} ({self.dealer_hand.blackjack_value})")
                break

    async def player_stand(self) -> None:
        self.player_standing = True
        await self.unhide_cards()
        await self.evaluate_status()
        while self.ongoing:
            await self.hit_dealer()

    async def hit_player(self, eval: bool = True, _print: bool = True) -> None:
        card = self.deck.draw()
        self.player_hand.add(card)
        if _print:
            await self.table.send(f"{str(self.player)} tõmbas pakist {str(card)} ({self.player_hand.blackjack_value})")
        if self.player_hand.blackjack_value > 21:
            if (untapped_ace := self.player_hand.seek_untapped_ace()) is not None:
                untapped_ace.blackjack_value = 1
                if _print:
                    await self.table.send(f"Õnneks oli pakis Ace kaart mis päästis käe ({self.player_hand.blackjack_value})")
        if eval:
            await self.evaluate_status()

    async def hit_dealer(self, eval: bool = True, _print: bool = True, hidden: bool = False) -> None:
        card = self.deck.draw()
        card.hidden = hidden
        self.dealer_hand.add(card)
        if _print:
            o = f"Diiler tõmbas pakist {str(card)}"
            if self.dealer_hand.has_hidden_card:
                o += " (?)"
            else:
                o += f" ({self.dealer_hand.blackjack_value})"
            await self.table.send(o)
        if self.dealer_hand.blackjack_value > 21:
            if (untapped_ace := self.dealer_hand.seek_untapped_ace()) is not None:
                untapped_ace.blackjack_value = 1
                if _print and not hidden:
                    await self.table.send(f"Õnneks oli pakis Ace kaart mis päästis käe ({self.dealer_hand.blackjack_value})")
        if eval:
            await self.evaluate_status()

    async def evaluate_status(self) -> None:
        player_hand_val = self.player_hand.blackjack_value
        dealer_hand_val = self.dealer_hand.blackjack_value

        if player_hand_val == dealer_hand_val == 21:
            await self.end_session(Session.TIE)
        elif dealer_hand_val > 21:
            await self.end_session(Session.PLAYER_WINS)
        elif player_hand_val > 21 or (self.player_standing and dealer_hand_val > player_hand_val):
            await self.end_session(Session.DEALER_WINS)

class BlackjackTable:
    VALID_COMMANDS = {"blackjack", "stand", "hit", "status", "bjrecords"}

    def __init__(self, path_to_achievements: str, client: Client, channel_id: int, user_collection: UserCollection):
        self.path_to_achievements = path_to_achievements
        self.client = client
        self.channel_id = channel_id
        self.user_collection = user_collection
        self.sessions = dict()

    async def handle_input(self, message: Message) -> None:
        msg_split = [w for w in [w.strip() for w in message.content.strip().split(" ")] if w]
        cmd = msg_split[0].lower()
        assert cmd in BlackjackTable.VALID_COMMANDS
        
        if message.channel.id != self.channel_id:
            return

        if (user := self.user_collection.get(message.author.id)) is None:
            await self.send(f"{message.author.name} - sina ei saa kasiinost osa võtta")
            return
        
        if cmd == "blackjack":
            if user in self.sessions:
                await self.send(f"{str(user)} - sul mäng käib juba!")
            else:
                if len(msg_split) >= 2 and msg_split[1].isnumeric() and msg_split[1] != "0":
                    if user.tokens_account.can_bet((tokens := int(msg_split[1]))):
                        sesh = Session(self, tokens, user)
                        self.sessions[user] = sesh
                        await sesh.start_session()
                    else:
                        await self.send(f"{str(user)} - sul pole nii palju tokeneid! (sul on {user.tokens_account.amount})")
                else:
                    await self.send("blackjack (tokenite arv)")
        
        elif cmd == "bjrecords":
            out = list()
            for filename in os.listdir(self.path_to_achievements):
                achievement = filename.split(".")[0]
                with open(f"{self.path_to_achievements}\\{filename}", "r") as fptr:
                    amount, holder = fptr.read().split(":")
                out.append(f"{achievement} - Kroonitud {holder} ({amount})")
            await self.send("\n".join(out))

        elif user in self.sessions:
            sesh = self.sessions[user]
            
            if cmd == "stand":
                await sesh.player_stand()

            elif cmd == "hit":
                await sesh.hit_player()

            elif cmd == "status":
                await self.send(str(sesh))

    async def test_achievement(self, user: User, amount: int, achievement: str) -> None:
        filename = f"{self.path_to_achievements}\\{achievement}.txt"
        if os.path.exists(filename):
            with open(filename, "r") as fptr:
                old = int(fptr.read().split(":")[0])
        else:
            old = -1
        if amount > old:
            with open(filename, "w") as fptr:
                fptr.write(f"{amount}:{str(user)}")
            await self.send(f"{str(user)} - õnnitlen, oled uus rekordihoidja kategoorias '{achievement}'")

    async def send(self, msg: str) -> None:
        await self.channel.send(msg)

    @property
    def channel(self) -> TextChannel:
        return self.client.get_channel(self.channel_id)

