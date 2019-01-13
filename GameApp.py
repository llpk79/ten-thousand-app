# Copyright 2018 Paul Kutrich. All rights reserved.
import kivy
import re
import math
import time

kivy.require('1.10.1')

from kivy.graphics import *
from kivy.animation import Animation, AnimationTransition
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty, ListProperty, NumericProperty, BooleanProperty
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.uix.scatter import Scatter
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.image import Image
from kivy.utils import rgba

from collections import deque
from media import sounds, die_images
from logic import Game
from game_rules import msg
from colors import colors
from random import randint, uniform


class PlayerNumButton(Button):
    def __init__(self, **kwargs):
        super(PlayerNumButton, self).__init__(**kwargs)

    def on_press(self):
        buttons = self.parent.parent.buttons
        player_num_screen = buttons.parent.parent
        if buttons.one == self:
            player_num_screen.set_num_players(1)
        elif buttons.two == self:
            player_num_screen.set_num_players(2)
        elif buttons.three == self:
            player_num_screen.set_num_players(3)
        return True


class PlayerNumberScreen(Screen):
    num_players = ObjectProperty()
    layout = ObjectProperty()

    def __init__(self, **kwargs):
        super(PlayerNumberScreen, self).__init__(**kwargs)

    def set_num_players(self, num_players):
        if num_players:
            self.num_players = num_players
            self.parent.current = 'name'


class FocusInput(TextInput):
    def __init__(self, **kwargs):
        super(FocusInput, self).__init__(**kwargs)

        self.write_tab = False

    def on_focus(self, widget, value):
        if self.parent and not self.focus:
            self.parent.add_player(self, value)


class PlayerNameScreen(Screen):
    player_names = ListProperty()
    active_game = ObjectProperty()
    num_players = NumericProperty()

    def __init__(self, **kwargs):
        super(PlayerNameScreen, self).__init__(**kwargs)

    def get_num_players(self):
        for screen in self.parent.screens:
            if screen.name is 'number':
                self.num_players = screen.num_players

    def add_player(self, name, valid):
        if not valid and name.text != '':
            self.player_names.append(name.text)

            if len(self.player_names) == self.num_players:
                self.active_game = Game(self.player_names)
                if self.num_players > 1:
                    self.parent.current = 'game'
                else:
                    self.parent.current = 'solo'

    def on_enter(self):
        self.get_num_players()

        for i in range(1, self.num_players + 1):
            label = Label(text=f'Enter Player {i}\'s name:',
                          font_size=30,
                          color=rgba(colors['text']),
                          pos_hint={'x': .15, 'y': .85 - (i * .2)},
                          size_hint=(.25, .1),
                          id=str(i))
            self.add_widget(label)
            input_name = (FocusInput(multiline=False,
                                     font_size=30,
                                     pos_hint={'x': .475, 'y': .85 - (i * .2)},
                                     size_hint=(.35, .09)))
            if i == 1:
                input_name.focus = True
            self.add_widget(input_name)


class MenuScreen(Screen):
    def __init__(self, **kwargs):
        super(MenuScreen, self).__init__(**kwargs)


class PlayerScore(BoxLayout):
    def __init__(self, **kwargs):
        super(PlayerScore, self).__init__(**kwargs)


class ScoreArea(BoxLayout):
    def __init__(self, **kwargs):
        super(ScoreArea, self).__init__(**kwargs)


