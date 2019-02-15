# Copyright 2018 Paul Kutrich. All rights reserved.
import kivy

kivy.require('1.10.1')

from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Rectangle, Color, InstructionGroup
from kivy.properties import ObjectProperty, StringProperty, ListProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scatter import Scatter
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.textinput import TextInput
from kivy.utils import rgba
from kivy.uix.widget import Widget

from collections import deque
from colors import colors
from game_rules import msg1, msg2
from logic import Game
from media import sounds, die_images
from random import randint, uniform


class PlayerNumDropDown(DropDown):

    """A drop down menu for selecting number of players.

    Inherits from DropDown.
    Overrides select method.
    """

    def __init__(self, **kwargs):
        super(PlayerNumDropDown, self).__init__(**kwargs)

    def select(self, num_players: int) -> None:
        """Update PlayerNumberScreen.num_players and close popup.

        :param num_players: number of players
        """
        player_number_screen = [child for child in self.parent.children[1].children][0]
        player_number_screen.num_players = num_players
        self.dismiss()


class BackButton(Button):

    """Button for returning to previous screen."""

    def __init__(self, **kwargs):
        super(BackButton, self).__init__(**kwargs)


class PlayerNumberScreen(Screen):

    """Screen for setting number of players.

    Inherits from Screen.
    Overrides Screen.on_enter.
    """

    num_players = NumericProperty()

    def __init__(self, **kwargs) -> None:
        super(PlayerNumberScreen, self).__init__(**kwargs)

    def on_num_players(self, screen: Screen, num_players: int) -> None:
        """Check num_players is non_zero -> set self.num_players, call set_label

        :param screen: the current Screen.
        :param num_players: number of players.
        """
        if num_players:
            self.num_players = num_players
            self.set_label()

    def on_enter(self) -> None:
        """Set up screen with widgets for setting number of players and optional comp player."""
        if not self.num_players:
            self.cont.disabled = True

        # Make a player_num_button.
        player_num_button = Button(text='SET NUMBER OF PLAYERS',
                                   font_size=75,
                                   size_hint=(.4, .1),
                                   pos_hint={'x': .3, 'y': .65},
                                   background_normal='',
                                   background_color=rgba(colors['prime dark']))
        self.add_widget(player_num_button)

        # Make a drop-down to add to the player_num_button.
        num_drop = PlayerNumDropDown()
        for i, num in zip(list(range(2, 7)), ['TWO', 'THREE', 'FOUR', 'FIVE']):
            btn = Button(text=num,
                         id=str(i),
                         size_hint_y=None,
                         height=125,
                         background_normal='',
                         background_color=rgba(colors['second']))
            # Use the id number to set the number of players.
            btn.bind(on_release=lambda button: num_drop.select(int(button.id)))
            # Add buttons to our drop-down.
            num_drop.add_widget(btn)

        # Finally, open the num_drop drop-down with the player_num_button.
        player_num_button.bind(on_release=num_drop.open)

        add_comp_player = Button(text='COMPUTER FRIEND: N0',
                                 id='compy',
                                 font_size=75,
                                 size_hint=(.4, .1),
                                 pos_hint={'x': .3, 'y': .45},
                                 background_normal='',
                                 background_color=rgba(colors['prime dark']),
                                 on_release=self.set_game_mode)
        self.add_widget(add_comp_player)

    def set_btn_text(self, game_mode: str) -> None:
        """Set text on add_comp_player button.

        :param game_mode: 'comp', 'game' or 'solo'.
        """
        add_comp_player_button = [child for child in self.children if child.id == 'compy'][0]
        if game_mode == 'comp':
            add_comp_player_button.text = 'COMPUTER FRIEND: YES'
        elif game_mode == 'game':
            add_comp_player_button.text = 'COMPUTER FRIEND: NO'

    def set_game_mode(self, *args: list) -> None:
        """Set PlayerNameScreen.game_mode.

        :param args: Unused.
        """
        mode = ''
        name_screen = [screen for screen in self.parent.screens if screen.name == 'name'][0]
        if name_screen.game_mode == 'comp':
            name_screen.game_mode = mode = 'game'
        elif name_screen.game_mode == 'game':
            name_screen.game_mode = mode = 'comp'
        self.set_btn_text(mode)

    def set_label(self) -> None:
        """Set num_label text and enable cont button."""
        texts = {1: 'ONE', 2: 'TWO', 3: 'THREE', 4: 'FOUR', 5: 'FIVE'}
        self.num_label.text = f'Players Selected: {texts[self.num_players]}'
        self.cont.disabled = False

    def to_menu_screen(self) -> None:
        """Reset PlayerNameScreen, PlayerNumberScreen and go to MenuScreen."""
        name_screen = [screen for screen in self.parent.screens if screen.name == 'name'][0]
        name_screen.game_mode = 'game'
        self.num_label.text = 'Players Selected: '
        self.cont.disabled = True
        self.parent.current = 'menu'


class FocusInput(TextInput):

    """Text input box adds player name after text entered if box becomes unfocused.

    Makes entering names easier.
    Inherits from TextInput
    """

    def __init__(self, **kwargs) -> None:
        """Disables write_tab and multiline attributes, sets font_size and  size_hint.

        :param kwargs: Passed to super
        """
        super(FocusInput, self).__init__(**kwargs)

        self.multiline = False
        self.font_size = 60
        self.write_tab = False
        self.size_hint = (.35, .09)

    def on_focus(self, widget: 'FocusInput', invalid: bool) -> None:
        """Call PlayerNameScreen.add_player with value if self.focused is False.

        :param widget: self
        :param invalid: True if gaining focus, False if loosing focus.
        """
        if self.parent and not self.focus:
            self.parent.add_player(widget, invalid)


class PlayerNameScreen(Screen):

    """Screen for setting player names.

    Inherits from Screen.
    Overrides Screen.on_enter.
    """

    player_names = ListProperty()
    active_game = ObjectProperty()
    num_players = NumericProperty()
    game_mode = StringProperty()

    def __init__(self, **kwargs) -> None:
        super(PlayerNameScreen, self).__init__(**kwargs)

    def get_num_players(self) -> None:
        """Get number of players from PlayerNumberScreen."""
        number_screen = [screen for screen in self.parent.screens if screen.name is 'number'][0]
        self.num_players = number_screen.num_players

    def add_player(self, focus_input: 'FocusInput', invalid: bool) -> None:
        """Add player to list of player_names. Call start_game after last player added.

        :param focus_input: a FocusInput object
        :param invalid: True if focus_input gaining focus, else False.
        """
        # Check that we are leaving the text-box and something has been entered before adding a player.
        if not invalid and focus_input.text != '':
            self.player_names.append(focus_input.text)

            if len(self.player_names) == self.num_players:
                self.start_game()

    def start_game(self) -> None:
        """Instantiate a Game. Make a comp_player if needed. Go to correct game screen."""
        self.active_game = Game(self.player_names)

        if self.game_mode == 'comp':
            self.active_game.player_list[-1].comp_player = True

        if self.game_mode == 'game' or self.game_mode == 'comp':
            self.parent.current = 'game'
        elif self.game_mode == 'solo':
            self.parent.current = 'solo'

    def on_enter(self) -> None:
        """Set up screen with widgets for entering player names."""
        self.get_num_players()
        if self.game_mode == 'comp':
            self.num_players += 1

        # Place a label and input_name text-box for each player.
        for i in range(1, self.num_players + 1):
            if self.game_mode == 'comp' and i == self.num_players:
                text = 'Enter Computer Player Name:'
                # Position above the keyboard and move upward slightly with more players. Place subsequent rows below.
                position = {'x': .1, 'y': .715 + (self.num_players / 30) - (i * .135)}
            else:
                text = f'Enter Player {i}\'s name:'
                position = {'x': .15, 'y': .715 + (self.num_players / 30) - (i * .135)}

            label = Label(text=text,
                          font_size=60,
                          color=rgba(colors['text']),
                          pos_hint=position,
                          size_hint=(.25, .1),
                          id=str(i))
            self.add_widget(label)

            input_name = (FocusInput(pos_hint={'x': .475, 'y': .715 + (self.num_players / 30) - (i * .135)}))
            self.add_widget(input_name)

    def reset_goal_screen(self) -> None:
        """Reset goal_screen variables and labels."""
        goal_screen = [screen for screen in self.parent.screens if screen.name == 'goal'][0]
        goal_screen.turn_limit = 0
        goal_screen.point_goal = 0
        goal_screen.goals.diff.text = 'Difficulty:'
        goal_screen.goals.points.text = 'Points goal:'
        goal_screen.goals.turns.text = 'Turn limit:'

    def reset_num_screen(self) -> None:
        """Reset number_screen variables, labels, and buttons."""
        number_screen = [screen for screen in self.parent.screens if screen.name == 'number'][0]
        number_screen.num_label.text = 'Players Selected: '
        number_screen.cont.disabled = True
        number_screen.num_players = 0

    def to_prev_screen(self) -> None:
        """Find previous screen, reset it, and go to it."""
        if self.game_mode == 'comp' and self.num_players == 2:
            self.reset_num_screen()
            self.parent.current = 'menu'
        elif self.game_mode == 'game' or (self.game_mode == 'comp' and self.num_players > 2):
            self.reset_num_screen()
            self.parent.current = 'number'
        elif self.game_mode == 'solo':
            self.reset_goal_screen()
            self.parent.current = 'goal'
        self.clear_widgets(self.children[:-2])


