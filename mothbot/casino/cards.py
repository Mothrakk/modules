import random
import itertools

from typing import List, Union

class Card:
    """Create a Card object.

    Parameters:\n
    `suit`: Suit of the card.\n
    `rank`: Rank of the card. Expecting a type `int` for ranks 2-10; otherwise `str`.\n
    `hidden` Boolean for deciding if this card should be hidden from the player on the playing table.
    """
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
            return f":{self.suit.lower()}: {self.rank} of {self.suit}"
        return "(Peidus kaart)"

class Deck:
    """Create a Deck object.

    Parameters:\n
    `populate_cards`: Boolean for determining if the deck should populate itself into a standard (52-card) deck.
    Set to True for populating, otherwise the deck will remain empty.\n
    `shuffle`: Boolean for determining if the deck should shuffle itself after populating. This argument has no effect
    and does nothing if `populate_cards` is False.
    """
    SUITS = ("Clubs", "Diamonds", "Hearts", "Spades")
    RANKS = tuple(range(2, 11)) + ("Ace", "King", "Queen", "Jack")

    def __init__(self, populate_cards: bool = True, shuffle: bool = True):
        self.deck = list()
        if populate_cards:
            for suit, rank in itertools.product(Deck.SUITS, Deck.RANKS):
                self.add(Card(suit, rank))
            if shuffle:
                self.shuffle()

    def __str__(self) -> str:
        if len(self.deck):
            return "\n".join((str(c) for c in self.deck))
        return "--"

    def add(self, card: Card) -> None:
        """Append `card` to the top of the deck."""
        self.deck.append(card)

    def draw(self) -> Union[Card, None]:
        """Draw a card and remove it from the top of the deck. Returns `Card` if the deck is not empty, otherwise `None`."""
        if self.size:
            return self.deck.pop()

    def shuffle(self) -> None:
        """Shuffles the deck."""
        random.shuffle(self.deck)

    def seek_untapped_ace(self) -> Union[Card, None]:
        """Find the first Ace card in the deck that has not been tapped.
        
        An untapped Ace card has a `blackjack_value` of 11.\n
        A tapped Ace card has a `blackjack_value` of 1.\n
        Returns `Card` if there is an untapped Ace card in the deck, otherwise `None`.
        """
        for card in self.deck:
            if card.blackjack_value == 11:
                return card

    @property
    def has_hidden_card(self) -> bool:
        """Returns `True` if there is at least one card in the deck with the `hidden` property set to `True`, otherwise `False`."""
        return any((card.hidden for card in self.deck))

    @property
    def size(self) -> int:
        """Returns the length/size of the deck."""
        return len(self.deck)

    @property
    def blackjack_value(self) -> Union[int, str]:
        """Returns the blackjack value of the deck.

        Equivalent to `sum((card.blackjack_value for card in self.deck))`
        """
        return sum((card.blackjack_value for card in self.deck))
