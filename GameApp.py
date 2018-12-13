# Copyright 2018 Paul Kutrich. All rights reserved.
import kivy
import random
import re

kivy.require('1.10.1')

import kivy.graphics
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

from collections import deque
from media import sounds, die_images
from logic import Game


Builder.load_string("""
<MenuScreen>
    name: 'menu'
    FloatLayout:
        Image:
            source: 'images/tabletop5.jpg'
            allow_stretch: True
            keep_ratio: False
        Button:
            text: 'Let\\'s play some dice!'
            size_hint: (.2, .1)
            pos_hint: {'x': .4, 'y': .45}
            on_press: root.manager.current = 'number'

<ResultsScreen>
    name: 'result'
    FloatLayout:
        Image:
            source: 'images/tabletop1.jpg'
            allow_stretch: True
            keep_ratio: False
        Button:
            text: 'Play again?'
            size_hint: (.15, .05)
            pos_hint: {'x': .45, 'y': .2}
            on_press: root.play_again()
        Button:
            text: 'Exit'
            size_hint: (.15, .05)
            pos_hint: {'x': .45, 'y': .09}
            on_press: root.exit()

<PlayerNameScreen>
    name: 'name'
    FloatLayout:
        Image:
            source: 'images/tabletop4.jpg'
            allow_stretch: True
            keep_ratio: False

<PlayerNumberScreen>
    name: 'number'
    FloatLayout:
        Image:
            source: 'images/tabletop3.jpg'
            allow_stretch: True
            keep_ratio: False
        Label:
            text: 'How many people are playing?\\nUp to three can play.'
            size_hint: (.2, .05)
            pos_hint: {'x': .27, 'y': .575}
        IntInput:
            id: num_players_input
            multiline: False
            on_text_validate: root.call_back(self.text)
            size_hint: (.3, .05)
            pos_hint: {'x': .25, 'y': .5}
            focus: True

<DieBasket>
    # valid_basket: valid_basket
    size_hint: .9, .25
    pos_hint: {'x': .05, 'y': .6}
    Image:
        source: 'images/basket.jpg'
        allow_stretch: True
        keep_ratio: False
        canvas.after:
            Color: 
                rgba: root.valid_basket
            Line:
                rectangle: self.x - 1, self.y - 1, self.width + 2, self.height + 2

<Roll>:
    text: 'Roll'
    size_hint: (.15, .15)
    pos_hint: {'x': .75, 'y': .4}
    font_size: 50
    background_color: .21, .45, .3, 1

<EndTurn>:
    text: 'End\\nTurn'
    size_hint: (.15, .2)
    pos_hint: {'x': .75, 'y': .15}
    font_size: 50
    background_color: .75, .41, .03, 1

<Base>:
    Image:
        source: 'images/tabletop2.jpg'
        allow_stretch: True
        keep_ratio: False

<PlayerScore>:
    size_hint: (.8, .2)
    pos_hint: {'x': .1, 'y': .8}

<GameScreen>
    name: 'game'
    Base:
        player_score: player_score
        die_basket: die_basket
        dice: dice
        end_turn: end_turn
        roll: roll
        id: base
        PlayerScore:
            id: player_score
        DieBasket:
            id: die_basket
            active_game: root.active_game
        Dice:
            id: dice
        EndTurn:
            id: end_turn
            on_press: root.set_current_player()
        Roll:
            id: roll
            on_release: root.update_round_score()
""")


class IntInput(TextInput):
    def __init__(self, **kwargs):
        super(IntInput, self).__init__(**kwargs)

    def insert_text(self, substring, from_undo=False):
        if re.match(r'^[1-3]$', substring):
            return super(IntInput, self).insert_text(substring, from_undo=False)


