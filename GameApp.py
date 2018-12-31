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
from kivy.uix.widget import Widget
from kivy.uix.scatter import Scatter
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.image import Image
from kivy.utils import rgba

from collections import deque
from media import sounds, die_images
from logic import Game
from colors import colors
from random import randint


class ButtonLabel(Label):
    def __init__(self, **kwargs):
        super(ButtonLabel, self).__init__(**kwargs)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            return True


class PlayerNumberScreen(Screen):
    num_players = ObjectProperty()

    def set_num_players(self, num_players):
        self.num_players = num_players
        self.parent.current = 'name'


class FocusInput(TextInput):
    def __init__(self, **kwargs):
        super(FocusInput, self).__init__(**kwargs)

        self.focus = True
        self.write_tab = False

    def on_focus(self, widget, value):
        if self.parent and not self.focus:
            self.parent.add_player(self, value)


class PlayerNameScreen(Screen):
    player_names = ListProperty()
    active_game = ObjectProperty()
    num_players = NumericProperty()

    def get_num_players(self):
        for screen in self.parent.screens:
            if screen.name is 'number':
                self.num_players = screen.num_players

    def add_player(self, name, valid):
        if not valid and name.text != '':
            self.player_names.append(name.text)

            if len(self.player_names) == self.num_players:
                self.active_game = Game(self.player_names)
                self.parent.current = 'game'

    def on_enter(self):
        self.get_num_players()
        player_num = self.num_players

        for i in range(1, self.num_players + 1):
            label = Label(text=f'Enter Player {player_num}\'s name:',
                          color=rgba(colors['text']),
                          pos_hint={'x': .2, 'y': (i / 10) + .45},
                          size_hint=(.25, .05),
                          id=str(player_num))
            self.add_widget(label)
            self.add_widget(FocusInput(multiline=False,
                                       pos_hint={'x': .25, 'y': (i / 10) + .4},
                                       size_hint=(.25, .05)))
            player_num -= 1


class MenuScreen(Screen):
    def __init__(self, **kwargs):
        super(MenuScreen, self).__init__(**kwargs)


class PlayerScore(BoxLayout):
    def __init__(self, **kwargs):
        super(PlayerScore, self).__init__(**kwargs)

        self.add_widget(Label(id='name'))
        self.add_widget(Label(id='round'))
        self.add_widget((Label(id='total')))


class GameScreen(Screen):
    active_game = ObjectProperty()
    list_o_players = deque()
    current_player = ObjectProperty()
    list_o_winners = ListProperty()

    def __init__(self, **kwargs):
        super(GameScreen, self).__init__(**kwargs)

    def get_active_game(self):
        for screen in self.parent.screens:
            if screen.name == 'name':
                self.active_game = screen.active_game
                return self.active_game

    def get_active_game_players(self):
        for player in self.active_game.player_list:
            self.list_o_players.append(player)
        return self.list_o_players

    def set_current_player(self):
        if self.current_player is not None:
            self.update_round_score(red=True)
            self.base.die_basket.valid_basket = rgba(colors['valid'])
            self.update_total_score()
            self.current_player.round_score = 0
            self.update_display('round')
            self.base.die_basket.keepers.clear()
            self.base.roll.update_color()
            self.base.roll.keeper_count.clear()
            self.base.dice.clear_widgets()
            self.update_display('name', 'small')

        if not any([player.total_score >= 2000 for player in self.list_o_players]):
            temp = self.list_o_players.popleft()
            self.current_player = temp
            self.update_display('name', 'big')
            self.list_o_players.append(temp)

        else:
            self.list_o_winners.append(self.current_player)
            self.current_player = self.list_o_players.popleft()
            self.update_display('name', 'big')

            if not self.list_o_players:
                self.parent.current = 'results'

    def update_round_score(self, red=None):
        if self.base.die_basket.valid_basket == rgba(colors['valid']):
            curr_basket_score = self.base.die_basket.basket_score
            self.current_player.round_score += curr_basket_score
            self.update_display('round')
            self.base.die_basket.basket_score = 0

            if not red:
                self.base.die_basket.valid_basket = rgba(colors['error'])
                self.base.roll.background_color = rgba(colors['prime off'])

    def update_display(self, score_type, font_size=None):
        for child in self.children:
                if child.id == 'score_area':
                    for kid in child.children:
                        if kid.id == self.current_player.name:
                            for imp in kid.children:

                                if imp.id == 'round':
                                    if score_type == 'basket':
                                        imp.color = rgba(colors['text'])
                                        imp.text = 'Round: {}'.format(str(self.current_player.round_score +
                                                                          self.ids['die_basket'].basket_score))
                                    if score_type == 'round':
                                        imp.color = rgba(colors['text'])
                                        imp.text = f'Round: {str(self.current_player.round_score)}'

                                elif imp.id == 'total':
                                    if score_type == 'total':
                                        imp.color = rgba(colors['text'])
                                        imp.text = f'Total: {str(self.current_player.total_score)}'

                                elif imp.id == 'name':
                                    if font_size == 'big':
                                        imp.color = rgba(colors['text'])
                                        imp.font_size = 32
                                        imp.bold = True

                                    elif font_size == 'small':
                                        imp.color = rgba(colors['text'])
                                        imp.font_size = 20
                                        imp.bold = False

    def update_total_score(self):
        if self.ids['die_basket'].valid_basket == rgba(colors['valid']):
            if self.current_player.total_score == 0 and self.current_player.round_score < 500:
                self.current_player.round_score = 0

            if self.current_player.total_score > 0 or self.current_player.round_score >= 500:
                self.current_player.total_score += self.current_player.round_score
                self.current_player.round_score = 0

        else:
            self.current_player.round_score = 0

        self.update_display('total')

    def on_enter(self, *args):
        self.get_active_game()
        self.get_active_game_players()
        self.set_current_player()

        score_area = BoxLayout(size_hint=(1, .05),
                               pos_hint={'x': 0, 'y': .9},
                               orientation='horizontal',
                               id='score_area')

        for i, player in enumerate(reversed(self.list_o_players)):
            new = PlayerScore(id=player.name)

            for child in new.children:
                if child.id == 'name':
                    child.text = player.name
                    child.color = rgba(colors['text'])

                    if i == 0:
                        child.bold = True
                        child.font_size = 32
                    else:
                        child.font_size = 20
                    child.texture_update()
                    child.size_hint = (child.texture_size[0] / 30, 1)

                if child.id == 'round':
                    child.font_size = 20
                    child.color = rgba(colors['text'])
                    child.text = f'Round: {str(player.round_score)}'

                if child.id == 'total':
                    child.font_size = 20
                    child.color = rgba(colors['text'])
                    child.text = f'Total: {str(player.total_score)}'

            score_area.add_widget(new)
        self.add_widget(score_area)


