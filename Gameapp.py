import kivy

kivy.require('1.10.1')

from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.scatter import Scatter
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.image import Image
from kivy.lang import Builder
from kivy.core.audio import SoundLoader
from kivy.properties import ObjectProperty, StringProperty, ListProperty, NumericProperty
import random
import re
from media import sounds, die_images

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

        # Button:
        #     text: 'This will be the player name setup screen'
        #     size_hint: (.35, .1)
        #     pos_hint: {'x': .4, 'y': .45}
        #     on_press: root.manager.current = 'game'


<PlayerNumberScreen>
    name: 'number'
    # num_players: num_players_input.text
    FloatLayout:
        Image:
            source: 'images/pattern.png'
            allow_stretch: True
            keep_ratio: False
        Label:
            text: 'How many people are playing?'
            size_hint: (.2, .05)
            pos_hint: {'x': .3, 'y': .55}
        IntInput:
            id: num_players_input
            multiline: False
            on_text_validate: root.call_back(self.text)
            size_hint: (.3, .05)
            pos_hint: {'x': .25, 'y': .5}

<DieBasket>
    size_hint: .9, .25
    pos_hint: {'x': .05, 'y': .6}
    size_hint: .9, .25
    Image:
        source: 'images/basket.jpg'
        allow_stretch: True
        keep_ratio: False
        canvas.after:
            Line:
                rectangle: self.x+1,self.y+1,self.width-1,self.height-1

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
        id: base
        DieBasket:
            id: die_basket
        Dice:
            id: dice
        Keep
        Roll:
            on_press: root.ids['dice'].update_dice(len(root.ids['base'].die_basket.keepers))
""")


class IntroScreen(Screen):
    pass


class IntInput(TextInput):
    pat = re.compile(r'\d')

    def insert_text(self, substring, from_undo=False):
        pat = self.pat
        s = re.match(pat, substring)
        print(s, substring)
        if s:
            return super(IntInput, self).insert_text(substring, from_undo=from_undo)


class PlayerNumberScreen(Screen):
    num_players = NumericProperty()

    def call_back(self, text):
        self.num_players = int(text)
        self.parent.current = 'name'


class Player(object):
    """Simple base class for Player objects.

    Players have a total score and name.

    """

    def __init__(self, name):
        """Player objects instantiated with total score and name.

        :param name: From Game.set_player.
        """
        self.total_score = 0
        self.name = name


class PlayerNameScreen(Screen):
    player_names = ListProperty()

    def get_num_players(self, screen_list):
        for screen in screen_list:
            if screen.name is 'number':
                num_players = screen.num_players
                player_num = num_players
        return player_num

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
            self.parent.current = 'game'
            print(self.parent)


class MenuScreen(Screen):
    pass


class GameScreen(Screen):
    pass


class ResultsScreen(Screen):
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
        print(num_dice)
        roll = [random.randint(1, 6) for _ in range(6 - num_dice)]
        self.clear_widgets()
        for x in range(len(roll)):
            image = Image(source=die_images[roll[x]])
            scatter = Scatter(
                center_x=self.parent.width * random.uniform(.1, .6),
                center_y=self.parent.height * random.uniform(.1, .5))
            new_die = Die(id='die' + str(roll[x]))
            new_die.add_widget(image)
            scatter.add_widget(new_die)
            self.add_widget(scatter)


class Keep(Button):
    def __init__(self, **kwargs):
        super(Keep, self).__init__(**kwargs)


class Roll(Button):
    def __init__(self, **kwargs):
        super(Roll, self).__init__(**kwargs)


class Base(FloatLayout):
    die_basket = ObjectProperty()

    def __init__(self, **kwargs):
        super(Base, self).__init__(**kwargs)


class DieBasket(BoxLayout):
    keepers = ListProperty()

    def __init__(self, **kwargs):
        super(DieBasket, self).__init__(**kwargs)

    def on_keepers(self, instance, value):
        print('kept!', self.keepers, instance, value)
        for keeper in self.keepers:
            print(keeper.children)


sm = ScreenManager()
sm.add_widget(MenuScreen(name='menu'))
sm.add_widget(PlayerNumberScreen(name='number'))
sm.add_widget(PlayerNameScreen(name='name'))
sm.add_widget(GameScreen(name='game'))


class Game(App):

    def build(self):
        self.root = root = sm
        return root


if __name__ == '__main__':
    Game().run()
