import random
import numpy as np

NUM_UNIQUE_CARDS = 13
NUM_REPLICAS = 4

class Deck:
    def __init__(self):
        self.cards: np.array = np.array([NUM_UNIQUE_CARDS] * NUM_REPLICAS, dtype=int)

    def _len_(self) -> int:
        """Returns the number of cards in the deck
        
        Returns:
            int: number of cards in the deck
        """
        return sum(self.cards)
    
    # Shuffle the deck
    def shuffle(self):
        if len(self) < 52:
            raise ValueError("Only full decks can be shuffled")
        random.shuffle(self.cards)
    
    # Deal a card from the deck
    def deal(self, num_cards=1):
        if len(self) < num_cards:
            raise ValueError("Not enough cards in the deck")
        return [self.cards.pop() for _ in range(num_cards)]
    
    # Check if deck is empty
    def is_empty(self):
        return len(self.cards) == 0
    
    # Add decks together
    def _add_(self, other):
        if isinstance(other, Deck):
            combined_deck = Deck()
            combined_deck.cards = self.cards + other.cards
            return combined_deck
        else:
            raise ValueError("Only decks can be added together")