class KeeperBox(BoxLayout):
    def __init__(self, **kwargs):
        super(KeeperBox, self).__init__(**kwargs)


class ResultsScreen(Screen):
    winners = ListProperty()

    def __init__(self, **kwargs):
        super(ResultsScreen, self).__init__(**kwargs)

    def get_winners(self):
        for screen in self.parent.screens:
            if screen.name == 'game':
                self.winners = screen.list_o_winners

    def on_enter(self, *args):
        self.get_winners()
        winners = sorted(self.winners, key=lambda x: x.total_score, reverse=True)

        self.add_widget(Label(text=f'{winners[0].name} wins !!\n\nWith {winners[0].total_score} points!',
                              color=rgba(colors['text']),
                              font_size=40,
                              bold=True,
                              size_hint=(.5, .5),
                              pos_hint={'x': .25, 'y': .35}))

    def play_again(self):
        pass

    def exit(self):
        pass


class DieScatter(Scatter):
    touch = ObjectProperty()

    def __init__(self, **kwargs):
        super(DieScatter, self).__init__(**kwargs)
        self.trigger = Clock.create_trigger(self.update_pos)
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
            self.trigger()

    def update_pos(self, thing):
        self.pos = (self.pos[0] + self.touch.dpos[0], self.pos[1] + self.touch.dpos[1])

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            self.scale -= .1
            die_basket = self.parent.parent.die_basket
            keepers = die_basket.keepers
            keeper_count = self.parent.parent.roll.keeper_count
            die_holders = die_basket.keeper_box.children
            if self.collide_widget(die_basket) and self not in keepers:
                keepers.append(self)
                die_holder = die_holders[(len(keepers) + len(keeper_count)) - 1]
                anim = Animation(pos=(die_holder.pos[0] + 20, die_holder.pos[1]), d=0.5, t='out_quart')
                if self.rotation <= 180:
                    anim &= Animation(rotation=0, d=0.5)
                else:
                    anim &= Animation(rotation=360, d=0.5)
                anim.start(self)
            if not self.collide_widget(die_basket) and self in keepers:
                keepers.remove(self)
                for die_holder, keeper in zip(die_holders[len(keeper_count):], keepers):
                    anim = Animation(pos=(die_holder.pos[0] + 20, die_holder.pos[1]), d=0.2)
                    anim.start(keeper)
            touch.ungrab(self)