class MenuScreen(Screen):

    """The main menu screen."""

    def __init__(self, **kwargs) -> None:
        super(MenuScreen, self).__init__(**kwargs)


class FriendsButton(Button):

    """Button for choosing multiplayer game mode.

    Inherits from Button.
    Overrides Button.on_release.
    """

    def __init__(self, **kwargs) -> None:
        super(FriendsButton, self).__init__(**kwargs)

    def on_release(self) -> None:
        """Set name_screen.game_mode and schedule move to PlayerNumberScreen."""
        name_screen = [screen for screen in self.parent.parent.screens if screen.name == 'name'][0]
        name_screen.game_mode = 'game'
        Clock.schedule_once(self.to_num_screen, .2)

    def to_num_screen(self, *args: list) -> None:
        """Set current screen to PlayerNumberScreen."""
        self.parent.parent.current = 'number'


class MyOwnSelfButton(Button):

    """Button to select single player v computer game mode.

    Inherits from Button.
    Overrides Button.on_release.
    """

    def __init__(self, **kwargs) -> None:
        super(MyOwnSelfButton, self).__init__(**kwargs)

    def on_release(self) -> None:
        """Set number of players and schedule move to PlayerNameScreen."""
        num_screen = [screen for screen in self.parent.parent.screens if screen.name == 'number'][0]
        num_screen.num_players = 1
        names = [screen for screen in self.parent.parent.screens if screen.name == 'name'][0]
        names.game_mode = 'comp'
        Clock.schedule_once(self.to_name_screen, .2)

    def to_name_screen(self, *args: list) -> None:
        """Set current screen to PlayerNameScreen."""
        self.parent.parent.current = 'name'


class SoloGameButton(Button):

    """Set game mode to challenge mode.

    Inherits from Button.
    Overrides Button.on_release.
    """

    def __init__(self, **kwargs) -> None:
        super(SoloGameButton, self).__init__(**kwargs)

    def on_release(self) -> None:
        """Set number of players, game mode and schedule move to PlayerGoalScreen."""
        screens = self.parent.parent.screens
        number_screen = [screen for screen in screens if screen.name == 'number'][0]
        number_screen.num_players = 1
        name_screen = [screen for screen in screens if screen.name == 'name'][0]
        name_screen.game_mode = 'solo'
        Clock.schedule_once(self.to_goal_screen, .2)

    def to_goal_screen(self, *args: list) -> None:
        """Set current screen to PlayerGoalScreen.

        :param args: Unused.
        """
        self.parent.parent.current = 'goal'


class PlayerScore(BoxLayout):

    """Empty box to hold PlayerScore(s)."""

    def __init__(self, **kwargs) -> None:
        super(PlayerScore, self).__init__(**kwargs)


class ScoreArea(BoxLayout):

    """Empty box to hold player score labels."""

    def __init__(self, **kwargs) -> None:
        super(ScoreArea, self).__init__(**kwargs)


