import random
from typing import Dict, List, Tuple
import numpy as np
from components.deck import Deck, NUM_UNIQUE_CARDS, NUM_REPLICAS
from components.player import Player

"""
QS/Things to Decide-Do-Discuss:

- [ ] Decide on the reward. Are we going to do sparse reward like end game +1/-1 or should we do
    intermediate rewards like +1 for each successful challenge and -1 for each failed challenge, or
    if the cards at hand +x/-x.
- Not sure about the history. Do we only need the action history, or do we also add some other
    information to the history? The information state should be Markovian so shouldn't we also need
    some state history?
    - I think "history" should not exist. We should have information_history or something that will
        be used by the players (history of the game in their perspective). But we also need a state
        history that will have all the game information.
"""


"""
We have a complicated action representation in Cheat since there is a large action space.

The important thing to note is that we have 2 different version of action representation. Because
we are using a state representation and the state includes action history. We want the state to be
as packed as possible. On the other hand we have the action representation that should be output of
the neural network, so the only reasonable way of having this is to have a one-hot encoding of the
action space. So we need to convert between these two representations. Here is a brief explanation
of the action space in both representations:

State Action Representation (History Saving):
    - The number of cards to declare (1-4) in a scalar value.
    - The rank being declared in a scalar value.
    - The cards being played in a vector of length 13, where each element represents the number of
        cards of a particular rank being played.
    - Whether the player is challenging the previous player's claim (0 or 1).

    So total length of the action space is 1 + 1 + 13 + 1 = 16

Action Representation (One-Hot Encoding):
    - The number of cards to declare (1-4) in a one-hot encoding format.
        [1, 0, 0, 0] -> 1 card, [0, 1, 0, 0] -> 2 cards, etc.
    - The rank being declared in a one-hot encoding format. This is a 13-dimensional vector where
        each element corresponds to a different rank.
    - The cards being played in a sparse one-hot encoding format. This is a 4x13 matrix where each
        row corresponds to a card being played and columns correspond to the rank of the card. So
        an Ace would be [0, 0, ..., 0, 1].
    - Whether the player is challenging the previous player's claim (0 or 1).

    So total length of the action space is 4 + 13 + 4*13 + 1 = 66
"""