class Dice(Widget):

    def __init__(self, **kwargs):
        super(Dice, self).__init__(**kwargs)
        self.id = 'dice'

    def update_dice(self, num_dice, turn=False):
        positions = [((490, 540), (215, 270)), ((245, 285), (230, 260)), ((50, 70), (236, 265)), ((60, 90), (85, 120)),
                     ((235, 275), (85, 130)), ((500, 550), (80, 120))]
        roll = [randint(1, 6) for _ in range(num_dice)]
        if not turn:
            self.clear_widgets([widget for widget in self.children if widget not in self.parent.roll.keeper_count])
        else:
            self.clear_widgets()

        # sound = sounds[random.randint(1, 6)]
        # sound.play()

        for x, pos in zip(roll, positions[:num_dice + 1]):
            scatter = DieScatter(id=str(x), scale=0.75)
            image = Image(source=die_images[x])
            scatter.add_widget(image)
            self.add_widget(scatter)

            anim = Animation(pos=(randint(*pos[0]), randint(*pos[1])), d=0.5)
            anim &= Animation(rotation=randint(-360, 360), d=0.75)
            anim.start(scatter)
            scatter.scale += 0.1


class EndTurn(Label):
    def __init__(self, **kwargs):
        super(EndTurn, self).__init__(**kwargs)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.parent.parent.set_current_player()
            return True


class Roll(Label):
    keeper_count = ListProperty()

    def __init__(self, **kwargs):
        super(Roll, self).__init__(**kwargs)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.grab(self)
            die_basket = self.parent.die_basket

            if die_basket.valid_basket == rgba(colors['valid']):
                for keeper in die_basket.keepers:
                    self.keeper_count.append(keeper)
                if len(self.keeper_count) >= 6:
                    self.keeper_count.clear()
                self.parent.dice.update_dice(6 - len(self.keeper_count))

            self.parent.parent.update_round_score()

            for keeper in self.keeper_count:
                keeper.locked = True

            for keeper in die_basket.keepers:
                with keeper.canvas.after:
                    Color(.9, .9, .9, .5)
                    Rectangle(pos=(keeper.pos[0] + 2, keeper.pos[1] + 7),
                              size=(keeper.children[0].size[0] - 25, keeper.children[0].size[1] - 25))
            die_basket.keepers.clear()
            touch.ungrab(self)
            self.update_color()
            return True

    def update_color(self):
        if self.parent.die_basket.valid_basket == rgba(colors['error']):
            with self.canvas.before:
                Color(rgba=rgba(colors['prime off']))
                Rectangle(pos=(self.pos[0] + 7, self.pos[1] + 7),
                          size=(self.texture_size[0] + 10, self.texture_size[1] + 5))

        elif self.parent.die_basket.valid_basket == rgba(colors['valid']):
            with self.canvas.before:
                Color(rgba=rgba(colors['prime']))
                Rectangle(pos=(self.pos[0] + 7, self.pos[1] + 7),
                          size=(self.texture_size[0] + 10, self.texture_size[1] + 5))


class Base(FloatLayout):
    die_basket = ObjectProperty()
    dice = ObjectProperty()
    roll = ObjectProperty()
    end_turn = ObjectProperty()

    def __init__(self, **kwargs):
        super(Base, self).__init__(**kwargs)


class DieHolder(Widget):
    def __init__(self, **kwargs):
        super(DieHolder, self).__init__(**kwargs)


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
        self.parent.parent.update_display('basket')

        scored = self.active_game.validate_choice(choice)
        scored = not bool(scored)

        roll = self.parent.roll
        if not scored or not choice:
            self.valid_basket = rgba(colors['error'])
            with roll.canvas.before:
                Color(rgba=rgba(colors['prime off']))
                Rectangle(pos=(roll.pos[0] + 7, roll.pos[1] + 7),
                          size=(roll.texture_size[0] + 10, roll.texture_size[1] + 5))

        if scored and choice:
            self.valid_basket = rgba(colors['valid'])
            with roll.canvas.before:
                Color(rgba=rgba(colors['prime']))
                Rectangle(pos=(roll.pos[0] + 7, roll.pos[1] + 7),
                          size=(roll.texture_size[0] + 10, roll.texture_size[1] + 5))


class Screens(ScreenManager):
    def __init__(self, **kwargs):
        super(Screens, self).__init__(**kwargs)
        self.add_widget(MenuScreen(name='menu'))
        self.add_widget(PlayerNumberScreen(name='number'))
        self.add_widget(PlayerNameScreen(name='name'))
        self.add_widget(GameScreen(name='game'))
        self.add_widget(ResultsScreen(name='results'))
        self.current = 'menu'


class GameApp(App):

    def build(self):
        return self.root


if __name__ == '__main__':
    GameApp().run()