class GameScreen(Screen):
    base = ObjectProperty()

    def __init__(self, **kwargs):
        super(GameScreen, self).__init__(**kwargs)

    def set_current_player(self):
        if self.base.current_player is not None:
            self.base.update_round_score(red=True)
            self.base.update_total_score()
            self.base.die_basket.valid_basket = rgba(colors['valid'])
            self.base.buttons.roll.update_color()
            self.base.buttons.roll.text = 'Roll \'em!'
            self.base.current_player.round_score = 0
            self.base.die_basket.keepers.clear()
            self.base.buttons.roll.keeper_count.clear()
            self.base.dice.remove_dice(self.base.dice.children, turn=True)
            self.base.update_display('round')
            self.base.update_display('name', 'small')
            self.base.update_display('total')

        if not any([player.total_score >= 2000 for player in self.base.list_o_players]):
            temp = self.base.list_o_players.popleft()
            self.base.current_player = temp
            self.base.update_display('name', 'big')
            self.base.list_o_players.append(temp)

        else:
            self.base.list_o_winners.append(self.base.current_player)
            self.base.current_player = self.base.list_o_players.popleft()
            self.base.update_display('name', 'big')

            if not self.base.list_o_players:
                for screen in self.parent.screens:
                    if screen.name == 'results':
                        screen.winners = [*self.base.list_o_winners]
                self.parent.current = 'results'

    def on_enter(self, *args):
        self.base.get_active_game()
        self.base.get_active_game_players()

        for i, player in enumerate(self.base.list_o_players):
            player_score = PlayerScore(id=player.name)

            name_area = player_score.name
            round_area = player_score.round
            total_area = player_score.total
            if i == 0:
                name_area.text = f'[u]{player.name}[/u]'
                name_area.font_size = 32
                name_area.bold = True
                round_area.bold = True
                total_area.bold = True
            else:
                name_area.text = player.name
                name_area.font_size = 22
            round_area.text = f'Round: {str(0)}'
            total_area.text = f'Total: {str(0)}'

            self.base.score_area.add_widget(player_score)
        self.set_current_player()


class ResultsScreen(Screen):
    winners = ListProperty()

    def __init__(self, **kwargs):
        super(ResultsScreen, self).__init__(**kwargs)

    def get_winners(self):
        for screen in self.parent.screens:
            if screen.name == 'game':
                self.winners = screen.list_o_winners

    def on_enter(self, *args):
        winners = sorted(self.winners, key=lambda x: x.total_score, reverse=True)

        self.add_widget(Label(text=f'{winners[0].name} wins !!\n\nWith {winners[0].total_score} points!',
                              color=rgba(colors['text']),
                              halign='center',
                              font_size=40,
                              bold=True,
                              size_hint=(.5, .5),
                              pos_hint={'x': .25, 'y': .35}))

    def play_again(self):
        self.parent.current = 'menu'

    def exit(self):
        self.parent.parent.close()


class DieScatter(Scatter):
    touch = ObjectProperty()

    def __init__(self, **kwargs):
        super(DieScatter, self).__init__(**kwargs)

        self.locked = False

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self.locked:
                return True
            self.scale += .1
            touch.grab(self)
            self.touch = touch
            return True

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            self.to_widget(*touch.pos)
            self.update_pos(touch)

    def update_pos(self, thing):
        self.pos = (self.pos[0] + self.touch.dpos[0], self.pos[1] + self.touch.dpos[1])

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            die_basket = self.parent.parent.die_basket
            keepers = die_basket.keepers

            self.scale -= .1

            if self.collide_widget(die_basket) or touch.is_double_tap:
                self.add_to_keepers()

            elif not self.collide_widget(die_basket):
                self.remove_from_keepers()

            touch.ungrab(self)

    def add_to_keepers(self):
        die_basket = self.parent.parent.die_basket
        keepers = die_basket.keepers
        keeper_count = self.parent.parent.buttons.roll.keeper_count
        die_holders = die_basket.keeper_box.children

        if self not in keepers:
            keepers.append(self)
            die_holder = die_holders[(len(keepers) + len(keeper_count)) - 1]

            anim = Animation(pos=(die_holder.pos[0] + 20, die_holder.pos[1]), d=0.5, t='out_quart')
            if self.rotation <= 180:
                anim &= Animation(rotation=0, d=0.5)
            else:
                anim &= Animation(rotation=360, d=0.5)
            anim.start(self)
        else:
            for die_holder, keeper in zip(die_holders[len(keeper_count):], keepers):
                anim = Animation(pos=(die_holder.pos[0] + 20, die_holder.pos[1]), d=0.2)
                anim.start(keeper)

    def remove_from_keepers(self):
        die_basket = self.parent.parent.die_basket
        keepers = die_basket.keepers
        keeper_count = self.parent.parent.buttons.roll.keeper_count
        die_holders = die_basket.keeper_box.children

        if self in keepers:
            keepers.remove(self)

        for die_holder, keeper in zip(die_holders[len(keeper_count):], keepers):
            anim = Animation(pos=(die_holder.pos[0] + 20, die_holder.pos[1]), d=0.2)
            anim.start(keeper)


