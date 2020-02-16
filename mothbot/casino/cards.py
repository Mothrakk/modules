import random

from typing import List, Union

class Card:
    def __init__(self, suit: str, rank: Union[str, int], hidden: bool = False):
        self.suit = suit
        self.rank = rank
        self.hidden = hidden
        if rank == "Ace":
            self.blackjack_value = 11
        elif type(rank) is int:
            self.blackjack_value = rank
        else:
            self.blackjack_value = 10

    def __str__(self) -> str:
        if not self.hidden:
            return f"{self.rank} of {self.suit}"
        return "(Peidus kaart)"

class Deck:
    SUITS = ("Clubs", "Diamonds", "Hearts", "Spades")
    RANKS = tuple(range(2, 11)) + ("Ace", "King", "Queen", "Jack")

    def __init__(self, populate_cards: bool = True, shuffle: bool = True):
        self.deck = list()
        if populate_cards:
            for suit in Deck.SUITS:
                for rank in Deck.RANKS:
                    self.add(Card(suit, rank))
            if shuffle:
                self.shuffle()

    def __str__(self) -> str:
        if len(self.deck):
            return "```\n" + "\n".join((str(c) for c in self.deck)) + "\n```"
        return ""

    def add(self, card: Card) -> None:
        self.deck.append(card)

    def draw(self) -> Union[Card, None]:
        if self.size:
            return self.deck.pop()

    def shuffle(self) -> None:
        random.shuffle(self.deck)

    def seek_untapped_ace(self) -> Union[Card, None]:
        for card in self.deck:
            if card.blackjack_value == 11:
                return card

    @property
    def size(self) -> int:
        return len(self.deck)

    @property
    def blackjack_value(self) -> Union[int, str]:
        return sum((card.blackjack_value for card in self.deck))