class GameScreen(Screen):

    """Screen game is played on.

    Inherits from Screen.
    Overrides Screen.on_enter.
    """

    base = ObjectProperty()

    def __init__(self, **kwargs) -> None:
        super(GameScreen, self).__init__(**kwargs)

    def on_enter(self, *args: list) -> None:
        """Set up screen for start of game.

        Call get_active_game and get_active_game_players. Instantiate PlayerScore widgets.
        Start game by calling next_round.

        :param args: Unused.
        """
        self.base.get_active_game()
        self.base.get_active_game_players()

        for player in self.base.list_o_players:
            player_score = PlayerScore(id=player.name,
                                       pos=(self.base.score_area.x, self.base.top + 10))
            player_score.name.text = player.name.title()
            player.score_display = player_score

        self.base.score_area.add_widget(self.base.list_o_players[0].score_display)
        self.next_round()

    def next_round(self, *args: list) -> None:
        """Get a player if there is none else call reset_round and animate_score_out.

        :param args: Unused.
        :return: None.
        """
        if not self.base.current_player or self.base.current_player.name == '':
            temp = self.base.list_o_players.popleft()
            self.base.current_player = temp
            self.base.list_o_players.append(temp)

            self.animate_indicator()
            return None

        self.reset_round()
        self.animate_score_out()

    def get_next_player(self) -> None:
        """Pop next player from list_o_players.

        If we have a winner, put players in list_o_winners instead of back into list_o_players.
        Keep comp_player turns moving, schedule roll.on_press.
        """
        if not any([player.total_score >= 10000 for player in self.base.list_o_players]):
            temp = self.base.list_o_players.popleft()
            self.base.current_player = temp
            self.base.list_o_players.append(temp)

        else:
            self.base.list_o_winners.append(self.base.current_player)
            self.base.current_player = self.base.list_o_players.popleft()

        if not self.base.list_o_players:
            self.find_winner()

        elif self.base.current_player.comp_player:
                Clock.schedule_once(self.base.buttons.roll.on_press, 1.)

    def find_winner(self) -> None:
        """Sort list_o_winners, pick the appropriate message, go to ResultsScreen."""
        winners = sorted(self.base.list_o_winners, key=lambda player: player.total_score, reverse=True)
        tie = [winners[0]] + [winner for winner in winners[1:] if winner.total_score == winners[0].total_score]

        if len(tie) > 1:
            names = [win.name.title() for win in tie]
            ties = ' and '.join(names)
            message = f'It\'s a Tie!\n{ties}\n' \
                f'Win with {winners[0].total_score:,} points!'
        else:
            message = f'{winners[0].name.title()} Wins!\n\nWith {winners[0].total_score:,} points!'

        results_screen = [screen for screen in self.parent.screens if screen.name == 'results'][0]
        results_screen.message = message

        self.results_screen()

    def continue_overlord_turn(self) -> None:
        """See if there are any keepers and keep them, else end the turn."""
        scoring_dice = [die for die in self.base.active_game.choose_dice(
            [die for die in self.base.dice.children if die not in self.base.die_basket.old_keepers])]

        if not scoring_dice:
            Clock.schedule_once(self.base.buttons.end_turn.on_press, .5)
            return

        else:
            # delay continuing the turn until all dice animations are complete.
            Clock.schedule_once(self.overlord_status_check, float(len(scoring_dice)))
            for i, die in enumerate(scoring_dice):
                # delay first animation by .75sec..
                Clock.schedule_once(die.add_to_keepers, float(i * .85 + .75))

    def overlord_status_check(self, *args: list) -> None:
        """Determine if comp_player should roll again.

        :param args: Unused.
        :return: None
        """
        winners = sorted(self.base.list_o_winners, key=lambda player: player.total_score, reverse=True)

        # if comp_player has six keepers, roll again.
        if len(self.base.die_basket.old_keepers) + len(self.base.die_basket.keepers) >= 6:
            Clock.schedule_once(self.base.buttons.roll.on_press, 1.)
            return

        # there's already a winner, keep rolling.
        elif winners and winners[0].total_score >= (self.base.current_player.total_score +
                                                    self.base.current_player.round_score +
                                                    self.base.die_basket.basket_score):
            Clock.schedule_once(self.base.buttons.roll.on_press, 1.)
            return

        # comp_player has the winning score, stop!
        elif winners and (self.base.current_player.total_score +
                          self.base.current_player.round_score +
                          self.base.die_basket.basket_score) > winners[0].total_score:
            Clock.schedule_once(self.base.buttons.end_turn.on_press, 1.)
            return

        # comp_player is the first to reach the goal, stop!
        elif not winners and (self.base.current_player.total_score +
                              self.base.current_player.round_score +
                              self.base.die_basket.basket_score) >= 10000:
            Clock.schedule_once(self.base.buttons.end_turn.on_press, 1.)
            return

        # comp_player has 500 or more points and three or fewer dice to roll. Pretty good, stop.
        elif (self.base.current_player.round_score + self.base.die_basket.basket_score >= 500 and
                len(self.base.die_basket.old_keepers) + len(self.base.die_basket.keepers) >= 3):
            Clock.schedule_once(self.base.buttons.end_turn.on_press, .1)
            return

        # whelp, I suppose we'd better roll 'em.
        else:
            Clock.schedule_once(self.base.buttons.roll.on_press, 1.)
            return

    def reset_round(self) -> None:
        """Restore all base objects to initial state."""
        self.base.update_round_score(green_line=True)
        self.base.update_total_score()
        self.base.die_basket.valid_basket = rgba(colors['valid'])
        self.base.buttons.roll.update_color()
        self.base.buttons.roll.text = 'ROLL \'EM!'
        self.base.current_player.round_score = 0
        self.base.die_basket.keepers.clear()
        self.base.die_basket.old_keepers.clear()
        self.base.dice.remove_dice(self.base.dice.children)
        self.base.update_display('name')
        self.base.update_display('total')
        self.base.update_display('round')
        self.base.update_display('basket')
        self.base.buttons.end_turn.text = 'END TURN'
        self.base.buttons.end_turn.disabled = True
        self.base.buttons.end_turn.color = [1, 1, 1, .3]

    def results_screen(self) -> None:
        """Go to ResultsScreen."""
        self.parent.current = 'results'

    def animate_indicator(self) -> None:
        """Animate indicator to current_player position."""
        indicator_pos = self.base.current_player.info.children[2]
        indicator = self.base.info.children[0]
        anim = Animation(pos=indicator_pos.pos, d=.25)
        anim &= Animation(scale=.5, d=.2)
        anim.start(indicator)

    # noinspection PyArgumentList
    def animate_score_out(self) -> None:
        """Begin score_display animation - remove curr_display

        Call animate_score_in from anim.on_complete
        """
        curr_display = self.base.current_player.score_display
        anim = Animation(pos=(self.base.score_area.x + 4, self.base.top + 10), d=.25)
        anim.bind(on_complete=lambda animation, display: self.animate_score_in(display))
        anim.start(curr_display)

    def add_new_display(self) -> ScoreArea:
        """Add current_player score_display off screen.

        :return: New score_display to display.
        """
        new_display = self.base.current_player.score_display
        new_display.size_hint_x = .692
        new_display.pos = (self.base.score_area.x + 4, self.base.top + 10)
        self.base.add_widget(new_display)
        return new_display

    # noinspection PyArgumentList
    def animate_score_in(self, curr_display: ScoreArea) -> None:
        """Continue process of changing score_display.

        Remove score_display of previous player.
        Call get_next_player.
        Add score_display of current_player.
        Call animate_indicator.
        Animate score_display of current_player.
        Call animate_score_finish from anim.on_complete.

        :param curr_display: previous player's score_display
        """
        self.base.score_area.remove_widget(curr_display)
        self.get_next_player()
        new_display = self.add_new_display()
        self.animate_indicator()

        anim = Animation(pos=(self.base.score_area.x + 4, self.base.score_area.y + 4), d=.25)
        anim.bind(on_complete=lambda animation, display: self.animate_score_finish(display))
        anim.start(new_display)

    def animate_score_finish(self, new_display: ScoreArea) -> None:
        """Assign proper ownership of score_display after animation finishes.

        :param new_display: current_player's score_display.
        """
        self.base.remove_widget(new_display)
        self.base.score_area.add_widget(new_display)
        self.base.buttons.end_turn.disabled = False
        self.base.buttons.end_turn.color = rgba(colors['text'])


class ResultsScreen(Screen):

    """Screen displaying results and options to play again or quit app.

    Inherits from Screen.
    Overrides Screen.on_enter.
    """

    message = StringProperty()

    def __init__(self, **kwargs) -> None:
        super(ResultsScreen, self).__init__(**kwargs)

    def on_enter(self, *args: list) -> None:
        """Display result message label.

        :param args: Unused.
        """
        self.add_widget(Label(id='message',
                              text=self.message,
                              color=rgba(colors['text']),
                              halign='center',
                              font_size=90,
                              bold=True,
                              size_hint=(.5, .5),
                              pos_hint={'x': .25, 'y': .35}))

    def play_again(self) -> None:
        """Iterate through screens calling reset method for each screen."""
        for screen in self.parent.screens:
            if screen.name == 'number':
                self.reset_num_screen(screen)

            if screen.name == 'name':
                self.reset_name_screen(screen)

            if screen.name == 'game':
                self.reset_game_screen(screen)

            if screen.name == 'goal':
                self.reset_goal_screen(screen)

            if screen.name == 'solo':
                self.reset_solo_screen(screen)

            if screen.name == 'results':
                self.reset_results_screen(screen)

        self.parent.current = 'menu'

    def reset_num_screen(self, num_screen: Screen) -> None:
        """Reset PlayerNumberScreen labels and button.

        :param num_screen: PlayerNumberScreen instance.
        """
        num_screen.num_players = 0
        num_screen.num_label.text = 'Selected Players: '
        num_screen.cont.disabled = True

    def reset_name_screen(self, name_screen: Screen) -> None:
        """Reset PlayerNameScreen variables and widgets.

        :param name_screen: PlayerNameScreen instance.
        """
        name_screen.player_names.clear()
        name_screen.active_game = ObjectProperty()
        name_screen.clear_widgets(name_screen.children[:-2])
        name_screen.num_players = 0

    def reset_game_screen(self, game_screen: Screen) -> None:
        """Reset GameScreen widgets.

        :param game_screen: GameScreen instance.
        """
        game_screen.base.info.box.clear_widgets()

        if game_screen.base.info.children[0].id == 'indi':
            game_screen.base.info.remove_widget(game_screen.base.info.children[0])

        game_screen.base.score_area.clear_widgets()
        game_screen.base.list_o_players.clear()
        game_screen.base.list_o_winners.clear()
        game_screen.base.current_player = ObjectProperty()
        game_screen.base.active_game = ObjectProperty()

    def reset_goal_screen(self, goal_screen: Screen) -> None:
        """Reset GoalScreen variables and labels.

        :param goal_screen: GoalScreen instance.
        """
        goal_screen.turn_limit = 0
        goal_screen.point_goal = 0
        goal_screen.goals.diff.text = 'Difficulty:'

    def reset_solo_screen(self, solo_screen: Screen) -> None:
        """Reset SoloGameScreen widgets and variables.

        :param solo_screen: SoloGameScreen instance.
        """
        solo_screen.base.info.box.clear_widgets()
        solo_screen.base.score_area.clear_widgets()
        solo_screen.turn = 0
        solo_screen.point_goal = 0
        solo_screen.turn_limit = 0

    def reset_results_screen(self, results_screen: Screen) -> None:
        """Reset ResultsScreen message.

        :param results_screen: ResultsScreen instance.
        """
        message = [child for child in results_screen.children if child.id == 'message'][0]
        results_screen.remove_widget(message)

    def exit(self) -> None:
        """Close the app."""
        self.parent.parent.close()


