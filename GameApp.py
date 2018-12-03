import kivy
import random
import re

kivy.require('1.10.1')

from kivy.app import App
from kivy.core.audio import SoundLoader
from kivy.lang import Builder
from kivy.graphics import *
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
from logic import Game, HumanPlayer, ComPlayer


Builder.load_string("""
<MenuScreen>
    name: 'menu'
    FloatLayout:
        Image:
            source: 'images/pattern.png'
            allow_stretch: True
            keep_ratio: False
        Button:
            text: 'Let\\'s play some dice!'
            size_hint: (.2, .1)
            pos_hint: {'x': .4, 'y': .45}
            on_press: root.manager.current = 'number'


<PlayerNameScreen>
    name: 'name'
    on_enter:  self.on_enter_call(root.manager.screens)
    FloatLayout:
        Image:
            source: 'images/pattern.png'
            allow_stretch: True
            keep_ratio: False

<PlayerNumberScreen>
    name: 'number'
    # num_players: num_players_input.text
    FloatLayout:
        Image:
            source: 'images/pattern.png'
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
    size_hint: (.15, .1)
    pos_hint: {'x': .75, 'y': .4}
    text: 'Roll'
    font_size: 50
    background_color: .21, .45, .3, 1

<Keep>:
    size_hint: (.15, .1)
    pos_hint: {'x': .75, 'y': .2}
    text: 'Keep'
    font_size: 50
    background_color: .75, .41, .03, 1


<Base>:
    Image:
        source: 'images/tabletop2.jpg'
        allow_stretch: True
        keep_ratio: False


<GameScreen>
    name: 'game'
    Base:
        die_basket: die_basket
        dice: dice
        keep: keep
        roll: roll
        id: base
        DieBasket:
            id: die_basket
        Dice:
            id: dice
        Keep:
            id: keep
            on_press: root.set_current_player()
        Roll:
            id: roll
            on_release: root.add_round_score()

""")


class IntroScreen(Screen):
    pass


class IntInput(TextInput):
    # TODO: try/except for invalid input.
    pat = re.compile(r'[1-3]')

    def insert_text(self, substring, from_undo=False):
        pat = self.pat
        s = re.match(pat, substring)
        if s:
            return super(IntInput, self).insert_text(substring, from_undo=from_undo)


class PlayerNumberScreen(Screen):
    num_players = NumericProperty()

    def call_back(self, text):
        self.num_players = int(text)
        self.parent.current = 'name'


class PlayerNameScreen(Screen):
    player_names = ListProperty()
    active_game = ObjectProperty()

    def get_num_players(self, screen_list):
        for screen in screen_list:
            if screen.name is 'number':
                return screen.num_players

    def on_enter_call(self, screen_list):
        num_players = self.get_num_players(screen_list)
        player_num = num_players
        for i in range(1, num_players + 1):
            self.add_widget(Label(text=f'Enter Player-{player_num}\'s name:',
                                  pos_hint={'x': .2, 'y': (i / 10) + .35},
                                  size_hint=(.25, .05)))
            self.add_widget(TextInput(multiline=False,
                                      pos_hint={'x': .25, 'y': (i / 10) + .3},
                                      size_hint=(.25, .05),
                                      id=f'player{player_num}',
                                      on_text_validate=self.add_player))
            player_num -= 1

    def add_player(self, name):
        num_players = self.get_num_players(self.parent.screens)
        self.player_names.append(name.text)
        if len(self.player_names) == num_players:
            self.active_game = Game(self.player_names)
            self.parent.current = 'game'


class MenuScreen(Screen):
    pass


