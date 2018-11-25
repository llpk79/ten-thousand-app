import kivy

kivy.require('1.10.1')

from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.scatter import Scatter
from kivy.uix.image import Image
from kivy.core.audio import SoundLoader
from kivy.properties import ObjectProperty, StringProperty, ListProperty
import random
from media import sounds, die_images, tables


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


class Base(FloatLayout):
    die_basket = ObjectProperty()

    def __init__(self, **kwargs):
        super(Base, self).__init__(**kwargs)


class DieBasket(BoxLayout):
    keepers = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(DieBasket, self).__init__(**kwargs)


class Game(App):
    def build(self):
        self.root = root = Base()
        return root


if __name__ == '__main__':
    Game().run()