class DieScatter(Scatter):

    """Functional container for dice images

    Inherits from Scatter.
    Overrides Scatter.on_touch_down, on_touch_move, on_touch_up.
    """

    touch = ObjectProperty()

    def __init__(self, **kwargs) -> None:
        """Add bool attribute locked.

        :param kwargs: Passed to super.
        """
        super(DieScatter, self).__init__(**kwargs)

        self.locked = False

    def on_touch_down(self, touch) -> bool:
        """Check the touch position, expand die image for visual feedback, grab the touch.

        :param touch: A touch object.
        :return: True to stop propagation of touch event.
        """
        if self.collide_point(*touch.pos):
            if self.locked:
                return True

            self.scale += .2
            touch.grab(self)
            self.touch = touch
            return True

    def on_touch_move(self, touch) -> None:
        """Check touch is from on_touch_down, convert to local coordinates, call update_pos.

        :param touch: A touch object
        """
        if touch.grab_current is self:
            self.to_widget(*touch.pos)
            self.update_pos()

    def update_pos(self) -> None:
        """Add change in touch position to pos."""
        self.pos = (self.pos[0] + self.touch.dpos[0], self.pos[1] + self.touch.dpos[1])

    def on_touch_up(self, touch) -> None:
        """Check touch continues, shrink for visual drop, check location and call appropriate function, release touch.

        :param touch: A touch object.
        """
        if touch.grab_current is self:
            die_basket = self.parent.parent.die_basket
            keepers = die_basket.keepers

            self.scale -= .2

            if self.collide_widget(die_basket) or touch.is_double_tap:
                self.add_to_keepers()

            elif not self.collide_widget(die_basket):
                self.remove_from_keepers()

            touch.ungrab(self)

    def add_to_keepers(self, *args: list) -> None:
        """Animate die to next die_holder in die_basket if newly added, reorganize if die moved within die_basket.

        :param args: Unused.
        """
        die_basket = self.parent.parent.die_basket
        keepers = die_basket.keepers
        old_keepers = die_basket.old_keepers
        die_holders = die_basket.keeper_box.children

        if self not in keepers:
            keepers.append(self)
            # trigger popup if a human is playing and has six scoring dice in the die_basket.
            if (len(keepers) + len(old_keepers) == 6 and
                    die_basket.valid_basket == rgba(colors['valid']) and
                    not self.parent.parent.current_player.comp_player):
                popup = SixKeepersPopup()
                popup.open()
                Clock.schedule_once(popup.dismiss, 2.)

            # find the position of the next die_holder in keeper_box for the new die to live.
            die_holder = die_holders[(len(keepers) + len(old_keepers)) - 1]
            anim = Animation(pos=(die_holder.pos[0] + 20, die_holder.pos[1]), d=0.5, t='out_quart')
            # find the direction to rotate the least.
            if self.rotation <= 180:
                anim &= Animation(rotation=0, d=0.5)
            else:
                anim &= Animation(rotation=360, d=0.5)
            anim.start(self)

        else:
            # if the die is still in die_basket and has moved from its die_holder, put it back.
            for die_holder, keeper in zip(die_holders[len(old_keepers):], keepers):
                anim = Animation(pos=(die_holder.pos[0] + 20, die_holder.pos[1]), d=0.2)
                anim.start(keeper)

    def remove_from_keepers(self) -> None:
        """Remove die from list and reorganize the die_basket"""
        die_basket = self.parent.parent.die_basket
        keepers = die_basket.keepers
        old_keepers = die_basket.old_keepers
        die_holders = die_basket.keeper_box.children

        if self in keepers:
            keepers.remove(self)

        # any dice to the left of an empty slot slide to the right.
        for die_holder, keeper in zip(die_holders[len(old_keepers):], keepers):
            anim = Animation(pos=(die_holder.pos[0] + 20, die_holder.pos[1]), d=0.2)
            anim.start(keeper)


class Dice(Widget):

    """Platform owning and controlling all dice. Inherits from Widget."""

    num_dice = NumericProperty()

    def __init__(self, **kwargs) -> None:
        """Add string attribute id.

        :param kwargs: Passed to super.
        """
        super(Dice, self).__init__(**kwargs)

        self.id = 'dice'

    def update_dice(self, num_dice: int) -> None:
        """Determine dice to be removed.

        Call remove_dice on them, schedule call to update_dice_two after remove_dice is done.

        :param num_dice:
        """
        doomed_dice = [widget for widget in self.children if widget not in self.parent.die_basket.old_keepers]
        self.remove_dice(doomed_dice)
        self.num_dice = num_dice
        Clock.schedule_once(self.update_dice_two, .8)

    def update_dice_two(self, *args: list) -> None:
        """Generate new dice and add them to screen in randomized positions.

        :param args: Unused.
        :return: None.
        """
        sound = sounds[2]
        sound.play()
        num_dice = self.num_dice

        # Randomized dice positions.
        positions = [{'x': uniform(.05, .25), 'y': uniform(.4, .52)},  # Top row.
                     {'x': uniform(.35, .55), 'y': uniform(.4, .52)},
                     {'x': uniform(.65, .85), 'y': uniform(.4, .52)},
                     {'x': uniform(.05, .25), 'y': uniform(.15, .27)},  # Bottom row.
                     {'x': uniform(.35, .55), 'y': uniform(.15, .27)},
                     {'x': uniform(.65, .85), 'y': uniform(.15, .27)}]

        roll = [randint(1, 6) for _ in range(num_dice)]
        new_dice = []

        for x, pos in zip(roll, positions[:num_dice + 1]):
            scatter = DieScatter(id=str(x), scale=1.6)
            image = Image(source=die_images[x])
            scatter.add_widget(image)
            self.add_widget(scatter)

            if self.parent.current_player.comp_player:
                scatter.locked = True

            anim = Animation(pos=(self.parent.width * pos['x'] * .7, self.parent.height * pos['y']), d=0.5)
            anim &= Animation(rotation=randint(-360, 360), d=0.75)
            anim.start(scatter)

            new_dice.append(scatter)

        # check to see if any new_dice are scoring dice.
        if not self.parent.active_game.choose_dice(new_dice):
            popup = FarklePopup()
            popup.bind(on_dismiss=self.parent.parent.next_round)
            popup.open()
            Clock.schedule_once(popup.dismiss, 2.5)
            return

        if self.parent.current_player.comp_player:
            self.parent.parent.continue_overlord_turn()

    # noinspection PyArgumentList
    def remove_dice(self, dice: list) -> None:
        """Animate dice off screen and schedule complete.

        :param dice: List of DieScatter objects.
        """
        anim = Animation(pos=(-50, -50), d=0.5, t='in_out_quad')
        anim.bind(on_complete=lambda animation, die_scatter: self.complete_removal(die_scatter))
        if dice:
            for die in dice:
                anim.start(die)

    def complete_removal(self, die) -> None:
        """Remove dice after animation complete."""
        if die.parent:
            self.remove_widget(die)


