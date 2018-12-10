# Copyright 2018 Paul Kutrich. All rights reserved.

from random import randint
from collections import Counter
from scoring_rules import scoring_rules, overlord_scoring_rules

msg = '''
                    Welcome to Ten Thousand
                           The Game!
Objective:
    Score 10,000 points.
    Any turn in which a player ends with more than 10,000 points will be the 
    final turn.
    If multiple players finish with more than 10,000 points, the winner is the
    player with the most points.

To score:
    1's and 5's are worth 100 and 50 points respectively.
    Three-of-a-kind is worth the die number x 100. (Three 1's is 1000 points)
    Four-of-a-kind is worth double the same Three-of-a-kind.
    Five-of-a-kind is double Four-of-a-kind.
    Six of any number is worth 5000 points.
    A six dice straight is worth 1500 points.
    Three pairs are also worth 1500 points.

To play:
    Your dice will appear in [brackets].
    Choose your dice by the reference number located above your dice.
    You must choose at least one scoring die per throw. If no scoring die are
    thrown your turn is over and your score for the turn will be zero.
    You must score at least 500 points in one turn to get on the board.
    If you get six keepers in a turn, you may choose to roll all dice again.
    You'll press Enter a lot. Sorry about that. There will be graphics soon.
    Have fun and thanks for helping me develop my first app!!
'''


class Game:

    """The nuts and bolts of the game.

    Methods for instantiating players in player_list, game rules, scoring,
    taking turns, choosing a winner, and ending the game.

    """

    def __init__(self, name_list):
        """Begins Game by creating list of Player objects.

        Calls Game.set_player.
        """
        self.player_list = []
        self.set_player(name_list)

    def set_player(self, name_list):
        """Sets number of players and player names. Adds computer player if desired.

        Instantiates number of Player indicated by user input. Names players as entered by user.

        :return: List of Player objects
        """
        for name in name_list:
            self.player_list.append(HumanPlayer(name))
        return self.player_list

    @staticmethod
    def is_three_pair(choice):
        choice = sorted(choice)
        return len(choice) == 6 and choice[0] == choice[1] and choice[2] == choice[3] and choice[4] == choice[5]

    @staticmethod
    def is_straight(choice):
        return sorted(choice) == list(range(1, 7))

    def keep_score(self, choice):
        """Scores choices from choose_dice() according to scoring_rules.

        Ensures highest legal score is used.
        Player informed of end of turn if score is zero.

        :param choice: List of dice chosen from Player.choose_dice.
        :return: integer score
        """
        counts = Counter(choice)
        score = sum(scoring_rules[die - 1][count - 1]
                    for die, count in counts.items())
        if score < 1500:
            if self.is_straight(choice) or self.is_three_pair(choice):
                score = 1500
        elif score == 0:
            print('\nSorry, no keepers. That ends your turn.'
                  '\nYour score for this round is: 0')
            return 0
        return score

    def turn(self, player):
        """One player turn.

        Updates total scores. Sets thresholds for ComPlayer ending its turns.
        Calls Player.choose_dice and Game.keep_score.

        :param player: Player object.
        """
        round_score, keepers = 0, 0
        while True:
            roll = [randint(1, 6) for _ in range(6 - keepers)]
            print(f'\n{player.name}, your dice in []'
                  '\n 1  2  3  4  5  6'
                  f'\n{roll}')
            choice = player.choose_dice(roll)
            print(f'\nHere are your choices: {choice}')
            score = self.keep_score(choice)
            if score == 0:
                break
            print(f'\nScore for this throw is: {score}')
            round_score += score
            print(f'\nTotal score for this turn is: {round_score}')
            keepers += len(choice)
            if keepers == 6:
                print('\nSix keepers! Roll \'em again!')
                keepers = 0
            if player.name != 'Digital Overlord':
                again = input('''
Roll again or keep current score?
Enter = Roll, K = Keep'''
                              )
                if r'k' in again.lower():
                    player.total_score += round_score
                    if player.total_score < 500:
                        print('\nScore at least 500 to get on the board.')
                        player.total_score = 0
                        break
                    else:
                        print(f'\n{player.name}\'s score this turn: {round_score}')
                        break
            else:
                if round_score >= 500 and keepers > 2:
                    player.total_score += round_score
                    print(f'\n{player.name}\'s score this turn: {round_score}')
                    break

    def take_turns(self, player_list):
        """Sets winning score, switches between players, prints winner's name and score.

        Calls Game.turn

        :param player_list: List of Player objects.
        """
        while not any(player.total_score >= 10000 for player in player_list):
            for player in player_list:
                self.turn(player)
                for _player in player_list:
                    print(f'\n{_player.name}\'s total score is: {_player.total_score}')
        winner_dict = {}
        for x in range(len(player_list)):
            winner_dict.update({player_list[x].total_score: player_list[x]})
        winner = winner_dict[max(winner_dict.keys())]
        print(f'\nThe winner is {winner.name} with a score of: {winner.total_score}!!')

    def validate_choice(self, choice):
        """Removes errant choices and informs user of error(s) if present.

        :param choice: List. User choices before validating
        :return: List. User choices sans errors."""
        counts = Counter(choice)
        if Game.is_three_pair(choice) and \
                sum(scoring_rules[die - 1][count - 1]
                    for die, count in counts.items()) < 1500:
            return []
        if Game.is_straight(choice):
            return []
        else:
            errors = []
            for die, count in counts.items():
                if (scoring_rules[die - 1][count - 1] == 0 and not
                        Game.is_straight(choice) and not
                        Game.is_three_pair(choice)):
                    errors.append(die)
        # for error in errors:
        #     print(f'\nYou must have three {error}\'s to score. '
        #           'Let\'s put that back.')
        # choice = [die for die, count in counts.items()
        #           for _ in range(count)
        #           if scoring_rules[die - 1][count - 1] > 0]
        return errors