class Dice(Widget):

    def __init__(self, **kwargs):
        super(Dice, self).__init__(**kwargs)

        self.id = 'dice'

    def update_dice(self, num_dice, turn=False):
        if not turn:
            self.remove_dice([widget for widget in self.children
                              if widget not in self.parent.buttons.roll.keeper_count])
        else:
            self.remove_dice(self.children)

        # sound = sounds[random.randint(1, 6)]
        # sound.play()

        # Randomized dice positions.
        positions = [{'x': uniform(.05, .25), 'y': uniform(.4, .52)},  # Top row.
                     {'x': uniform(.35, .55), 'y': uniform(.4, .52)},
                     {'x': uniform(.65, .85), 'y': uniform(.4, .52)},
                     {'x': uniform(.05, .25), 'y': uniform(.15, .27)},  # Bottom row.
                     {'x': uniform(.35, .55), 'y': uniform(.15, .27)},
                     {'x': uniform(.65, .85), 'y': uniform(.15, .27)}]

        roll = [randint(1, 6) for _ in range(num_dice)]

        for x, pos in zip(roll, positions[:num_dice + 1]):
            scatter = DieScatter(id=str(x), scale=.8)
            image = Image(source=die_images[x])

            scatter.add_widget(image)
            self.add_widget(scatter)

            anim = Animation(pos=(self.parent.width * pos['x'], self.parent.height * pos['y']), d=0.5)
            anim &= Animation(rotation=randint(-360, 360), d=0.75)
            anim.start(scatter)

    def remove_dice(self, dice, turn=False):
        anim = Animation(pos=(-50, -50), d=0.5, t='in_out_quad')
        anim.bind(on_complete=lambda x, y: self.complete(y))
        if dice:
            for die in dice:
                anim.start(die)

    def complete(self, die):
        if die.parent:
            die.parent.remove_widget(die)


class GameButtonRow(BoxLayout):
    def __init__(self, **kwargs):
        super(GameButtonRow, self).__init__(**kwargs)
        roll = ObjectProperty()
        end_turn = ObjectProperty()
        keep = ObjectProperty()


class RulesButton(Button):
    def __init__(self, **kwargs):
        super(RulesButton, self).__init__(**kwargs)

    def on_press(self):
        popup = RulesPopup()
        popup.open()


class RulesPopup(Popup):
    def __init__(self, **kwargs):
        super(RulesPopup, self).__init__(**kwargs)
        self.title = 'How To Play'
        label = Label(text=msg)
        self.content = label
        self.size_hint = (.9, .9)


class KeepAll(Button):
    def __init__(self, **kwargs):
        super(KeepAll, self).__init__(**kwargs)

    def on_press(self):
        dice = self.parent.parent.dice.children
        for die in dice:
            if (die not in self.parent.parent.buttons.roll.keeper_count and
                    die not in self.parent.parent.die_basket.keepers):
                die.add_to_keepers()


class EndTurn(Button):
    def __init__(self, **kwargs):
        super(EndTurn, self).__init__(**kwargs)

    def on_press(self):
        self.parent.parent.parent.set_current_player()
        return True