class Indicator(Scatter):

    """Die Image for use as a turn indicator.

    Inherits from Scatter.
    Overrides on_touch_down.
    """

    def __init__(self, **kwargs) -> None:
        """Add die image, make it tiny and disallow user to rescale.

        :param kwargs: Passed to super.
        """
        super(Indicator, self).__init__(**kwargs)
        self.add_widget(Image(source=die_images[1]))
        self.scale = .01
        self.do_scale = False

    def on_touch_down(self, touch) -> bool:
        """Do nothing and stop touch propagation."""
        if self.collide_point(*touch.pos):
            return True


class InformationStation(FloatLayout):

    """Layout for in-game score information. Inherits from FloatLayout."""

    box = ObjectProperty()

    def __init__(self, **kwargs) -> None:
        super(InformationStation, self).__init__(**kwargs)

    def add_player_totals(self) -> None:
        """Add widgets for displaying player totals."""
        base = self.parent
        for player in base.list_o_players:
            lil_box = BoxLayout(id=player.name)
            turn_indicator_holder = Widget(id='turn',
                                           size_hint=(.025, 1),
                                           pos_hint={'x': 0, 'y': .45})
            lil_box.add_widget(turn_indicator_holder)

            lil_box.add_widget(Label(id='name',
                                     text=player.name.title(),
                                     halign='left',
                                     size_hint=(.6, 1),
                                     pos_hint={'x': .025, 'y': 0},
                                     shorten=True,
                                     shorten_from='right'))
            total = Label(id='total',
                          text=str(player.total_score),
                          size_hint=(.375, 1),
                          pos_hint={'x': .525, 'y': 0})
            lil_box.add_widget(total)

            self.box.add_widget(lil_box)
            player.info = lil_box

        indicator = Indicator(id='indi')
        self.add_widget(indicator)


class GameButtonRow(BoxLayout):

    """Box for holding game operation buttons. Inherits from Box Layout."""

    roll = ObjectProperty()
    end_turn = ObjectProperty()
    keep = ObjectProperty()

    def __init__(self, **kwargs) -> None:
        super(GameButtonRow, self).__init__(**kwargs)


class RulesButton(Button):

    """Launch RulesPopup. Inherits from Button."""

    def __init__(self, **kwargs) -> None:
        """Add RulesPopup as attribute popup.

        :param kwargs: Pass to super.
        """
        super(RulesButton, self).__init__(**kwargs)

        self.popup = RulesPopup()

    def on_press(self) -> None:
        """Open RulesPopup."""
        self.popup.open()


class KeepAll(Button):

    """Button for adding all dice to the keeper_box.

    Inherits from Button.
    Overrides on_press.
    """

    def __init__(self, **kwargs) -> None:
        super(KeepAll, self).__init__(**kwargs)

    def on_press(self) -> None:
        """Add all dice not in keeper_box to keepers."""
        # do nothing if it's comp_player's turn.
        if self.parent.parent.current_player.comp_player:
            return
        dice = self.parent.parent.dice.children
        for die in dice:
            if (die not in self.parent.parent.die_basket.old_keepers and
                    die not in self.parent.parent.die_basket.keepers):
                die.add_to_keepers()


class MyPopup(Popup):

    """Template for popups, inherits from Popup."""

    def __init__(self, **kwargs) -> None:
        """Set attributes for popups to inherit.

        :param kwargs: Passed to super.
        """
        super(MyPopup, self).__init__(**kwargs)

        self.title_size = 75
        self.title_align = 'center'
        self.separator_color = rgba(colors['second'])
        self.size_hint = (.6, .5)


class RulesPopup(MyPopup):

    """Popup displaying rules of the game. Inherits from MyPopup."""

    def __init__(self, **kwargs) -> None:
        """Set title and content to display. Override MyPopup.size_hint.

        :param kwargs: Passed to super.
        """
        super(RulesPopup, self).__init__(**kwargs)

        self.title = 'How To Play'

        label = Label(text=msg1,
                      font_size=40,
                      halign='center',
                      pos_hint={'x': 0, 'y': .45})
        label2 = Label(text=msg2,
                       font_size=35,
                       halign='left',
                       size_hint=(1, .6),
                       pos_hint={'x': 0, 'y': .1})
        container = FloatLayout()
        container.add_widget(label2)
        container.add_widget(label)

        self.content = container
        self.size_hint = (.9, .9)


class YouSurePopup(MyPopup):

    """Ensure user knows points are left on the board. Inherits from MyPopup."""

    def __init__(self, **kwargs) -> None:
        """Set title and content. Add button to discard points and continue game.

        :param kwargs: Passed to super.
        """
        super(YouSurePopup, self).__init__(**kwargs)

        self.title = 'Are You Sure?!'

        label = Label(text='You still have points on the board!',
                      halign='center',
                      pos_hint={'x': 0, 'y': .225})

        btn = Button(text='MEH, I DON\'T WANT THOSE.',
                     size_hint=(.6, .4),
                     pos_hint={'x': .2, 'y': .1},
                     background_normal='',
                     background_color=rgba(colors['prime dark']))
        btn.bind(on_release=self.leave_points)

        base = FloatLayout()
        base.add_widget(label)
        base.add_widget(btn)

        self.content = base

    def leave_points(self, *args: list) -> None:
        """Call next game for active screen and close popup.

        :param args: Unused.
        """
        game_screen = [screen for screen in self.parent.children[1].screens if screen.name == 'game'][0]
        solo_screen = [screen for screen in self.parent.children[1].screens if screen.name == 'solo'][0]

        if len(game_screen.base.list_o_players) > 1:
            game_screen.next_round()
        else:
            solo_screen.next_round()

        self.dismiss()


class Exit(Button):

    """Call ReallyExit popup to confirm user intention.

    Inherit from Button.
    Override on_release.
    """

    def __init__(self, **kwargs) -> None:
        super(Exit, self).__init__(**kwargs)

    def on_release(self) -> None:
        """Open confirmation popup."""
        popup = ReallyExit()
        popup.open()


class ReallyExit(MyPopup):

    """Confirm user intention to leave app. Inherits from MyPopup."""

    def __init__(self, **kwargs) -> None:
        """Set title and content. Add buttons for staying and leaving app.

        :param kwargs: Passed to super.
        """
        super(ReallyExit, self).__init__(**kwargs)

        self.title = 'So soon?'

        label = Label(text='Are you sure you want to exit the app?',
                      halign='center',
                      pos_hint={'x': 0, 'y': .3})

        yes_go = Button(text='Exit',
                        size_hint=(.4, .4),
                        pos_hint={'x': .55, 'y': .1},
                        background_normal='',
                        background_color=rgba(colors['prime dark']))
        yes_go.bind(on_release=self.quit)

        no_stay = Button(text='Stay',
                         size_hint=(.4, .4),
                         pos_hint={'x': .05, 'y': .1},
                         background_normal='',
                         background_color=rgba(colors['prime dark']))
        no_stay.bind(on_release=self.stay)

        base = FloatLayout()
        base.add_widget(label)
        base.add_widget(yes_go)
        base.add_widget(no_stay)
        self.content = base

    def stay(self, *args: list) -> None:
        """Dismiss popup and remain in-app.

        :param args: Unused.
        """
        self.dismiss()

    def quit(self, *args: list) -> None:
        """Close the app.

        :param args: Unused.
        """
        self.parent.close()


