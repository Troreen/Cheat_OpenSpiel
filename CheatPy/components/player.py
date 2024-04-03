from deck import NUM_UNIQUE_CARDS
import numpy as np 

class Player:
    def __init__(self, name: str) -> None:
        self.name = name
        self.hand = np.zeros(NUM_UNIQUE_CARDS, dtype=int)

    def add_cards(self, cards: int) -> None:
        """Update the player's hand with the new cards.
        
        Args:
            cards (List[Card]): The cards to add to the player's hand
        """
        self.hand += cards
    
    def remove_cards(self, cards: np.array) -> None:
        """Remove cards from the player's hand.
        
        Args:
            cards (List[Card]): The cards to remove from the player's hand
        """
        self.hand -= cards

    def reset_hand(self) -> None:
        """Reset the player's hand."""
        self.hand = np.zeros(NUM_UNIQUE_CARDS, dtype=int)