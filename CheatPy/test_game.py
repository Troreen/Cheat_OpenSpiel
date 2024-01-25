import unittest
from Cheat import Card, Deck, Player, GameState

class TestCard(unittest.TestCase):

    def test_card_init(self):
        card = Card('A', 'H')
        self.assertEqual(card.rank, 'A')
        self.assertEqual(card.suit, 'H')

        with self.assertRaises(ValueError):
            card = Card('1', 'H') # Invalid rank

        with self.assertRaises(ValueError):
            card = Card('4', 'B') # Invalid suit

    def test_card_string_representation(self):
        card = Card('A', 'H')
        self.assertEqual(str(card), 'AH')

    def test_card_equality(self):
        card1 = Card('A', 'H')
        card2 = Card('A', 'H')
        card3 = Card('K', 'H')
        self.assertTrue(card1 == card2)
        self.assertFalse(card1 == card3)

    def test_card_comparison(self):
        card1 = Card('A', 'H')
        card2 = Card('K', 'H')
        self.assertTrue(card1 > card2)
        self.assertFalse(card1 < card2)
    
    def test_hash_consistency(self):
        # Test that the hash of a card is consistent.
        card = Card('A', 'H')
        initial_hash = hash(card)
        for _ in range(10):
            self.assertEqual(hash(card), initial_hash)

    def test_hash_uniqueness(self):
        # Test that different cards have unique hashes.
        cards = [Card(rank, suit) for suit in ['H', 'D', 'S', 'C'] for rank in Card.rank_values]
        unique_hashes = len(set(hash(card) for card in cards))
        self.assertEqual(unique_hashes, len(cards))

    def test_equal_cards_same_hash(self):
        # Test that two equal cards have the same hash.
        card1 = Card('K', 'D')
        card2 = Card('K', 'D')
        self.assertEqual(hash(card1), hash(card2))

    def test_card_set_behavior(self):
        # Test cards in a set for correct behavior.
        card_set = {Card('Q', 'S'), Card('Q', 'S')}
        self.assertEqual(len(card_set), 1)

class TestDeck(unittest.TestCase):

    def test_deck_init(self):
        deck = Deck()
        self.assertEqual(len(deck), 52)
        deck = Deck() + Deck()
        self.assertEqual(len(deck), 104)
        deck = Deck() + Deck() + Deck()
        self.assertEqual(len(deck), 156)

    def test_deck_string_representation(self):
        deck = Deck()
        self.assertEqual(str(deck), 'Deck of 52 cards')

    def test_deck_shuffle(self):
        deck = Deck()
        cards_before_shuffle = deck.cards[:]
        deck.shuffle()
        self.assertNotEqual(cards_before_shuffle, deck.cards) # Order should change

    def test_deck_deal(self):
        deck = Deck()
        dealt_cards = deck.deal(5)
        self.assertEqual(len(dealt_cards), 5) # Check if 5 cards are dealt
        self.assertEqual(len(deck), 47) # Deck should have 47 cards left
        

    def test_deck_is_empty(self):
        deck = Deck()
        self.assertFalse(deck.is_empty()) # Deck should not be empty
        deck.deal(52) # Deal all cards
        self.assertTrue(deck.is_empty()) # Deck should be empty
    
    def test_shuffle_not_full_deck(self):
        deck = Deck()
        deck.deal(1)
        with self.assertRaises(ValueError):
            deck.shuffle() # Should rause ValueError as deck is not full


class TestPlayer(unittest.TestCase):

    def setUp(self):
        self.player = Player('TestPlayer')
        self.cards = [Card('A', 'H'), Card('K', 'H'), Card('Q', 'H')]

    def test_receive_cards(self):
        self.player.receive_cards(self.cards)
        self.assertEqual(len(self.player.hand), 3) # Player should have 3 cards

    def test_play_cards_valid(self):
        self.player.receive_cards(self.cards)
        played_cards, success = self.player.play_cards([self.cards[0]], 'A', 1)
        self.assertTrue(success)
        self.assertEqual(len(self.player.hand), 2) # Player should have 2 cards

    def test_play_cards_invalid_number(self):
        self.player.receive_cards(self.cards)
        played_cards, success = self.player.play_cards([self.cards[0]], 'A', 2)
        self.assertFalse(success) # Playing 1 card while claiming 2 is invalid

    def test_play_cards_invalid_card(self):
        self.player.receive_cards(self.cards)
        invalid_card = Card('2', 'C')
        played_cards, success = self.player.play_cards([invalid_card], '2', 1)
        self.assertFalse(success) # Cannot play a card that is not in hand

    def test_show_hand(self):
        self.player.receive_cards(self.cards)
        hand_representation = self.player.show_hand()
        expected_representation = 'AH, KH, QH'
        self.assertEqual(hand_representation, expected_representation)


class TestGameState(unittest.TestCase):

    def setUp(self):
        self.players = [Player(f"Player {i+1}") for i in range(2)] # Create 2 players for simplicity
        self.game_state = GameState(self.players)

         # Giving each player some cards
        self.cards_p1 = [Card('A', 'H'), Card('K', 'D')]
        self.cards_p2 = [Card('5', 'S'), Card('2', 'C')]
        self.players[0].receive_cards(self.cards_p1)
        self.players[1].receive_cards(self.cards_p2)
    
    def test_next_player(self):
        self.game_state.next_player()
        self.assertEqual(self.game_state.current_player_index, 1) # Player 2 should be next 

    def test_add_to_pile(self):
        self.game_state.add_to_pile(self.cards_p1)
        self.assertEqual(len(self.game_state.central_pile), 2)
    
    def test_challenge(self):
        self.game_state.add_to_pile([Card('A', 'H'), Card('A', 'D')])
        self.game_state.current_claim = ('A', 2)
        self.assertTrue(self.game_state.challenge() is False)  # Correct claim

        self.game_state.central_pile.append(Card('2', 'H'))  # Add incorrect card
        self.assertTrue(self.game_state.challenge() is True)  # Incorrect claim

    def test_resolve_challenge(self):
        self.game_state.add_to_pile(self.cards_p1)
        self.game_state.resolve_challenge(True, self.players[1]) # Player 2 wins challenge
        self.assertEqual(len(self.players[0].hand), 4) # Player 1 should recieve the pile, having 4 cards now

    def test_check_winner(self):
        self.players[0].hand = [] # Player 1 has no cards
        self.assertTrue(self.game_state.check_winner() is self.players[0])

    def test_valid_claim(self):
        player = self.players[0]
        claimed_cards = [Card('A', 'H'), Card('A', 'D')]
        player.receive_cards(claimed_cards)
        self.game_state.make_claim(player, 'A', 2)
    
        played_cards, success = player.play_cards(claimed_cards, 'A', 2)
        self.assertTrue(success)
        self.game_state.add_to_pile(played_cards)
    
        self.assertFalse(self.game_state.challenge())  # No challenge should be successful for a valid claim

    def test_invalid_claim(self):
        player = self.players[0]
        claimed_cards = [Card('A', 'H'), Card('K', 'D')]
        player.receive_cards(claimed_cards)
        self.game_state.make_claim(player, 'A', 2)
    
        played_cards, success = player.play_cards(claimed_cards, 'A', 2)
        self.assertTrue(success)
        self.game_state.add_to_pile(played_cards)
    
        self.assertTrue(self.game_state.challenge())  # Challenge should be successful for an invalid claim



if __name__ == '__main__':
    unittest.main()

