import random
import itertools

from typing import List, Union, Tuple, Dict, Set

class Deck:
    """Create a Deck object.

    Parameters:\n
    `populate_cards`: Boolean for determining if the deck should populate itself into a standard (52-card) deck.
    Set to True for populating, otherwise the deck will remain empty.\n
    `shuffle`: Boolean for determining if the deck should shuffle itself after populating. This argument has no effect
    and does nothing if `populate_cards` is False.
    """
    SUITS = ("Clubs", "Diamonds", "Hearts", "Spades")
    RANKS = tuple(range(2, 11)) + ("Jack", "Queen", "King", "Ace")

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

    def __iter__(self):
        return iter(self.deck)

    def add(self, card: "Card") -> None:
        """Append `card` to the top of the deck."""
        self.deck.append(card)

    def draw(self) -> Union["Card", None]:
        """Draw a card and remove it from the top of the deck. Returns `Card` if the deck is not empty, otherwise `None`."""
        if self.size:
            return self.deck.pop()

    def shuffle(self) -> None:
        """Shuffles the deck."""
        random.shuffle(self.deck)

    def seek_untapped_ace(self) -> Union["Card", None]:
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
        self.rank_tier = Deck.RANKS.index(rank) + 2
        self.suit_tier = Deck.SUITS.index(suit)

    def __str__(self) -> str:
        if not self.hidden:
            return f":{self.suit.lower()}: {self.rank} of {self.suit}"
        return "(Peidus kaart)"

    @staticmethod
    def rank_tier_to_str(rank_tier: int) -> str:
        return str(Deck.RANKS[rank_tier - 2])

    @staticmethod
    def suit_tier_to_str(suit_tier: int) -> str:
        return Deck.SUITS[suit_tier]