class SixKeepersPopup(MyPopup):

    """Congratulate user on a good round. Inherits from MyPopup."""

    def __init__(self, **kwargs) -> None:
        """Set title and content.

        :param kwargs: Passed to super.
        """
        super(SixKeepersPopup, self).__init__(**kwargs)

        self.title = 'Congratulations!'

        label = Label(text='You got six keepers! Roll \'em all again!',
                      halign='center')

        self.content = label
        self.size_hint = (.45, .3)


class ThresholdNotMet(MyPopup):

    """Inform user the point threshold for a first turn has not been met. Inherits from MyPopup."""

    def __init__(self, **kwargs) -> None:
        """Set title. and content.

        :param kwargs: Passed to super.
        """
        super(ThresholdNotMet, self).__init__(**kwargs)

        self.title = 'Hold Up!'

        label = Label(text='You haven\'t earned 500 points in one turn yet.\n\n Keep rolling!',
                      halign='center')

        self.content = label


class FarklePopup(MyPopup):

    """Inform user that no keepers were thrown and their turn is over. Inherits from MyPopup."""

    def __init__(self, **kwargs) -> None:
        """Set title and content.

        :param kwargs: Passed to super.
        """
        super(FarklePopup, self).__init__(**kwargs)

        self.title = 'Oh No!'

        label = Label(text='You didn\'t get any keepers! Your turn is over.\n\n:(',
                      halign='center')

        self.content = label
        self.size_hint = (.5, .4)


class NonKeeperKept(MyPopup):

    """Warn user that a non-scoring die is in the scoring area. Offer button to open RulesPopup.

    Inherits from MyPopup.
    """

    def __init__(self, **kwargs) -> None:
        """Set title and content. Add button to open RulesButton.

        :param kwargs: Passed to super.
        """
        super(NonKeeperKept, self).__init__(**kwargs)

        self.title = 'WARNING!!'

        label = Label(text='You have non-scoring dice in the scoring area.'
                           '\n\nRemove non-scoring dice to turn line green and continue',
                      halign='center',
                      pos_hint={'x': 0, 'y': .25})
        btn = RulesButton(size_hint=(.5, .3),
                          pos_hint={'x': .25, 'y': .1})

        layout = FloatLayout()
        layout.add_widget(label)
        layout.add_widget(btn)

        self.content = layout
        self.size_hint = (.7, .6)


class EndTurn(Button):

    """Button to end player turn and move to next player.

    Inherits from Button.
    Overrides on_press.
    """

    def __init__(self, **kwargs) -> None:
        super(EndTurn, self).__init__(**kwargs)

    def on_press(self, *args: list) -> None:
        # do nothing if it's comp_player's turn.
        if self.parent.parent.current_player.comp_player and not args:
            return
        base = self.parent.parent
        # check that player has met first turn threshold.
        if (base.die_basket.valid_basket == rgba(colors['valid'])
                and base.current_player.total_score == 0
                and (base.current_player.round_score + base.die_basket.basket_score) < 500):
            popup = ThresholdNotMet()
            popup.open()
        # check if points are still on the board.
        elif (base.die_basket.valid_basket == rgba(colors['valid']) and
                ([die for die in base.active_game.choose_dice([die for die in base.dice.children
                                                               if die not in base.die_basket.old_keepers])
                    if die not in base.die_basket.keepers])):
            popup = YouSurePopup()
            popup.open()
        # check for non-scoring dice in the keeper_box.
        elif (base.die_basket.valid_basket == rgba(colors['error']) and
              base.die_basket.keepers and
              base.active_game.validate_choice([int(die.id) for die in base.die_basket.keepers])):
            popup = NonKeeperKept()
            popup.open()
        # everything looks good.
        else:
            base.parent.next_round()


class Roll(Button):

    """Button to roll dice.

    Inherits from Button.
    Overrides on_press.
    """

    def __init__(self, **kwargs) -> None:
        super(Roll, self).__init__(**kwargs)

    def on_press(self, *args: list) -> None:
        """Clear non-keepers, gray out keepers, add them to old_keepers.

        Call update_color, update_round_score, and update_dice.

        :param args: Will have non-zero len if called by comp_player.
        :return: None.
        """
        # do nothing if comp_player turn.
        if self.parent.parent.current_player.comp_player and not args:
            return

        die_basket = self.parent.parent.die_basket
        keepers = die_basket.keepers
        old_keepers = die_basket.old_keepers

        if die_basket.valid_basket == rgba(colors['valid']):
            for keeper in keepers:
                old_keepers.append(keeper)
            if len(old_keepers) >= 6:
                old_keepers.clear()
            self.parent.parent.dice.update_dice(6 - len(old_keepers))

        self.parent.parent.update_round_score()

        for keeper in old_keepers:
            keeper.locked = True

        for keeper in die_basket.keepers:
            gray = InstructionGroup()
            gray.add(Color(.9, .9, .9, .5))
            gray.add(Rectangle(pos=(5, 7), size=(keeper.size[0] - 15, keeper.size[1] - 15)))
            keeper.canvas.add(gray)

        die_basket.keepers.clear()
        self.update_color()

    def update_color(self) -> None:
        """Disable button if die_basket == error else enable it. Change texts if score over threshold."""
        die_basket = self.parent.parent.die_basket.valid_basket
        if die_basket == rgba(colors['error']):
            self.background_color = rgba(colors['prime off'])
            self.disabled = True
            self.color = [1, 1, 1, .3]
            self.parent.end_turn.text = 'END TURN'

        elif die_basket == rgba(colors['valid']):
            self.background_color = rgba(colors['prime dark'])
            self.disabled = False
            self.color = rgba(colors['text'])
            current_player = self.parent.parent.current_player
            if (current_player.total_score + current_player.round_score +
                    self.parent.parent.die_basket.basket_score) >= 500:
                self.parent.end_turn.text = 'KEEP POINTS'
                self.text = 'RISK \'N ROLL!'


class ReallyQuit(MyPopup):

    """Confirm user intention to quit the game. Inherits from MyPopup."""

    def __init__(self, **kwargs) -> None:
        """Set title and content. Add buttons for staying in-game and quitting game.

        :param kwargs: Passed to super.
        """
        super(ReallyQuit, self).__init__(**kwargs)

        self.title = 'You\'ve got a good thing going here.'

        label = Label(text='Are you sure you want quit your game?',
                      halign='center',
                      pos_hint={'x': 0, 'y': .3})
        yes_go = Button(text='Quit',
                        font_size=75,
                        size_hint=(.4, .4),
                        pos_hint={'x': .55, 'y': .1},
                        background_normal='',
                        background_color=rgba(colors['prime dark']))
        yes_go.bind(on_release=self.quit)

        no_stay = Button(text='Stay',
                         font_size=75,
                         size_hint=(.4, .4),
                         pos_hint={'x': .05, 'y': .1},
                         background_normal='',
                         background_color=rgba(colors['prime dark']))
        no_stay.bind(on_release=self.stay)

        base = FloatLayout()
        base.add_widget(label)
        base.add_widget(yes_go)
        base.add_widget(no_stay)
        self.content = base

    def stay(self, *args: list) -> None:
        """Close the popup.

        :param args: Unused.
        """
        self.dismiss()

    def quit(self, *args: list) -> None:
        """Close popup, reset screens and return to MenuScreen.

        :param args: Unused.
        """
        self.dismiss()
        results = [screen for screen in self.parent.children[1].screens if screen.name == 'results'][0]
        screen_manager = self.parent.children[1]
        for screen in screen_manager.screens:
            if screen.name == 'results':
                results = screen

        for screen in screen_manager.screens:
            if screen.name == 'number':
                results.reset_num_screen(screen)

            if screen.name == 'name':
                results.reset_name_screen(screen)

            if screen.name == 'game':
                results.reset_game_screen(screen)

            if screen.name == 'goal':
                results.reset_goal_screen(screen)

            if screen.name == 'solo':
                results.reset_goal_screen(screen)

        screen_manager.current = 'menu'