class GameScreen(Screen):
    active_game = ObjectProperty()
    list_o_players = deque()
    current_player = ObjectProperty()

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
        temp = self.list_o_players.popleft()
        self.current_player = temp
        print(self.current_player.name)
        self.list_o_players.append(temp)

    def on_enter(self, *args):
        self.get_active_game()
        self.get_active_game_players()
        self.set_current_player()
        for i, player in enumerate(self.list_o_players):
            self.add_widget(Label(text=self.update_round_score(),
                                  size_hint=(.15, .05),
                                  pos_hint={'x': .1 + i/3, 'y': .9},
                                  id=player.name))

    def add_round_score(self):
        self.current_player.round_score += self.ids['die_basket'].basket_score
        print('ars', self.current_player.round_score)
        self.update_round_score()

    def update_round_score(self):
        print('urs', self.current_player.name, self.current_player.round_score)
        return f'{self.current_player.name} ' \
               f'Round Score: {self.current_player.round_score} ' \
               f'Total Score: {self.current_player.total_score}'


class ResultsScreen(Screen):
    # TODO: add results
    pass


class Die(Widget):
    def __init__(self, **kwargs):
        super(Die, self).__init__(**kwargs)

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            for widget in self.parent.walk():
                if isinstance(widget, Scatter):
                    die_basket = self.parent.parent.parent.die_basket
                    if widget.collide_widget(die_basket) and widget not in die_basket.keepers:
                        die_basket.keepers.append(widget)
                    if not widget.collide_widget(die_basket) and widget in die_basket.keepers:
                        die_basket.keepers.remove(widget)


class Dice(Widget):

    def __init__(self, **kwargs):
        super(Dice, self).__init__(**kwargs)

    def update_dice(self, num_dice):
        # TODO: add call to scoring function
        roll = [random.randint(1, 6) for _ in range(6 - num_dice)]
        self.clear_widgets()
        for x in range(len(roll)):
            image = Image(source=die_images[roll[x]])
            scatter = Scatter(
                center_x=self.parent.width * random.uniform(.1, .6),
                center_y=self.parent.height * random.uniform(.1, .5))
            new_die = Die(id=str(roll[x]))
            new_die.add_widget(image)
            scatter.add_widget(new_die)
            self.add_widget(scatter)


class Keep(Button):
    def __init__(self, **kwargs):
        super(Keep, self).__init__(**kwargs)


class Roll(Button):
    keeper_count = NumericProperty(0)

    def __init__(self, **kwargs):
        super(Roll, self).__init__(**kwargs)

    def on_press(self):
        self.keeper_count += len(self.parent.die_basket.keepers)
        if self.keeper_count == 6:
            self.keeper_count = 0
        self.parent.dice.update_dice(self.keeper_count)
        self.parent.die_basket.keepers.clear()


class Base(FloatLayout):
    die_basket = ObjectProperty()
    dice = ObjectProperty()
    roll = ObjectProperty()
    keep = ObjectProperty()

    def __init__(self, **kwargs):
        super(Base, self).__init__(**kwargs)


class DieBasket(BoxLayout):
    keepers = ListProperty()
    basket_score = NumericProperty()
    valid_basket = ListProperty()

    def __init__(self, **kwargs):
        super(DieBasket, self).__init__(**kwargs)
        self.valid_basket = [1, 0, 0, 1]

    def get_active_game(self):
        for screen in self.parent.parent.parent.screens:
            if screen.name == 'name':
                return screen.active_game

    def on_keepers(self, instance, value):
        active_game = self.get_active_game()
        children = [child.children for child in self.keepers]
        choice = [int(keeper[0].id) for keeper in children]
        scored = active_game.validate_choice(choice)
        scored = not bool(scored)
        if not scored or not choice:
            self.valid_basket = [1, 0, 0, 1]
        if scored and choice:
            self.valid_basket = [0, 1, 0, 1]
        score = active_game.keep_score(choice)
        self.basket_score = score
        print(self.basket_score)


sm = ScreenManager()
sm.add_widget(MenuScreen(name='menu'))
sm.add_widget(PlayerNumberScreen(name='number'))
sm.add_widget(PlayerNameScreen(name='name'))
sm.add_widget(GameScreen(name='game'))


class GameApp(App):

    def build(self):
        self.root = root = sm
        return root


if __name__ == '__main__':
    GameApp().run()