class Roll(Button):
    keeper_count = ListProperty()

    def __init__(self, **kwargs):
        super(Roll, self).__init__(**kwargs)

    def on_press(self):
        die_basket = self.parent.parent.die_basket

        if die_basket.valid_basket == rgba(colors['valid']):
            for keeper in die_basket.keepers:
                self.keeper_count.append(keeper)
            if len(self.keeper_count) >= 6:
                self.keeper_count.clear()
            self.parent.parent.dice.update_dice(6 - len(self.keeper_count))

        self.parent.parent.update_round_score()

        for keeper in self.keeper_count:
            keeper.locked = True

        for keeper in die_basket.keepers:
            gray = InstructionGroup()
            gray.add(Color(.9, .9, .9,  .5))
            gray.add(Rectangle(pos=(5, 7), size=(keeper.size[0] - 15, keeper.size[1] - 15)))
            keeper.canvas.add(gray)

        die_basket.keepers.clear()
        self.update_color()
        return True

    def update_color(self):
        die_basket = self.parent.parent.die_basket.valid_basket
        if die_basket == rgba(colors['error']):
            self.background_color = rgba(colors['second off'])
            self.disabled = True
            self.color = [1, 1, 1, .3]

        elif die_basket == rgba(colors['valid']):
            self.background_color = rgba(colors['second dark'])
            self.text = 'Risk \'n Roll!'
            self.disabled = False
            self.color = rgba(colors['text'])


class Base(FloatLayout):
    die_basket = ObjectProperty()
    dice = ObjectProperty()
    score_area = ObjectProperty()
    buttons = ObjectProperty()
    active_game = ObjectProperty()
    list_o_players = deque()
    current_player = ObjectProperty()
    list_o_winners = ListProperty()

    def __init__(self, **kwargs):
        super(Base, self).__init__(**kwargs)

    def get_active_game(self):
        for screen in self.parent.parent.screens:
            if screen.name == 'name':
                self.active_game = screen.active_game
                return self.active_game

    def get_active_game_players(self):
        for player in self.active_game.player_list:
            self.list_o_players.append(player)
        return self.list_o_players

    def update_round_score(self, red=None):
        die_basket = self.die_basket
        if die_basket.valid_basket == rgba(colors['valid']):
            self.current_player.round_score += die_basket.basket_score
            self.update_display('round')
            die_basket.basket_score = 0

            if not red:
                die_basket.valid_basket = rgba(colors['error'])
                self.buttons.roll.background_color = rgba(colors['prime off'])

        die_basket.basket_score = 0

    def update_total_score(self):
        if self.die_basket.valid_basket == rgba(colors['valid']):
            if self.current_player.total_score == 0 and self.current_player.round_score < 500:
                self.current_player.round_score = 0

            if self.current_player.total_score > 0 or self.current_player.round_score >= 500:
                self.current_player.total_score += self.current_player.round_score
                self.current_player.round_score = 0

        else:
            self.current_player.round_score = 0

    def update_display(self, score_type, font_size=None):
        for player_score in self.score_area.children:
            if player_score.id == self.current_player.name:
                player_area = player_score

        if score_type == 'name':
            self.update_name_display(player_area.name, font_size)
        if score_type == 'round' or score_type == 'basket':
            self.update_round_display(player_area.round, score_type, font_size)
        if score_type == 'total':
            self.update_total_display(player_area.total, font_size)
        if score_type == 'progress':
            self.update_progress_display(player_area.progress)
        if score_type == 'solo total':
            self.update_solo_total_display(player_area.total)

    def update_name_display(self, player_area, font_size):
        if font_size == 'big':
            player_area.markup = True
            player_area.text = f'[u]{self.current_player.name}[/u]'
            player_area.font_size = 25
            player_area.bold = True
        elif font_size == 'small':
            player_area.markup = False
            player_area.text = self.current_player.name
            player_area.font_size = 22
            player_area.bold = False

    def update_round_display(self, player_area, score_type, font_size):
        if font_size == 'big':
            player_area.bold = True
        elif font_size == 'small':
            player_area.bold = False

        if score_type == 'basket':
            player_area.text = 'Round: {}'.format(str(self.current_player.round_score +
                                                      self.die_basket.basket_score))
        if score_type == 'round':
            player_area.text = f'Round: {str(self.current_player.round_score)}'

    def update_total_display(self, player_area, font_size):
        if font_size == 'big':
            player_area.bold = True
        elif font_size == 'small':
            player_area.bold = False

        player_area.text = f'Total: {str(self.current_player.total_score)}'

    def update_progress_display(self, player_area):
        player_area.bold = True
        player_area.text = f'{self.parent.turn} / 5'

    def update_solo_total_display(self, player_area):
        player_area.bold = True
        player_area.text = f'{self.current_player.total_score} / 5000'