class Quit(Button):

    """Button to quit game."""

    def __init__(self, **kwargs) -> None:
        super(Quit, self).__init__(**kwargs)

    def on_release(self) -> None:
        """Confirm user intention to quit with popup."""
        popup = ReallyQuit()
        popup.open()


class Base(FloatLayout):

    """A container for all gameplay and display objects. Inherits from FloatLayout."""

    list_o_players = deque()
    list_o_winners = ListProperty()
    active_game = ObjectProperty()
    buttons = ObjectProperty()
    current_player = ObjectProperty()
    die_basket = ObjectProperty()
    dice = ObjectProperty()
    info = ObjectProperty()
    score_area = ObjectProperty()

    def __init__(self, **kwargs) -> None:
        super(Base, self).__init__(**kwargs)

    def get_active_game(self) -> None:
        """Retrieve active game from PlayerNameScreen.

        :return: active_game ObjectProperty.
        """
        name_screen = [screen for screen in self.parent.parent.screens if screen.name == 'name'][0]
        self.active_game = name_screen.active_game
        return self.active_game

    def get_active_game_players(self) -> deque:
        """Create list_o_players from active_game.player_list.

        :return: A deque, list_o_players.
        """
        for player in self.active_game.player_list:
            self.list_o_players.append(player)
        self.info.add_player_totals()
        return self.list_o_players

    def update_round_score(self, green_line=None) -> None:
        """Add basket_score to round score and call update_display to reflect update.

        :param green_line: True when changing players to start with green line and active Roll button.
        """
        die_basket = self.die_basket
        if die_basket.valid_basket == rgba(colors['valid']):
            self.current_player.round_score += die_basket.basket_score
            self.update_display('round')

            if not green_line:
                die_basket.valid_basket = rgba(colors['error'])
                self.buttons.roll.background_color = rgba(colors['prime off'])

        die_basket.basket_score = 0

    def update_total_score(self) -> None:
        """Add round_score to total_score."""
        if self.die_basket.valid_basket == rgba(colors['valid']):
            # player has not hit the first turn threshold yet.
            if self.current_player.total_score == 0 and self.current_player.round_score < 500:
                self.current_player.round_score = 0

            if self.current_player.total_score > 0 or self.current_player.round_score >= 500:
                self.current_player.total_score += self.current_player.round_score
                self.current_player.round_score = 0

        else:
            self.current_player.round_score = 0

    def update_display(self, score_type: str) -> None:
        """Helper function calls functions based on score_type.

        :param score_type: May be: 'round', 'basket', 'total, 'progress', or 'solo total'.
        """
        if score_type == 'round' or score_type == 'basket':
            self.update_round_display(score_type)
        if score_type == 'total':
            self.update_total_display()
        if score_type == 'progress':
            self.update_progress_display()
        if score_type == 'solo total':
            self.update_solo_total_display()

    def update_round_display(self, score_type: str) -> None:
        """Update player's round and total_plus displays in ScoreArea.

        :param score_type: 'basket' or 'round'
        """
        if score_type == 'basket':
            self.current_player.score_display.round.text = 'Round: {:,}'.format(self.current_player.round_score +
                                                                                self.die_basket.basket_score)
            self.current_player.score_display.total_plus.text = 'Round + Total: {:,}'.format(
                self.current_player.total_score +
                self.current_player.round_score +
                self.die_basket.basket_score)
        if score_type == 'round':
            self.current_player.score_display.round.text = f'Round: {self.current_player.round_score:,}'

    def update_total_display(self) -> None:
        """Update player's total display in ScoreArea and InformationStation."""
        self.current_player.info.children[0].text = f'{self.current_player.total_score:,}'
        self.current_player.score_display.total.text = f'Total: {self.current_player.total_score:,}'

    def update_progress_display(self) -> None:
        """Update player's progress display in ScoreArea"""
        self.current_player.score_display.progress.text = f'{self.parent.turn} / {self.parent.turn_limit}'

    def update_solo_total_display(self) -> None:
        """Update player's progress toward point_goal in InformationStation and total_plus in ScoreArea."""
        self.current_player.score_display.total_plus.text = 'Round + Total: {:,}'.format(
                self.current_player.total_score +
                self.current_player.round_score +
                self.die_basket.basket_score)
        self.current_player.info.children[0].text = \
            f'{self.current_player.total_score:,} / \n{self.parent.point_goal:,}'


class DieHolder(Widget):

    """Container for dice added to die_basket."""

    def __init__(self, **kwargs) -> None:
        super(DieHolder, self).__init__(**kwargs)


class KeeperBox(BoxLayout):

    """Container for DieHolders."""

    def __init__(self, **kwargs) -> None:
        super(KeeperBox, self).__init__(**kwargs)


class DieBasket(FloatLayout):

    """Container for scoring dice.

    Dice colliding with die_basket are added to keepers.
    on_keepers checks validity of die added and updates scoring line color and round score as dice are added.
    Inherits from FloatLayout.
    """

    keepers = ListProperty()
    old_keepers = ListProperty()
    valid_basket = ListProperty()
    basket_score = NumericProperty()
    active_game = ObjectProperty()
    keeper_box = ObjectProperty()

    def __init__(self, **kwargs) -> None:
        super(DieBasket, self).__init__(**kwargs)

        self.valid_basket = rgba(colors['valid'])

    def on_keepers(self, *args: list) -> None:
        """Check if newly added die is a keeper or completes a group of three.

        Update keeper line and Roll button accordingly.

        :param args: Unused.
        """
        choice = [int(child.id) for child in self.keepers]

        score = self.active_game.keep_score(choice)
        self.basket_score = score
        self.parent.update_display('basket')

        # validate_choice returns a list of non-scoring dice.
        scored = self.active_game.validate_choice(choice)
        scored = not bool(scored)

        roll_button = self.parent.buttons.roll
        if not scored or not choice:
            self.valid_basket = rgba(colors['error'])
            roll_button.update_color()

        if scored and choice:
            self.valid_basket = rgba(colors['valid'])
            roll_button.update_color()


class SoloPLayerScore(BoxLayout):

    """Container for single player score information."""

    def __init__(self, **kwargs) -> None:
        super(SoloPLayerScore, self).__init__(**kwargs)


class PointGoal(DropDown):

    """Menu for selecting game's ending score. Inherits from DropDown."""

    def __init__(self, **kwargs) -> None:
        super(PointGoal, self).__init__(**kwargs)

    def select(self, data: int) -> None:
        """Set point_goal with data selected by user. If turn_limit is also set, enable cont button.

        :param data: point_goal selected by user.
        """
        goal_screen = self.parent.children[1].children[0]
        goal_screen.point_goal = data
        if goal_screen.turn_limit:
            goal_screen.cont.disabled = False


class TurnLimit(DropDown):

    """Menu for setting maximum turns allowed in game. Inherits from DropDown."""

    def __init__(self, **kwargs) -> None:
        super(TurnLimit, self).__init__(**kwargs)

    def select(self, data: int) -> None:
        """Set turn_limit with data selected by user. If point_goal is also set, enable cont button.

        :param data: turn_limit selected by user.
        """
        goal_screen = self.parent.children[1].children[0]
        goal_screen.turn_limit = data
        if goal_screen.point_goal:
            goal_screen.cont.disabled = False


