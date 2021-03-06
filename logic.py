# Copyright 2018 Paul Kutrich. All rights reserved.

from collections import Counter
from scoring_rules import scoring_rules


class Game:

    """The nuts and bolts of the game.

    Methods for instantiating players in player_list, game rules, scoring, taking turns, choosing a winner, and ending
    the game.

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
            self.player_list.append(Player(name))
        return self.player_list

    @staticmethod
    def is_three_pair(choice):
        choice = sorted(choice)
        return (len(choice) == 6 and
                choice[0] == choice[1] and
                choice[2] == choice[3] and
                choice[4] == choice[5] and
                (choice[0] != choice[2] and choice[0] != choice[4]) and
                choice[2] != choice[4])

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
        return errors

    def choose_dice(self, roll):
        """Choose dice according to scoring rules. Boop Beep.

        :param roll: List. Dice to choose from.
        :return: List. Dice chosen.
        """
        nums = [int(die.id) for die in roll]
        counts = Counter(nums)
        if Game.is_three_pair(nums) and \
                sum(scoring_rules[die - 1][count - 1]
                    for die, count in counts.items()) < 1500:
            choice = roll
        elif Game.is_straight(nums):
            choice = roll
        else:
            temp = [die for die, count in counts.items() for _ in range(count)
                    if scoring_rules[die - 1][count - 1] > 0]
            choice = [die for die in roll if int(die.id) in temp]
        return choice


class Player(object):

    """Simple base class for Player objects.

    Players have a total score, round score, and name.

    """
    def __init__(self, name):
        """Player objects instantiated with total score, round score, and name.

        :param name: From Game.set_player.
        """
        self.total_score = 0
        self.round_score = 0
        self.basket_score = 0
        self.name = name
        self.score_display = None
        self.info = None
        self.comp_player = False
        self.first_turn = True


def main():
    pass


if __name__ == "__main__":
    main()
