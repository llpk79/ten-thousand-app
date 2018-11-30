import kivy

kivy.require('1.10.1')

from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.scatter import Scatter
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.image import Image
from kivy.lang import Builder
from kivy.core.audio import SoundLoader
from kivy.properties import ObjectProperty, StringProperty, ListProperty
import random
from media import sounds, die_images, basket, tables


Builder.load_string("""
<MenuScreen>:
    name: 'menu'
    BoxLayout:
        Button:
            text: 'press for game screen'
            on_press: root.manager.current = 'game'
        Button:
            text: 'press me'

<DieBasket>
    size_hint: .9, .25
    pos_hint: {'x': .05, 'y': .7}
    size_hint: .9, .25
    Image:
        source: 'media/basket.jpg'
        allow_stretch: True
        keep_ratio: False
        canvas.after:
            Line:
                rectangle: self.x+1,self.y+1,self.width-1,self.height-1
<Roll>:
    id: roller
    on_press: dice.update_dice()
    center_x: root.width * .8
    top: root.top *.5
    text: 'Roll'
    font_size: 70
    background_color: .21, .45, .3, 1

<Keep>:
    id: keep
    center_x: root.width * .775
    top: root.top * .3
    text: 'Keep'
    font_size: 70
    background_color: .75, .41, .03, 1

<Base>:
    die_basket: die_basket
    DieBasket:
        id: die_basket
    Dice:
        id: dice

<GameScreen>:
    name: 'game'
    Image:
        source: 'media/tables2.jpg'
        allow_stretch: True
        keep_ratio: False
        Roll:
        Keep:
        Base
""")

class MenuScreen(Screen):
    pass


class GameScreen(Screen):
    pass


class Die(Widget):
    def __init__(self, **kwargs):
        super(Die, self).__init__(**kwargs)

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            for widget in self.parent.walk():
                if isinstance(widget, Scatter):
                    if widget.collide_widget(self.parent.parent.parent.die_basket):
                        print('FUCK YES!!')


class Dice(Widget):

    def __init__(self, **kwargs):
        super(Dice, self).__init__(**kwargs)

    def update_dice(self):
        roll = [random.randint(1, 6) for _ in range(6)]
        self.clear_widgets()
        for x in range(len(roll)):
            image = Image(source=die_images[roll[x]])
            scatter = Scatter(
                center_x=self.parent.width * random.uniform(.1, .6),
                center_y=self.parent.height * random.uniform(.1, .5),
                )
            new_die = Die(id='die'+str(roll[x]))
            new_die.add_widget(image)
            scatter.add_widget(new_die)
            self.add_widget(scatter)


class Keep(Button):
    def __init__(self, **kwargs):
        super(Keep, self).__init__(**kwargs)


class Roll(Button):
    def __init__(self, **kwargs):
        super(Roll, self).__init__(**kwargs)


class Base(GameScreen):
    die_basket = ObjectProperty()

    def __init__(self, **kwargs):
        super(Base, self).__init__(**kwargs)


class DieBasket(BoxLayout):
    keepers = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(DieBasket, self).__init__(**kwargs)


sm = ScreenManager()
sm.add_widget(MenuScreen(name='menu'))
sm.add_widget(GameScreen(name='game'))


class Game(App):

    def build(self):
        self.root = root = sm
        return root


if __name__ == '__main__':
    Game().run()