class Player(object):

    """Simple base class for Player objects.

    Players have a total score and name.

    """
    def __init__(self, name):
        """Player objects instantiated with total score and name.

        :param name: From Game.set_player.
        """
        self.total_score = 0
        self.round_score = 0
        self.name = name


class HumanPlayer(Player):

    """Human Player objects inherits from Player base class.

    Methods for obtaining user input and input validation.

    """

    def _get_user_choice(self):
        """Adjusts user input for indexing. Returns input if valid.

        :return: int. User choice adjusted for zero indexing.
        """
        try:
            choose = int(input('''
Choose which die to keep by position 1-6
Type position number, then enter. Repeat for all choices.
Press enter when finished
'''
                               ))
        except ValueError:
            return None
        return choose - 1

    def choose_dice(self, roll):
        """Ensures user input refers to a valid choice.

        Calls get_user_choice().
        Calls validate_choice().
        :param roll: List. Dice user can choose from.
        :return: List. validated user choices.
        """
        choice_list = []
        while True:
            choose = self._get_user_choice()
            if choose is None:  # From user pressing enter to stop choosing dice.
                break
            if choose >= len(roll):
                print(f'\n{choose + 1} not available\n')
                continue
            if choose in choice_list:
                print('\nYou may choose a die only once.\n')
                continue
            choice_list.append(choose)
        choice = [roll[x] for x in choice_list]
        return self._validate_choice(choice)



class ComPlayer(Player):

    """Computer player with method for choosing dice.

    Inherits from Player base class.

    """

    def choose_dice(self, roll):
        """Choose dice according to scoring rules. Boop Beep.

        :param roll: List. Dice to choose from.
        :return: List. Dice chosen.
        """
        counts = Counter(roll)
        if Game.is_three_pair(roll) and \
                sum(overlord_scoring_rules[die - 1][count - 1]
                    for die, count in counts.items()) < 1500:
            choice = roll
        elif Game.is_straight(roll):
            choice = roll
        else:
            choice = [die for die, count in counts.items() for _ in range(count)
                      if overlord_scoring_rules[die - 1][count - 1] > 0]
        return choice


def main():
    print(msg)
    while True:
        game = Game()
        game.take_turns(game.player_list)
        replay = input('\nWould you like to play again? y/n')
        if r'n' in replay.lower():
            print('Thanks for playing!!')
            break


if __name__ == "__main__":
    main()