class PlayerNumberScreen(Screen):
    num_players = NumericProperty()

    def call_back(self, text):
        try:
            self.num_players = int(text)
            self.parent.current = 'name'

        except ValueError as e:
            print(e)


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
            self.add_widget(Label(text=f'Enter Player {player_num}\'s name:',
                                  pos_hint={'x': .2, 'y': (i / 10) + .45},
                                  size_hint=(.25, .05),
                                  id=str(player_num)))

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
            self.update_total_score()
            self.current_player.round_score = 0
            self.update_display('round')
            self.ids['die_basket'].keepers.clear()
            self.ids['die_basket'].valid_basket = [1, 0, 0, 1]
            self.ids['roll'].keeper_count = 0
            self.ids['roll'].background_color = [.21, .45, .3, .5]
            self.update_display('name', 'small')

        if not any([player.total_score > 2000 for player in self.list_o_players]):
            temp = self.list_o_players.popleft()
            self.current_player = temp
            self.update_display('name', 'big')
            self.list_o_players.append(temp)

        else:
            self.list_o_winners.append(self.current_player)
            self.current_player = self.list_o_players.popleft()
            self.update_display('name', 'big')

            if not self.list_o_players:
                self.parent.current = 'result'

    def update_round_score(self, red=None):
        if self.ids['die_basket'].valid_basket == [.4, .69, .3, 1]:
            curr_basket_score = self.ids['die_basket'].basket_score
            self.current_player.round_score += curr_basket_score
            self.update_display('round')
            self.ids['die_basket'].basket_score = 0

            if not red:
                self.ids['die_basket'].valid_basket = [1, 0, 0, 1]
                self.ids['roll'].background_color = [.21, .45, .3, .5]

    def update_display(self, score_type, font=None):
        for child in self.children:
                if child.id == 'score_area':
                    for kid in child.children:
                        if kid.id == self.current_player.name:
                            for imp in kid.children:

                                if imp.id == 'round':
                                    if score_type == 'basket':
                                        imp.text = 'Round: {}'.format(str(self.current_player.round_score +
                                                                          self.ids['die_basket'].basket_score))
                                    if score_type == 'round':
                                        imp.text = f'Round: {str(self.current_player.round_score)}'

                                elif imp.id == 'total':
                                    if score_type == 'total':
                                        imp.text = f'Total: {str(self.current_player.total_score)}'

                                elif imp.id == 'name':
                                    if font == 'big':
                                        imp.font_size = 25
                                        imp.bold = True

                                    elif font == 'small':
                                        imp.font_size = 15
                                        imp.bold = False

    def update_total_score(self):
        if self.ids['die_basket'].valid_basket == [.4, .69, .3, 1]:
            if self.current_player.total_score == 0 and self.current_player.round_score < 500:
                self.current_player.round_score = 0

            if self.current_player.total_score > 0 or self.current_player.round_score >= 500:
                self.current_player.total_score += self.current_player.round_score
                self.current_player.round_score = 0

        else:
            self.current_player.round_score = 0

        self.update_display('total')
        self.ids['dice'].update_dice(0)

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

                    if i == 0:
                        child.bold = True
                        child.font_size = 25
                    child.texture_update()
                    child.size_hint = (child.texture_size[0] / 30, 1)

                if child.id == 'round':
                    child.text = f'Round: {str(player.round_score)}'

                if child.id == 'total':
                    child.text = f'Total: {str(player.total_score)}'

            score_area.add_widget(new)
        self.add_widget(score_area)


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

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.scale += .1
            touch.grab(self)
            self.touch = touch
            return True

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            self.to_widget(*touch.pos)
            self.trigger()
            # Clock.schedule_once(self.update_other, 0)

    def update_pos(self, thing):
        self.pos = (self.pos[0] + self.touch.dpos[0], self.pos[1] + self.touch.dpos[1])

    def update_other(self, thing):
        for child in self.parent.children:
            if child.collide_widget(self):
                child.pos = (child.pos[0] + self.touch.dpos[0], child.pos[1] + self.touch.dpos[1])

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            self.scale -= .1
            die_basket = self.parent.parent.die_basket
            if self.collide_widget(die_basket) and self not in die_basket.keepers:
                die_basket.keepers.append(self)
            if not self.collide_widget(die_basket) and self in die_basket.keepers:
                die_basket.keepers.remove(self)
            touch.ungrab(self)


class Dice(Widget):
    def __init__(self, **kwargs):
        super(Dice, self).__init__(**kwargs)
        self.id = 'dice'

    def update_dice(self, num_dice):
        roll = [random.randint(1, 6) for _ in range(6 - num_dice)]
        self.clear_widgets()

        sound = sounds[random.randint(1, 6)]
        sound.play()

        for x in range(len(roll)):
            image = Image(source=die_images[roll[x]])
            scatter = DieScatter(
                center_x=self.parent.width * .75,
                center_y=self.parent.height * .1,
                id=str(roll[x]))
            scatter.add_widget(image)
            self.add_widget(scatter)

        for child in self.parent.children:
            if child.id == 'dice':
                for kid in child.children:
                    anim = Animation(center_x=self.parent.width * random.uniform(.1, .6),
                                     center_y=self.parent.height * random.uniform(.1, .5),
                                     d=.25)
                    anim.start(kid)


class EndTurn(Button):
    def __init__(self, **kwargs):
        super(EndTurn, self).__init__(**kwargs)


class Roll(Button):
    keeper_count = NumericProperty(0)

    def __init__(self, **kwargs):
        super(Roll, self).__init__(**kwargs)

    def on_press(self):
        if self.parent.die_basket.valid_basket == [.4, .69, .3, 1]:
            self.keeper_count += len(self.parent.die_basket.keepers)

            if self.keeper_count >= 6:
                self.keeper_count = 0

            self.parent.dice.update_dice(self.keeper_count)
            self.parent.die_basket.keepers.clear()


class Base(FloatLayout):
    die_basket = ObjectProperty()
    dice = ObjectProperty()
    roll = ObjectProperty()
    end_turn = ObjectProperty()

    def __init__(self, **kwargs):
        super(Base, self).__init__(**kwargs)


class DieBasket(BoxLayout):
    keepers = ListProperty()
    basket_score = NumericProperty()
    valid_basket = ListProperty()
    active_game = ObjectProperty()

    def __init__(self, **kwargs):
        super(DieBasket, self).__init__(**kwargs)
        self.valid_basket = [.4, .69, .3, 1]

    def on_keepers(self, instance, value):
        choice = [int(child.id) for child in self.keepers]

        score = self.active_game.keep_score(choice)
        self.basket_score = score
        self.parent.parent.update_display('basket')

        scored = self.active_game.validate_choice(choice)
        scored = not bool(scored)

        if not scored or not choice:
            self.valid_basket = [1, 0, 0, 1]
            self.parent.parent.ids['roll'].background_color = [.21, .45, .3, .5]

        if scored and choice:
            self.valid_basket = [.4, .69, .3, 1]
            self.parent.parent.ids['roll'].background_color = [.21, .45, .3, 1]


sm = ScreenManager()
sm.add_widget(MenuScreen(name='menu'))
sm.add_widget(PlayerNumberScreen(name='number'))
sm.add_widget(PlayerNameScreen(name='name'))
sm.add_widget(GameScreen(name='game'))
sm.add_widget(ResultsScreen(name='result'))


class GameApp(App):

    def build(self):
        self.root = root = sm
        return root


if __name__ == '__main__':
    GameApp().run()