class Hand:
    """Create a Hand object.

    The functional difference between a `Hand` and a `Deck` is that a `Hand` object will ALWAYS stay sorted, by priority of rank > suit.
    """
    def __init__(self, cards: List[Card]):
        self.cards = cards
        self.sort()

    def __iter__(self):
        return iter(self.cards)

    def __str__(self) -> str:
        return "\n".join((str(card) for card in self.cards))

    def add(self, cards: Union[Card, List[Card]]) -> None:
        """Add a `Card` to the hand."""
        if type(cards) is list:
            self.cards += cards
        else:
            self.cards.append(cards)
        self.sort()

    def sort(self) -> None:
        """Sort the hand, first by suit, then by rank."""
        self.sort_by_suit()
        self.sort_by_ranking()

    def sort_by_suit(self) -> None:
        """Sort the hand in place by suit."""
        self.cards = sorted(self.cards, key=lambda card: card.suit_tier)

    def sort_by_ranking(self) -> None:
        """Sort the hand in place by rank."""
        self.cards = sorted(self.cards, key=lambda card: card.rank_tier)

    @staticmethod
    def straight_has_flush(rank_to_suits: Dict[int, Set[int]], largest: int) -> bool:
        suits_intersection = rank_to_suits[largest]
        for rank in range(largest - 1, largest - 5, -1):
            suits_intersection.intersection_update(rank_to_suits[rank])
        return bool(suits_intersection)

    @staticmethod
    def straight_array_to_str(largest: int) -> str:
        s = list()
        for rank in range(largest - 4, largest + 1):
            s.append(Card.rank_tier_to_str(rank))
        return "-".join(s)
        
    def poker_value(self, community_cards: List[Card] = []) -> Tuple[int, str]:
        """Returns the poker value of the hand in the form of (strength, str)"""
        cards = self.cards + community_cards
        raw_rankings = [card.rank_tier for card in cards]
        raw_suits = [card.suit_tier for card in cards]
        rank_to_suits = {rank: set() for rank in raw_rankings}
        suit_to_ranks = {suit: set() for suit in raw_suits}
        for rank, suit in zip(raw_rankings, raw_suits):
            rank_to_suits[rank].add(suit)
            suit_to_ranks[suit].add(rank)
        
        straights = set()
        for largest in range(14, 5, -1):
            if all((rank in rank_to_suits for rank in range(largest, largest - 5, -1))):
                straights.add(largest)

        # ROYAL FLUSH
        if 14 in straights and Hand.straight_has_flush(rank_to_suits, 14):
            return 100000, "Royal Flush!"

        # STRAIGHT FLUSH
        for largest in sorted(straights.difference({14}), reverse=True):
            if Hand.straight_has_flush(rank_to_suits, largest):
                return 90000 + largest, f"Straight Flush ({Hand.straight_array_to_str(largest)})"

        pairs = {i: set() for i in range(2, 5)}
        for rank, suits in rank_to_suits.items():
            l = len(suits)
            if l > 1:
                pairs[l].add(rank)
        
        # FOUR OF A KIND
        if pairs[4]:
            largest_four_of_a_kind = max(pairs[4])
            kicker = max(set(rank_to_suits).difference({largest_four_of_a_kind}))
            return 80000 + largest_four_of_a_kind * 10 + kicker, f"Four of a Kind (4x {Card.rank_tier_to_str(largest_four_of_a_kind)}, {Card.rank_tier_to_str(kicker)} kicker)"
        
        # FULL HOUSE
        if pairs[3] and pairs[2]:
            largest_threesome = max(pairs[3])
            largest_twosome = max(pairs[2])
            return 70000 + largest_threesome * 10 + largest_twosome, f"Full House (3x {Card.rank_tier_to_str(largest_threesome)}, 2x {Card.rank_tier_to_str(largest_twosome)})"

        flushes = set()
        for suit, ranks in suit_to_ranks.items():
            if len(ranks) >= 5:
                flushes.add(suit)
        
        # FLUSH
        if flushes:
            # find the flush with the largest high card
            best_flush = sorted(flushes, key=lambda suit: max(suit_to_ranks[suit]))[-1]
            highest_card = max(suit_to_ranks[best_flush])
            return 60000 + highest_card, f"Flush (5x {Card.suit_tier_to_str(best_flush)}, high card {Card.rank_tier_to_str(highest_card)})"

        # STRAIGHT
        if straights:
            highest_card_of_largest_straight = max(straights)
            return 50000 + highest_card_of_largest_straight, f"Straight ({Hand.straight_array_to_str(highest_card_of_largest_straight)})"

        # THREE OF A KIND
        if pairs[3]:
            largest_threesome = max(pairs[3])
            return 40000 + largest_threesome, f"Three of a Kind (3x {Card.rank_tier_to_str(largest_threesome)})"

        # TWO PAIR
        if len(pairs[2]) >= 2:
            largest_pair = max(pairs[2])
            second_largest_pair = max(pairs[2].difference({largest_pair}))
            kicker = max(set(rank_to_suits).difference({largest_pair}).difference({second_largest_pair}))
            s = f"Two Pair (2x {Card.rank_tier_to_str(largest_pair)}, 2x {Card.rank_tier_to_str(second_largest_pair)}, kicker {Card.rank_tier_to_str(kicker)})"
            return 30000 + largest_pair * 100 + second_largest_pair * 10 + kicker, s

        # ONE PAIR
        if pairs[2]:
            largest_pair = max(pairs[2])
            kicker = max(set(rank_to_suits).difference({largest_pair}))
            return 20000 + largest_pair * 10 + kicker, f"One Pair (2x {Card.rank_tier_to_str(largest_pair)}, kicker {Card.rank_tier_to_str(kicker)})"

        # HIGH CARD
        high_card = max(rank_to_suits)
        return high_card, f"High Card ({Card.rank_tier_to_str(high_card)})"
            
if __name__ == "__main__":
    deck = Deck()
    hands = [
        Hand([
            Card("Spades", i) for i in (10, "Jack", "Queen", "King", 9)
        ]),
        Hand([
            Card("Spades", 2),
            Card("Diamonds", 2),
            Card("Spades", 4),
            Card("Hearts", 4),
            Card("Diamonds", "Ace")
        ]),
        Hand([Card(suit, 4) for suit in Deck.SUITS] + [Card("Diamonds", 9), Card("Spades", "Ace")]),
        Hand([
            Card("Diamonds", "Ace"),
            Card("Spades", "Ace"),
            Card("Spades", 3)
        ]),
        Hand([
            Card("Diamonds", 5),
            Card("Diamonds", "Ace"),
            Card("Diamonds", 2),
            Card("Diamonds", 3),
            Card("Diamonds", "Jack")
        ])
    ]
    correct_values = [
        "Straight Flush (9-10-Jack-Queen-King)",
        "Two Pair (2x 4, 2x 2, kicker Ace)",
        "Four of a Kind (4x 4, Ace kicker)",
        "One Pair (2x Ace, kicker 3)",
        "Flush (5x Diamonds, high card Ace)"
    ]
    for i, hand in enumerate(hands):
        val, s = hand.poker_value()
        if i < len(correct_values):
            assert s == correct_values[i]
        print(s)