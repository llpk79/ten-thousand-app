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
        die_basket: die_basket
        dice: dice
        end_turn: end_turn
        roll: roll
        player_score: player_score
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
        try:
            self.num_players = int(text)
            self.parent.current = 'name'
        except ValueError as e:
            print(e)


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

    def on_enter(self, *args):
        self.get_active_game()
        self.get_active_game_players()
        self.set_current_player()
        score_area = BoxLayout(size_hint=(1, .05),
                               pos_hint={'x': 0, 'y': .9},
                               orientation='horizontal',
                               id='score_area')
        for player in reversed(self.list_o_players):
            new = PlayerScore(id=player.name)

            for child in new.children:
                if child.id == 'name':
                    child.text = player.name
                    child.texture_update()
                    child.size_hint = (child.texture_size[0] / 30, 1)
                if child.id == 'round':
                    child.text = f'Round: {str(player.round_score)}'
                if child.id == 'total':
                    child.text = f'Total: {str(player.total_score)}'

            score_area.add_widget(new)
        self.add_widget(score_area)

    def add_round_score(self, red=None):
        if self.ids['die_basket'].valid_basket == [0, 1, 0, 1]:
            curr_basket_score = self.ids['die_basket'].basket_score
            self.current_player.round_score += curr_basket_score
            self.update_display('round')
            self.ids['die_basket'].basket_score = 0
            if not red:
                self.ids['die_basket'].valid_basket = [1, 0, 0, 1]

    def update_display(self, score_type):
            for child in self.children:
                if child.id == 'score_area':
                    for kid in child.children:
                        if kid.id == self.current_player.name:
                            for imp in kid.children:
                                if imp.id == score_type:
                                    if score_type == 'round':
                                        imp.text = f'Round: {str(self.current_player.round_score)}'
                                    if score_type == 'total':
                                        imp.text = f'Total: {str(self.current_player.total_score)}'

    def update_total_score(self):
        if self.ids['die_basket'].valid_basket == [0, 1, 0, 1]:
            if self.current_player.total_score == 0 and self.current_player.round_score < 500:
                self.current_player.round_score = 0

            if self.current_player.total_score > 0 or self.current_player.round_score > 500:
                self.current_player.total_score += self.current_player.round_score
                self.current_player.round_score = 0

        else:
            self.current_player.round_score = 0

        self.update_display('total')
        self.ids['dice'].update_dice(0)

    def set_current_player(self):
        if self.current_player is not None:
            self.add_round_score(red=True)
            self.update_total_score()
            self.current_player.round_score = 0
            self.update_display('round')
            self.ids['die_basket'].keepers.clear()
            self.ids['die_basket'].valid_basket = [1, 0, 0, 1]
            self.ids['roll'].keeper_count = 0
        temp = self.list_o_players.popleft()
        self.current_player = temp
        self.list_o_players.append(temp)


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


class EndTurn(Button):
    def __init__(self, **kwargs):
        super(EndTurn, self).__init__(**kwargs)


class Roll(Button):
    keeper_count = NumericProperty(0)

    def __init__(self, **kwargs):
        super(Roll, self).__init__(**kwargs)

    def on_press(self):
        if self.parent.die_basket.valid_basket == [0, 1, 0, 1]:
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
        self.valid_basket = [0, 1, 0, 1]

    def on_keepers(self, instance, value):
        children = [child.children for child in self.keepers]
        choice = [int(keeper[0].id) for keeper in children]
        scored = self.active_game.validate_choice(choice)
        scored = not bool(scored)
        if not scored or not choice:
            self.valid_basket = [1, 0, 0, 1]
        if scored and choice:
            self.valid_basket = [0, 1, 0, 1]
        score = self.active_game.keep_score(choice)
        self.basket_score = score


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
