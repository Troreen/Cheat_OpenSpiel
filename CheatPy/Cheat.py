import random
from typing import Dict, List, Tuple
class Card: 
    # Mapping ranks to numerical values for comparison
    rank_values = {
        '2':2, 
        '3':3, 
        '4':4, 
        '5':5, 
        '6':6, 
        '7':7, 
        '8':8, 
        '9':9, 
        'T':10,                     
        'J':11, 
        'Q':12, 
        'K':13, 
        'A':14
    }
    
    # Initialize card with rank and suit
    def __init__(self, rank, suit):
        if suit not in ['H', 'D', 'S', 'C']:
            raise ValueError("Invalid suit")
        if rank not in Card.rank_values.keys():
            raise ValueError("Invalid rank")
        
        self.suit = suit
        self.rank = rank

    # Return string representation of card
    def __str__(self):
        return f"{self.rank}{self.suit}"
    
    # Check if two cards are equal
    def __eq__(self, other):
        return self.rank == other.rank and self.suit == other.suit
    
    # Check if one card is less than another card
    def __lt__(self, other):
        return Card.rank_values[self.rank] < Card.rank_values[other.rank]
    
    # Return a hash for the card
    def __hash__(self):
        return hash((self.rank, self.suit))
    
class Deck:
    # Initialize deck with a standard set of cards
    def __init__(self):
        self.cards = [
            Card(rank, suit) 
            for suit in ['H', 'D', 'S', 'C'] 
            for rank in Card.rank_values
        ]
    
    # Return string representation of deck
    def __str__(self):
        return f"Deck of {len(self.cards)} cards"
    
    # Return the number of cards in the deck
    def __len__(self):
        return len(self.cards)
    
    # Shuffle the deck
    def shuffle(self):
        if len(self) < 52:
            raise ValueError("Only full decks can be shuffled")
        random.shuffle(self.cards)

    # Deal cards from the deck
    def deal(self, num_cards=1):
        if len(self) < num_cards:
            raise ValueError("Not enough cards in deck to deal")
        return [self.cards.pop() for _ in range(num_cards)]
    
    # Check if deck is empty
    def is_empty(self):
        return len(self.cards) == 0
    
    # Add decks together
    def __add__(self, other):
        if isinstance(other, Deck):
            combined_deck = Deck()
            combined_deck.cards = self.cards + other.cards
            return combined_deck
        else:
            raise ValueError("Only decks can be added together")
    
class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []
    
    # Adds cards to player's hand
    def receive_cards(self, cards):
        self.hand.extend(cards)

    def play_cards(self, cards_to_play, claim, number):
        '''
        :param cards_to_play: List of Card objects that the player is actually playing.
        :param claim: The rank the player claims the cards to be.
        :param number: The number of cards the player is claiming to play.
        :return: Tuple of (played cards, success flag)
        '''
        if len(cards_to_play) != number:
            return [], False # Number of cards played doesnt match the claim
        
        for card in cards_to_play:
            if card not in self.hand:
                return [], False # Player tried to play a card they dont have
        
        for card in cards_to_play:
            self.hand.remove(card)

        return cards_to_play, True


    def show_hand(self):
        return ', '.join(str(card) for card in self.hand)
    