class CheatGame:
    def __init__(self, num_players: int = 2, num_rounds: int = 50):
        self.num_players = num_players
        self.players = [Player(f"Player {i}") for i in range(self.num_players)]
        self.deck = Deck()

        self.max_number_of_rounds = num_rounds

        self.invalid_penalty = -99

        self.player_hand_size = NUM_UNIQUE_CARDS
        self.max_unique_pile_len = NUM_UNIQUE_CARDS

        # (players action space + opponents turn exposure) * max number of rounds
        # (action_repr (16 - explained on top) + action_repr without cards (3)) * max_rounds
        self.max_history_len = (
            (2 + NUM_UNIQUE_CARDS + 1) + 3
        ) * self.max_number_of_rounds

        # Maximum info_state size
        self.state_space = len(self.players[0].hand) + self.max_history_len

        self.action_space = None  # This should be handled differently since:
        # Each round we have 4 different actions (4 different heads for NN):
        #   - Number of cards to declare (1-4)
        #   - Rank being declared (2-14)
        #   - Cards being played (4 cards)
        #   - Whether the player is challenging the previous player's claim (0 or 1)
        self.reset()

    def reset(self) -> List[int]:
        """Reset the game state and return the initial information state.

        Returns:
            List[int]: The initial information state.
        """
        self.num_rounds = 0
        self.deck.shuffle()
        for player in self.players:
            player.reset()
            player.hand = self.deck.deal(len(self.deck) // self.num_players)

        self.state = np.array(
            [], dtype=int
        )  # empty state - we are using padding for stability
        self.player_history = [np.array([], dtype=int) for _ in range(self.num_players)]

        self.current_player = 0
        self.central_pile = np.zeros(NUM_UNIQUE_CARDS, dtype=int)
        self.if_last_claim_bluff = False

        self.done = False

        return self.get_info_state()

    def get_info_state(self) -> np.array:
        """Get the current information state.

        An information state consists of the following components:
            - The current player's hand. This is vector of length 13, where each element represents
                the number of cards of a particular rank in the player's hand.
            - The action history. This is the sequence of actions that have been played in the game
                so far that the player has knowledge of. This is a vector of length max_history_len
                for stability (Neural Networks expect fixed input sizes).

        Returns:
            np.array: The current information state.
        """
        pad_len = self.max_history_len - len(self.player_history[self.current_player])
        return np.concatenate(
            [
                self.players[self.current_player].hand,
                np.pad(
                    self.player_history[self.current_player],
                    (0, pad_len),
                    mode="constant",
                ),
            ]
        )

    def output_actions_to_history_actions(self, actions: np.array) -> np.array:
        """Convert the output actions to history actions.

        ! The difference between the two representation is stated on the top of the file.

        Args:
            actions (np.array): The output actions from the neural network.

        Returns:
            np.array: The history actions.
        """
        # Convert the number of cards to declare to a scalar value
        num_cards_to_declare = np.argmax(actions[:4])

        # Convert the rank being declared to a scalar value
        rank_declared = (
            np.argmax(actions[4:17]) + 2
        )  # Ranks start from 2 (Ace is 14, 2 is 2, etc.)

        # Convert the cards being played to a vector of length 13
        cards_played = np.zeros(NUM_UNIQUE_CARDS, dtype=int)
        for i in range(4):
            cards_played += actions[17 + i * 13 : 17 + (i + 1) * 13]

        # Convert whether the player is challenging the previous player's claim to a scalar value
        challenge = np.argmax(actions[-1])

        return np.concatenate(
            [num_cards_to_declare, rank_declared, cards_played, challenge]
        )

    def step(self, actions: np.array) -> Tuple[List[int], int, bool, Dict]:
        """Take a step in the environment given an action.

        Args:
            actions (np.array): The action taken by the player. The actions are multi-dimensional.
                Each dimension corresponds to a different component of the action space. The
                components are:
                    - The number of cards to declare (1-4) in a one-hot encoding format.
                        [1, 0, 0, 0] -> 1 card, [0, 1, 0, 0] -> 2 cards, etc.
                    - The rank being declared in a one-hot encoding format. This is a 13-dimensional
                        vector where each element corresponds to a different rank.
                    - The cards being played in a sparse one-hot encoding format. This is a 4x13
                        matrix where each row corresponds to a card being played and columns
                        correspond to the rank of the card. So an Ace would be [0, 0, ..., 0, 1].
                    - Whether the player is challenging the previous player's claim (0 or 1).
        Returns:
            Tuple[List[int], int, bool, Dict]: A tuple containing the following elements:
                - The information state for the next player.
                - The reward for the current player.
                - Whether the game is over.
                - Additional information.
        """
        assert not self.done, "Game is already over. Please reset the game."

        action_repr = self.output_actions_to_history_actions(actions)

        selected_suite = action_repr[0]
        selected_rank = action_repr[1]
        selected_cards = action_repr[2:15]
        challenge = action_repr[-1]

        # Update the number of rounds
        self.num_rounds += 1

        # Check if the action is valid / if not return PENALTY reward
        if not self.is_valid_action(
            selected_suite, selected_rank, selected_cards, challenge
        ):
            return (
                self.get_info_state(),
                self.invalid_penalty,
                self.done,
                {},
            )

        # update history
        self.state = np.append(self.state, action_repr)
        self.player_history[self.current_player] = np.append(
            self.player_history[self.current_player], action_repr
        )
        # opponent also gets exposed to partial information
        self.player_history[1 - self.current_player] = np.append(
            self.player_history[1 - self.current_player],
            np.concatenate([selected_suite, selected_rank, challenge]),
        )

        # check if challenge
        if challenge:
            self.resolve_challenge()
        else:
            # update players hand
            self.players[self.current_player].remove_cards(selected_cards)

            # update central pile
            self.add_to_pile(selected_cards)

            # Check if bluff
            if self.is_bluff(selected_suite, selected_rank, selected_cards):
                self.if_last_claim_bluff = True

        # check for terminal state
        if self.is_terminal():
            self.done = True  # For stopping recalling step()
        else:
            # update current player
            self.next_player()

        return (
            self.get_info_state(),
            self.get_reward(self.current_player),
            self.done,
            {},
        )
    # Move to the next player
    def next_player(self) -> None:
        """Update the current player to the next player."""
        self.current_player = (self.current_player + 1) % len(self.players)

    def add_to_pile(self, cards: np.array) -> None:
        """Add cards to the central pile.

        Args:
            cards (np.array): The cards to add to the central pile.
        """
        assert len(cards) == NUM_UNIQUE_CARDS, "Invalid cards representation."
        self.central_pile += cards

    def is_bluff(
        self, selected_suite: int, selected_rank: int, selected_cards: np.array
    ) -> bool:
        """Checks if the action was a bluff.

        Looks at the selected_suite and the selected_rank and compares it to the actual cards
        played. If the cards match the claim, then it was not a bluff.

        Args:
            selected_suite (int): The selected suite.
            selected_rank (int): The selected rank.
            selected_cards (np.array): The selected cards.

        Returns:
            bool: True if the last claim was a bluff, False otherwise.
        """
        idxs = np.where(selected_cards > 0)[0]  # indexes of the selected cards
        if idxs > 1:  # player cannot play more than 1 card so this is a bluff
            return True
        idx = idxs[0]
        return idx != selected_rank - 2

    def resolve_challenge(self) -> None:
        """Resolves if the previous player's claim was a bluff or not.

        If the previous player's claim was a bluff, the previous player receives the central pile.
        Otherwise, the challenging player receives the central pile.
        """
        if self.if_last_claim_bluff:
            self.players[1 - self.current_player].add_cards(
                self.central_pile
            )  # ! Assumes 2 players
        else:
            self.players[self.current_player].add_cards(self.central_pile)

        # reset central pile
        self.central_pile = np.zeros(NUM_UNIQUE_CARDS, dtype=int)

    def is_terminal(self) -> bool:
        """Check if the game is in a terminal state.

        The game ends if either player has no cards left in their hand, or if the number of rounds
        exceeds the maximum number of rounds.

        Returns:
            bool: True if the game is in a terminal state, False otherwise.
        """
        return self.num_rounds >= self.max_number_of_rounds or any(
            len(player.hand) == 0 for player in self.players
        )

    def get_reward(self, player_idx: int) -> int:
        """Get the reward for the player.

        The reward is +1 if the player wins, -1 if the player loses, and 0 if the game is a draw.
        ! Check discussion on top of the file for more reward options.

        Args:
            player_idx (int): The index of the player.

        Returns:
            int: The reward for the player.
        """
        if (
            self.done
        ):  # game is over - this doesn't necessarily have to be a reward condition
            return (
                1
                if len(self.players[player_idx].hand)
                > len(self.players[1 - player_idx].hand)
                else -1
            )
        return 0

    def is_valid_action(
        self,
        selected_suite: int,
        selected_rank: int,
        selected_cards: np.array,
        challenge: int,
    ) -> bool:
        """Check if the action is valid.

        The action is valid if:
            - The selected cards are in the player's hand
            - The number of cards selected is equal to the number of cards declared.
            - This is not a second challenge in a row.
            - If challanged, there is a previous claim - aka. an action has been taken.

        Args:
            selected_suite (int): The selected suite.
            selected_rank (int): The selected rank.
            selected_cards (np.array): The selected cards.
            challenge (int): Whether the player is challenging the previous player's claim.

        Returns:
            bool: True if the action is valid, False otherwise.
        """
        # check if the selected cards are in the player's hand
        if not np.all(selected_cards <= self.players[self.current_player].hand):
            return False

        # check if the number of cards selected is equal to the number of cards declared
        if np.sum(selected_cards) != selected_suite:
            return False

        # check if challenged
        if challenge:
            if len(self.state) == 0:
                return False
            if self.state[-1] == 1:
                return False
        return True