class DieHolder(Widget):
    def __init__(self, **kwargs):
        super(DieHolder, self).__init__(**kwargs)


class KeeperBox(BoxLayout):
    def __init__(self, **kwargs):
        super(KeeperBox, self).__init__(**kwargs)


class DieBasket(FloatLayout):
    keepers = ListProperty()
    basket_score = NumericProperty()
    valid_basket = ListProperty()
    active_game = ObjectProperty()
    keeper_box = ObjectProperty()

    def __init__(self, **kwargs):
        super(DieBasket, self).__init__(**kwargs)

        self.valid_basket = rgba(colors['valid'])

    def on_keepers(self, instance, value):
        choice = [int(child.id) for child in self.keepers]

        score = self.active_game.keep_score(choice)
        self.basket_score = score
        self.parent.update_display('basket')

        scored = self.active_game.validate_choice(choice)
        scored = not bool(scored)

        roll = self.parent.buttons.roll
        if not scored or not choice:
            self.valid_basket = rgba(colors['error'])
            roll.update_color()

        if scored and choice:
            self.valid_basket = rgba(colors['valid'])
            roll.update_color()


class SoloGameButton(Button):
    def __init__(self, **kwargs):
        super(SoloGameButton, self).__init__(**kwargs)

    def on_press(self):
        for screen in self.parent.parent.parent.screens:
            if screen.name == 'number':
                screen.num_players = 1
        self.parent.parent.parent.current = 'name'


class SoloPLayerScore(BoxLayout):
    def __init__(self, **kwargs):
        super(SoloPLayerScore, self).__init__(**kwargs)


class SoloGameScreen(Screen):
    base = ObjectProperty()
    turn = NumericProperty(0)

    def __init__(self, **kwargs):
        super(SoloGameScreen, self).__init__(**kwargs)

    def set_current_player(self):
        self.base.update_round_score(red=True)
        self.base.update_total_score()
        self.base.die_basket.valid_basket = rgba(colors['valid'])
        self.base.buttons.roll.update_color()
        self.base.buttons.roll.text = 'Roll \'em!'
        self.base.current_player.round_score = 0
        self.base.die_basket.keepers.clear()
        self.base.buttons.roll.keeper_count.clear()
        self.base.dice.remove_dice(self.base.dice.children, turn=True)
        self.base.update_display('round')
        self.base.update_display('progress')
        self.base.update_display('solo total')
        self.turn += 1

        if self.base.current_player.total_score >= 5000 or self.turn > 5:
            for screen in self.parent.screens:
                if screen.name == 'results':
                    screen.winners = [self.base.current_player]
            self.parent.current = 'results'

    def on_enter(self, *args):
        self.base.get_active_game()
        self.base.get_active_game_players()

        player = self.base.list_o_players[0]
        self.base.current_player = player
        player_score = SoloPLayerScore(id=player.name)

        name_area = player_score.name
        round_area = player_score.round
        total_area = player_score.total
        prog_area = player_score.progress

        name_area.markup = True
        name_area.text = f'[u]{player.name}[/u]'
        name_area.font_size = 32
        name_area.bold = True

        round_area.bold = True
        round_area.text = f'Round: {str(0)}'

        total_area.bold = True
        total_area.text = f'Total: {str(0)}'

        prog_area.bold = True

        self.base.score_area.add_widget(player_score)
        self.set_current_player()


class Screens(ScreenManager):
    def __init__(self, **kwargs):
        super(Screens, self).__init__(**kwargs)

        self.add_widget(MenuScreen(name='menu'))
        self.add_widget(PlayerNumberScreen(name='number'))
        self.add_widget(SoloGameScreen(name='solo'))
        self.add_widget(PlayerNameScreen(name='name'))
        self.add_widget(GameScreen(name='game'))
        self.add_widget(ResultsScreen(name='results'))

        self.current = 'menu'


class GameApp(App):

    def build(self):
        return self.root


if __name__ == '__main__':
    GameApp().run()