class CheatGame:
    def __init__(self, num_players: int, num_rounds: int = 50):
        self.num_players = num_players
        self.players = [Player(f"Player {i}") for i in range(self.num_players)]
        self.deck = Deck()

        self.max_player_unique_hand_len = self.deck.unique_cards
        self.max_unique_pile_len = self.deck.unique_cards
        self.max_history_len = self.num_players**2 * num_rounds

        # +1 for last claim, +num_players for each player deciding to challenge or not
        #self.max_player_hand_len*num_players + self.max_pile_len + 1 + num_players 
        
        # Maximum info_state size
        # TODO: Continue here
        self.state_space = {
            self.max_player_unique_hand_len*self.num_players 
            }
           
          # players card + history len + players bet + opponents bet
        self.action_space = 2  # pass or bet

        self.reset()

    def reset(self) -> List[int]:
        """Reset the game state and return the initial information state.

        Returns:
            List[int]: The initial information state.
        """
        self.deck.shuffle()
        for player in self.players:
            player.hand = self.deck.deal(len(self.deck) // self.num_players)  # TODO: Dealing has to be fixed for uneven numbers
        
        self.history = []
        self.player_info_states = [[] for _ in range(self.num_players)]  

        self.current_player = 0
        self.central_pile = []
        self.current_claim = None

        self.state = [self.current_player]
        for player in self.players:
            


        return self.get_info_state()

    def get_info_state(self) -> List[int]:
        """Get the current information state.

        Returns:
            List[int]: The current information state.
        """
        # 
    def step(self, action: int) -> Tuple[List[int], int, bool, Dict]:

        return
    430410

    # Move to the next player
    def next_player(self):
        self.current_player = (self.current_player + 1) % len(self.players)

    # Add cards to the central pile
    def add_to_pile(self, cards):
        self.central_pile.extend(cards)

    def make_claim(self, player, claim, number):
        '''
        Player makes a claim about the cards they are playing.

        :param player: The player making the claim.
        :param claim: The rank the player is claiming.
        :param number: The number of cards the player is claiming to play.
        return: True if the claim is valid, False otherwise.
        '''
        self.current_claim = (claim, number)
        print(f"{player.name} claims to be playing {number} card(s) of rank {claim}.")

    # Handle a challenge. Return True if the challenger wins, False otherwise.
    def challenge(self):
        if not self.central_pile or not self.current_claim:
            return None

        # Extract the last set of played cards
        last_played = self.central_pile[-1]

        # Ensure last_played is a list of cards
        if not isinstance(last_played, list):
            last_played = [last_played]

        claimed_rank, _ = self.current_claim
        if all(card.rank == claimed_rank for card in last_played):
            return False  # Challenger loses
        else:
            return True  # Challenger wins
        
    # Resolve a challenge
    def resolve_challenge(self, challenge_result, challenger):
        loser = self.players[self.current_player] if challenge_result else challenger
        loser.receive_cards(self.central_pile)
        self.central_pile = []  # Clear the central pile


    # Check if a player has won
    def check_winner(self):
        for player in self.players:
            if not player.hand:
                return player
        return None
    
def main():
    # Create players
    num_players = int(input("Enter the number of players: "))
    players = [Player(f"Player {i+1}") for i in range(num_players)]

    # Determine the number of decks needed based on player count (52 cards per set of 4 players)
    num_decks = 0
    while num_players > 0:
        num_decks += 1
        num_players -= 4

    # Initialize the game state
    game_state = GameState(players)

    # Create and shuffle the deck
    deck = Deck()
    for _ in range(1, num_decks):
        deck += Deck()
    deck.shuffle()

    # Deal cards to players
    while not deck.is_empty():
        for player in players:
            if deck.is_empty():
                break
            player.receive_cards(deck.deal(1))

    # Game loop
    while not game_state.check_winner():
        current_player = players[game_state.current_player]
        print(f"\n{current_player.name}'s turn.")

        # Display current player's hand
        print(f"Your hand: {current_player.show_hand()}")

        # Player chooses number of cards to play
        num_cards_to_play = int(input("How many cards do you want to play? "))

        # Player selects cards to play
        cards_to_play = []
        for i in range(num_cards_to_play):
            card_str = input(f"Enter card {i+1} to play (e.g., 'AH' for Ace of Hearts): ")
            rank, suit = card_str[:-1], card_str[-1]
            cards_to_play.append(Card(rank, suit))

        # Player makes a claim
        claim = input("Enter the rank you claim these cards to be (e.g., 'A' for Aces): ")

        # Process played cards
        played_cards, success = current_player.play_cards(cards_to_play, claim, num_cards_to_play)
        if not success:
            print("Invalid play. Please try again.")
            continue

        # Add played cards to the pile and make the claim
        game_state.add_to_pile(played_cards)
        game_state.make_claim(current_player, claim, num_cards_to_play)

        # Check for challenges
        for i in range(len(players) - 1):
            challenger_index = (game_state.current_player + i + 1) % len(players)
            challenger = players[challenger_index]
            challenge_input = input(f"{challenger.name}, do you want to challenge {current_player.name}? (y/n) ")
            if challenge_input.lower() == 'y':
                result = game_state.challenge()
                game_state.resolve_challenge(result, challenger)
                break

        # Move to the next player
        game_state.next_player()

    # Declare the winner
    winner = game_state.check_winner()
    print(f"\n{winner.name} has won the game!")

if __name__ == "__main__":
    main()