class SoloGoalScreen(Screen):

    """Screen for choosing point_goal and turn_limit for challenge mode.

    Inherits from Screen.
    Overrides on_enter.
    """

    point_goal = NumericProperty()
    turn_limit = NumericProperty()

    def __init__(self, **kwargs) -> None:
        super(SoloGoalScreen, self).__init__(**kwargs)

    def on_enter(self) -> None:
        """Set up screen with labels, buttons and drop-down menus."""
        # continue button disabled until both point_goal and turn_limit set.
        self.cont.disabled = True
        intro_label = Label(text='Set up your own game for a customized challenge!',
                            halign='center',
                            font_size=100,
                            pos_hint={'x': .2, 'y': .825},
                            size_hint=(.6, .1))
        self.add_widget(intro_label)
        # construct drop-down menus.
        # make the button containing the drop-down.
        point_button = Button(text='SET POINTS GOAL',
                              pos_hint={'x': .1, 'y': .7},
                              size_hint=(.3, .1),
                              font_size=75,
                              background_normal='',
                              background_color=rgba(colors['prime dark']))
        self.add_widget(point_button)
        # instantiate the drop-down.
        point_drop = PointGoal()
        # make btns to select a point value.
        for x in [2500, 5000, 7500, 10000, 15000]:
            btn = Button(text=f'{x:,}',
                         id=str(x),
                         size_hint_y=None,
                         height=110,
                         background_normal='',
                         background_color=rgba(colors['second']))
            # bind the btn press to the drop-down's select method and pass the btn id.
            btn.bind(on_release=lambda button: point_drop.select(int(button.id)))
            point_drop.add_widget(btn)
        # open the menu with the first button.
        point_button.bind(on_release=point_drop.open)

        turn_button = Button(pos_hint={'x': .6, 'y': .7},
                             size_hint=(.3, .1),
                             text='SET TURN LIMIT',
                             font_size=75,
                             background_normal='',
                             background_color=rgba(colors['prime dark']))
        self.add_widget(turn_button)

        turn_drop = TurnLimit()
        for x in [5, 10, 15, 20, 30]:
            btn = Button(text=str(x),
                         size_hint_y=None,
                         height=110,
                         background_normal='',
                         background_color=rgba(colors['second']))
            btn.bind(on_release=lambda button: turn_drop.select(int(button.text)))
            turn_drop.add_widget(btn)
        turn_button.bind(on_release=turn_drop.open)

    def on_point_goal(self, *args: list) -> None:
        """Update point_goal label with point_goal data.

        :param args: Unused.
        """
        self.goals.points.text = f'Points goal: {self.point_goal:,}'
        if self.turn_limit and self.point_goal:
            self.set_difficulty()

    def on_turn_limit(self, *args: list) -> None:
        """Update turn_limit label with turn_limit data.

        :param args: Unused.
        """
        self.goals.turns.text = f'Turn limit: {self.turn_limit}'
        if self.point_goal and self.turn_limit:
            self.set_difficulty()

    def set_difficulty(self) -> None:
        """Update difficulty label by points per turn."""
        diff = 'Difficulty: '
        points_per_turn = self.point_goal // self.turn_limit
        if 0 < points_per_turn <= 125:
            diff = 'Difficulty: Really Easy'
        elif 125 < points_per_turn <= 175:
            diff = 'Difficulty: Easy'
        elif 175 < points_per_turn <= 250:
            diff = 'Difficulty: Medium'
        elif 250 < points_per_turn <= 500:
            diff = 'Difficulty: Hard'
        elif 500 < points_per_turn <= 750:
            diff = 'Difficulty: Really Hard'
        elif points_per_turn > 750:
            diff = 'Difficulty: Possible'
        self.goals.diff.text = diff

    def to_menu_screen(self) -> None:
        """Reset PlayerNumberScreen stuff and go to menu screen."""
        number_screen = [screen for screen in self.parent.screens if screen.name == 'number'][0]
        number_screen.num_players = 0
        number_screen.num_label.text = 'Players Selected: '
        self.goals.diff.text = 'Difficulty:'
        self.goals.points.text = 'Points goal:'
        self.goals.turns.text = 'Turn limit:'
        self.parent.current = 'menu'


class SoloGameScreen(Screen):

    """Screen for playing challenge mode.

    Inherits from Screen.
    Overrides on_enter.
    """

    base = ObjectProperty()
    comp_player = StringProperty()
    turn = NumericProperty(0)
    point_goal = NumericProperty()
    turn_limit = NumericProperty()

    def __init__(self, **kwargs) -> None:
        super(SoloGameScreen, self).__init__(**kwargs)

    def on_enter(self, *args: list) -> None:
        """Set up screen to play challenge mode.

        Get game and player. Add players' score_display. Get the game started by calling next_round.

        :param args: Unused.
        """
        self.base.get_active_game()
        self.base.get_active_game_players()

        goal_screen = [screen for screen in self.parent.screens if screen.name == 'goal'][0]
        self.point_goal = goal_screen.point_goal
        self.turn_limit = goal_screen.turn_limit

        player = self.base.list_o_players[0]
        self.base.current_player = player
        player_score = SoloPLayerScore(id=player.name)

        name_area = player_score.name
        name_area.text = player.name.title()
        name_area.bold = True

        player_score.round.text = 'Round: 0'
        player_score.total_plus.text = 'Round + Total: 0'
        player_score.progress.text = f'Turns: {self.turn} / {self.turn_limit}'

        player.score_display = player_score

        self.base.score_area.add_widget(player.score_display)
        self.next_round()

    def next_round(self, *args: list) -> None:
        """Reset all base variables and widgets to initial state, check game status, increment turn."""
        self.base.update_round_score(green_line=True)
        self.base.update_total_score()
        self.base.die_basket.valid_basket = rgba(colors['valid'])
        self.base.buttons.roll.update_color()
        self.base.buttons.roll.text = 'ROLL \'EM!'
        self.base.buttons.end_turn.text = 'END TURN'
        self.base.current_player.round_score = 0
        self.base.die_basket.keepers.clear()
        self.base.die_basket.old_keepers.clear()
        self.base.dice.remove_dice(self.base.dice.children)
        self.base.update_display('round')
        self.base.update_display('progress')
        self.base.update_display('solo total')

        if self.base.current_player.total_score >= self.point_goal or self.turn > self.turn_limit:
            if self.base.current_player.total_score >= self.point_goal:
                message = f'{self.base.current_player.name.title()} wins!\n\n' \
                    f'With {self.base.current_player.total_score:,} points!\n\nIn {self.turn - 1} turns!'
            else:
                message = f'Oh no, {self.base.current_player.name.title()}!\n\n' \
                    f'You\'re out of turns\n\nand only got {self.base.current_player.total_score:,} points.'
            for screen in self.parent.screens:
                if screen.name == 'results':
                    screen.message = message
            self.results_screen()
        self.turn += 1

    def results_screen(self) -> None:
        """Set current screen to ResultsScreen."""
        self.parent.current = 'results'


class Screens(ScreenManager):

    """Manages available screens. Inherits from ScreenManager"""

    def __init__(self, **kwargs) -> None:
        """Add and name all screens.

        :param kwargs: Passed to super.
        """
        super(Screens, self).__init__(**kwargs)

        self.add_widget(MenuScreen(name='menu'))
        self.add_widget(PlayerNumberScreen(name='number'))
        self.add_widget(SoloGoalScreen(name='goal'))
        self.add_widget(SoloGameScreen(name='solo'))
        self.add_widget(PlayerNameScreen(name='name'))
        self.add_widget(GameScreen(name='game'))
        self.add_widget(ResultsScreen(name='results'))

        self.current = 'menu'


class GameApp(App):

    """Base class with main loop internals."""

    def build(self):
        """Set title and return widget tree root."""
        self.title = 'Ten Thousand'
        return self.root


Window.softinput_mode = 'below_target'
Window.keyboard_padding = 5

if __name__ == '__main__':
    GameApp().run()
