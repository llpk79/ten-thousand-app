# Copyright 2018 Paul Kutrich. All rights reserved.
import kivy

kivy.require('1.10.1')

from kivy.graphics import *
from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty, ListProperty, NumericProperty, BooleanProperty
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
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


class PlayerNumDropDown(DropDown):
    def __init__(self, **kwargs):
        super(PlayerNumDropDown, self).__init__(**kwargs)

    def select(self, data):
        [child for child in self.parent.children[1].children][0].num_players = data
        self.dismiss()


class PlayerNumberScreen(Screen):
    num_players = NumericProperty()

    def __init__(self, **kwargs):
        super(PlayerNumberScreen, self).__init__(**kwargs)

    def on_num_players(self, other, num_players):
        if num_players:
            self.num_players = num_players
            self.set_label()

    def on_enter(self):
        player_num_button = Button(text='Set Number\nof Players',
                                   size_hint=(.3, .1),
                                   pos_hint={'x': .35, 'y': .65},
                                   background_normal='',
                                   background_color=rgba(colors['second dark']))
        self.add_widget(player_num_button)

        num_drop = PlayerNumDropDown()
        for i, num in zip(list(range(2, 7)), ['two', 'three', 'four', 'five', 'six']):
            btn = Button(text=num,
                         id=str(i),
                         size_hint_y=None,
                         height=44,
                         background_normal='',
                         background_color=rgba(colors['second light']))
            btn.bind(on_release=lambda button: num_drop.select(int(button.id)))
            num_drop.add_widget(btn)

        player_num_button.bind(on_release=num_drop.open)

    def set_label(self):
        self.num_label.text = f'Players Selected: {self.num_players}'
        self.cont.disabled = False


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
    game_mode = StringProperty()

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

                game = [screen for screen in self.parent.screens if screen.name == 'game'][0]
                if self.game_mode == 'comp':
                    game.comp_player = self.player_names[-1]
                else:
                    game.comp_player = ''

                if self.game_mode == 'game' or self.game_mode == 'comp':
                    self.parent.current = 'game'
                elif self.game_mode == 'solo':
                    self.parent.current = 'solo'

    def on_enter(self):
        self.get_num_players()
        if self.game_mode == 'comp':
            self.num_players += 1

        for i in range(1, self.num_players + 1):
            if self.game_mode == 'comp' and i == self.num_players:
                text = 'Enter Computer Player Name:'
                pos = {'x': .1, 'y': .4 + (self.num_players / 10) - (i * .15)}
            else:
                text = f'Enter Player {i}\'s name:'
                pos = {'x': .15, 'y': .4 + (self.num_players / 10) - (i * .15)}

            label = Label(text=text,
                          font_size=30,
                          color=rgba(colors['text']),
                          pos_hint=pos,
                          size_hint=(.25, .1),
                          id=str(i))
            self.add_widget(label)
            input_name = (FocusInput(multiline=False,
                                     font_size=30,
                                     pos_hint={'x': .475, 'y': .4 + (self.num_players / 10) - (i * .15)},
                                     size_hint=(.35, .09)))
            if i == 1:
                input_name.focus = True
            self.add_widget(input_name)


class MenuScreen(Screen):
    def __init__(self, **kwargs):
        super(MenuScreen, self).__init__(**kwargs)


class FriendsButton(Button):
    def __init__(self, **kwargs):
        super(FriendsButton, self).__init__(**kwargs)

    def on_release(self):
        name_screen = [screen for screen in self.parent.parent.screens if screen.name == 'name'][0]
        name_screen.game_mode = 'game'
        Clock.schedule_once(self.to_num_screen, .2)

    def to_num_screen(self, *args):
        self.parent.parent.current = 'number'


class MyOwnSelfButton(Button):
    def __init__(self, **kwargs):
        super(MyOwnSelfButton, self).__init__(**kwargs)

    def on_release(self):
        num_screen = [screen for screen in self.parent.parent.screens if screen.name == 'number'][0]
        num_screen.num_players = 1
        names = [screen for screen in self.parent.parent.screens if screen.name == 'name'][0]
        names.game_mode = 'comp'
        Clock.schedule_once(self.to_name_screen, .2)

    def to_name_screen(self, *args):
        self.parent.parent.current = 'name'


class SoloGameButton(Button):
    def __init__(self, **kwargs):
        super(SoloGameButton, self).__init__(**kwargs)

    def on_press(self):
        for screen in self.parent.parent.screens:
            if screen.name == 'number':
                screen.num_players = 1
                screen.game_mode = 'solo'
            if screen.name == 'name':
                screen.game_mode = 'solo'
        Clock.schedule_once(self.to_goal_screen, .2)

    def to_goal_screen(self, *args):
        self.parent.parent.current = 'goal'


class PlayerScore(BoxLayout):
    def __init__(self, **kwargs):
        super(PlayerScore, self).__init__(**kwargs)


class ScoreArea(BoxLayout):
    def __init__(self, **kwargs):
        super(ScoreArea, self).__init__(**kwargs)


class GameScreen(Screen):
    base = ObjectProperty()
    comp_player = StringProperty()

    def __init__(self, **kwargs):
        super(GameScreen, self).__init__(**kwargs)

    def on_enter(self, *args):
        self.base.get_active_game()
        self.base.get_active_game_players()

        for player in self.base.list_o_players:
            player_score = PlayerScore(id=player.name,
                                       pos=(self.base.score_area.x, 550))

            name_area = player_score.name
            round_area = player_score.round
            total_area = player_score.total
            total_plus_area = player_score.total_plus

            name_area.font_size = 32
            name_area.bold = True
            name_area.text = player.name.title()

            round_area.text = f'Round: {str(0)}'
            total_area.text = f'Total: {str(0)}'
            total_plus_area.text = f'Total + Round: {str(0)}'

            player.score_display = player_score

        self.base.score_area.add_widget(self.base.list_o_players[0].score_display)
        self.next_round()

    def next_round(self, *args):
        if not self.base.current_player or self.base.current_player.name == '':
            temp = self.base.list_o_players.popleft()
            self.base.current_player = temp
            self.base.list_o_players.append(temp)

            self.animate_indicator()
            return

        self.reset_round()
        self.animate_score_out()

    def get_next_player(self):
        if not any([player.total_score >= 2000 for player in self.base.list_o_players]):
            temp = self.base.list_o_players.popleft()
            self.base.current_player = temp
            self.base.list_o_players.append(temp)

        else:
            self.base.list_o_winners.append(self.base.current_player)
            self.base.current_player = self.base.list_o_players.popleft()

        if not self.base.list_o_players:
            self.find_winner()

        else:
            if self.base.current_player.name == self.base.parent.comp_player:
                Clock.schedule_once(self.base.buttons.roll.on_press, 1.)

    def find_winner(self):
        winners = sorted(self.base.list_o_winners, key=lambda player: player.total_score, reverse=True)
        tie = [winners[0]] + [winner for winner in winners[1:] if winner.total_score == winners[0].total_score]

        if len(tie) > 1:
            names = [win.name.title() for win in tie]
            ties = ' and '.join(names)
            message = f'It\'s a Tie!\n{ties}\n' \
                f'Win with {winners[0].total_score} points!'
        else:
            message = f'{winners[0].name.title()} Wins!\n\nWith {winners[0].total_score} points!'

        for screen in self.parent.screens:
            if screen.name == 'results':
                screen.message = message

        self.results_screen()

    def continue_overlord_turn(self):
        scoring_dice = [die for die in self.base.active_game.choose_dice(
            [die for die in self.base.dice.children if die not in self.base.buttons.roll.proto_keepers])]

        if not scoring_dice:
            Clock.schedule_once(self.base.buttons.end_turn.on_press, .5)
            return

        else:
            Clock.schedule_once(self.overlord_status_check, float(len(scoring_dice)))
            for i, die in enumerate(scoring_dice):
                Clock.schedule_once(die.add_to_keepers, float(i * .85 + .75))

    def overlord_status_check(self, *args):
        winners = sorted(self.base.list_o_winners, key=lambda player: player.total_score, reverse=True)

        if len(self.base.buttons.roll.proto_keepers) + len(self.base.die_basket.keepers) >= 6:
            Clock.schedule_once(self.base.buttons.roll.on_press, 1.)
            return

        elif winners and winners[0].total_score >= (self.base.current_player.total_score +
                                                    self.base.current_player.round_score +
                                                    self.base.die_basket.basket_score):
            Clock.schedule_once(self.base.buttons.roll.on_press, 1.)
            return

        elif not winners and (self.base.current_player.total_score +
                              self.base.current_player.round_score +
                              self.base.die_basket.basket_score) >= 2000:
            Clock.schedule_once(self.base.buttons.end_turn.on_press, 1.)
            return

        elif (self.base.current_player.round_score + self.base.die_basket.basket_score >= 500 and
                len(self.base.buttons.roll.proto_keepers) + len(self.base.die_basket.keepers) >= 3):
            Clock.schedule_once(self.base.buttons.end_turn.on_press, .1)
            return

        else:
            Clock.schedule_once(self.base.buttons.roll.on_press, 1.)
            return

    def reset_round(self):
        self.base.update_round_score(green_line=True)
        self.base.update_total_score()
        self.base.die_basket.valid_basket = rgba(colors['valid'])
        self.base.buttons.roll.update_color()
        self.base.buttons.roll.text = 'Roll \'em!'
        self.base.current_player.round_score = 0
        self.base.die_basket.keepers.clear()
        self.base.buttons.roll.proto_keepers.clear()
        self.base.dice.remove_dice(self.base.dice.children)
        self.base.update_display('name')
        self.base.update_display('total')
        self.base.update_display('round')
        self.base.update_display('basket')
        self.base.buttons.end_turn.disabled = True

    def results_screen(self):
        self.parent.current = 'results'

    def animate_indicator(self):
        indicator_pos = self.base.current_player.info.children[2]
        indicator = self.base.info.children[0]
        anim = Animation(pos=indicator_pos.pos, d=.25)
        anim &= Animation(scale=.25, d=.2)
        anim.start(indicator)

    def animate_score_out(self):
        curr_display = self.base.current_player.score_display
        anim = Animation(pos=(self.base.score_area.x + 4, 550), d=.25)
        anim.bind(on_complete=lambda animation, display: self.animate_score_in(display))
        anim.start(curr_display)

    def add_new_display(self, pos):
        new_display = self.base.current_player.score_display
        new_display.size_hint_x = .692
        new_display.pos = (pos[0], 555)
        self.base.add_widget(new_display)
        return new_display

    def animate_score_in(self, curr_display):
        pos = curr_display.pos
        self.base.score_area.remove_widget(curr_display)

        self.get_next_player()

        new_display = self.add_new_display(pos)

        self.animate_indicator()

        anim = Animation(pos=(self.base.score_area.x + 4, self.base.score_area.y + 4), d=.25)
        anim.bind(on_complete=lambda animation, display: self.animate_score_finish(display))
        anim.start(new_display)

    def animate_score_finish(self, new_display):
        self.base.remove_widget(new_display)
        self.base.score_area.add_widget(new_display)
        self.base.buttons.end_turn.disabled = False


class ResultsScreen(Screen):
    message = StringProperty()

    def __init__(self, **kwargs):
        super(ResultsScreen, self).__init__(**kwargs)

    def on_enter(self, *args):
        self.add_widget(Label(id='message',
                              text=self.message,
                              color=rgba(colors['text']),
                              halign='center',
                              font_size=40,
                              bold=True,
                              size_hint=(.5, .5),
                              pos_hint={'x': .25, 'y': .35}))

    def play_again(self):
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

    def reset_num_screen(self, screen):
        screen.num_players = 0

    def reset_name_screen(self, screen):
        screen.player_names.clear()
        screen.active_game = ObjectProperty()
        screen.clear_widgets(screen.children[:-1])
        screen.num_players = 0

    def reset_game_screen(self, screen):
        screen.base.info.box.clear_widgets()

        if screen.base.info.children[0].id == 'indi':
            screen.base.info.remove_widget(screen.base.info.children[0])

        screen.base.score_area.clear_widgets()
        screen.base.list_o_players.clear()
        screen.base.list_o_winners.clear()
        screen.base.current_player = ObjectProperty()
        screen.base.active_game = ObjectProperty()

    def reset_goal_screen(self, screen):
        screen.turn_limit = 0
        screen.point_goal = 0

    def reset_solo_screen(self, screen):
        screen.base.info.box.clear_widgets()
        screen.base.score_area.clear_widgets()
        screen.turn = 0
        screen.point_goal = 0
        screen.turn_limit = 0

    def reset_results_screen(self, screen):
        message = [child for child in screen.children if child.id == 'message'][0]
        screen.remove_widget(message)

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

    def add_to_keepers(self, *args):
        die_basket = self.parent.parent.die_basket
        keepers = die_basket.keepers
        proto_keepers = self.parent.parent.buttons.roll.proto_keepers
        die_holders = die_basket.keeper_box.children

        if self not in keepers:
            keepers.append(self)
            if (len(keepers) + len(proto_keepers) == 6 and
                    die_basket.valid_basket == rgba(colors['valid']) and
                    self.parent.parent.current_player.name != self.parent.parent.parent.comp_player):
                popup = SixKeepersPopup()
                popup.open()
            die_holder = die_holders[(len(keepers) + len(proto_keepers)) - 1]

            anim = Animation(pos=(die_holder.pos[0] + 20, die_holder.pos[1]), d=0.5, t='out_quart')
            if self.rotation <= 180:
                anim &= Animation(rotation=0, d=0.5)
            else:
                anim &= Animation(rotation=360, d=0.5)
            anim.start(self)

        else:
            for die_holder, keeper in zip(die_holders[len(proto_keepers):], keepers):
                anim = Animation(pos=(die_holder.pos[0] + 20, die_holder.pos[1]), d=0.2)
                anim.start(keeper)

    def remove_from_keepers(self):
        die_basket = self.parent.parent.die_basket
        keepers = die_basket.keepers
        proto_keepers = self.parent.parent.buttons.roll.proto_keepers
        die_holders = die_basket.keeper_box.children

        if self in keepers:
            keepers.remove(self)

        for die_holder, keeper in zip(die_holders[len(proto_keepers):], keepers):
            anim = Animation(pos=(die_holder.pos[0] + 20, die_holder.pos[1]), d=0.2)
            anim.start(keeper)


class Dice(Widget):
    num_dice = NumericProperty()

    def __init__(self, **kwargs):
        super(Dice, self).__init__(**kwargs)

        self.id = 'dice'

    def update_dice(self, num_dice):
        doomed_dice = [widget for widget in self.children if widget not in self.parent.buttons.roll.proto_keepers]
        self.remove_dice(doomed_dice)
        self.num_dice = num_dice
        Clock.schedule_once(self.update_dice_two, .8)

    def update_dice_two(self, *args):
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
            scatter = DieScatter(id=str(x), scale_max=.8, scale=.7)
            image = Image(source=die_images[x])

            scatter.add_widget(image)
            self.add_widget(scatter)

            new_dice.append(scatter)

            anim = Animation(pos=(self.parent.width * pos['x'] * .7, self.parent.height * pos['y']), d=0.5)
            anim &= Animation(rotation=randint(-360, 360), d=0.75)
            anim.start(scatter)

        if not self.parent.active_game.choose_dice(new_dice):
            popup = FarklePopup()
            popup.bind(on_dismiss=self.parent.parent.next_round)
            popup.open()
            if self.parent.current_player.name == self.parent.parent.comp_player:
                Clock.schedule_once(popup.dismiss, 1.)
                return
            return

        if self.parent.current_player.name == self.parent.parent.comp_player:
            self.parent.parent.continue_overlord_turn()

    def remove_dice(self, dice):
        anim = Animation(pos=(-50, -50), d=0.5, t='in_out_quad')
        anim.bind(on_complete=lambda x, y: self.complete(y))
        if dice:
            for die in dice:
                anim.start(die)

    def complete(self, die):
        if die.parent:
            self.remove_widget(die)


class Indicator(Scatter):
    def __init__(self, **kwargs):
        super(Indicator, self).__init__(**kwargs)
        self.scale = .01
        self.do_scale = False

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            return True


class InformationStation(FloatLayout):
    box = ObjectProperty()

    def __init__(self, **kwargs):
        super(InformationStation, self).__init__(**kwargs)

    def add_player_totals(self):
        base = self.parent
        for i, player in enumerate(base.list_o_players):
            lil_box = BoxLayout(id=player.name)
            turn_indicator = Widget(id='turn',
                                    size_hint=(.18, .1),
                                    pos_hint={'x': 0, 'y': .4})
            lil_box.add_widget(turn_indicator)

            lil_box.add_widget(Label(id='name',
                                     text=player.name.title(),
                                     size_hint=(.22, 1),
                                     font_size=22,
                                     text_size=(lil_box.width, None),
                                     shorten=True,
                                     shorten_from='right'))
            total = Label(id='total',
                          text=str(player.total_score),
                          font_size=22,
                          size_hint=(.6, 1))
            lil_box.add_widget(total)

            self.box.add_widget(lil_box)
            player.info = lil_box

        indicator = Indicator(id='indi')
        indicator.add_widget(Image(source=die_images[1]))
        self.add_widget(indicator)


class GameButtonRow(BoxLayout):
    roll = ObjectProperty()
    end_turn = ObjectProperty()
    keep = ObjectProperty()

    def __init__(self, **kwargs):
        super(GameButtonRow, self).__init__(**kwargs)


class RulesButton(Button):
    def __init__(self, **kwargs):
        super(RulesButton, self).__init__(**kwargs)

    def on_press(self):
        popup = RulesPopup()
        popup.open()


class KeepAll(Button):
    def __init__(self, **kwargs):
        super(KeepAll, self).__init__(**kwargs)

    def on_press(self):
        dice = self.parent.parent.dice.children
        for die in dice:
            if (die not in self.parent.parent.buttons.roll.proto_keepers and
                    die not in self.parent.parent.die_basket.keepers):
                die.add_to_keepers()


class RulesPopup(Popup):
    def __init__(self, **kwargs):
        super(RulesPopup, self).__init__(**kwargs)

        self.title = 'How To Play'
        self.title_align = 'center'

        label = Label(text=msg)

        self.content = label
        self.size_hint = (.9, .9)


class YouSurePopup(Popup):
    def __init__(self, **kwargs):
        super(YouSurePopup, self).__init__(**kwargs)

    def on_parent(self, *args):
        self.title = 'Are You Sure?!'
        self.title_align = 'center'

        label = Label(text='You still have points on the board!',
                      halign='center',
                      pos_hint={'x': 0, 'y': .2})

        btn = Button(text='Meh, I don\'t want those.',
                     size_hint=(.5, .2),
                     pos_hint={'x': .25, 'y': .1})
        btn.bind(on_release=self.leave_points)

        base = FloatLayout()
        base.add_widget(label)
        base.add_widget(btn)

        self.content = base
        self.size_hint = (.4, .3)

    def leave_points(self, *args):
        game_screen = [screen for screen in self.parent.children[1].screens if screen.name == 'game'][0]

        if len(game_screen.base.list_o_players) > 1:
            game_screen.next_round()
        else:
            [screen for screen in self.parent.children[1].screens if screen.name == 'solo'][0].next_round()

        self.dismiss()


class SixKeepersPopup(Popup):
    def __init__(self, **kwargs):
        super(SixKeepersPopup, self).__init__(**kwargs)

        self.title = 'Congratulations!'
        self.title_align = 'center'

        label = Label(text='You got six keepers! Roll \'em all again!',
                      halign='center')

        self.content = label
        self.size_hint = (.4, .3)


class ThresholdNotMet(Popup):
    def __init__(self, **kwargs):
        super(ThresholdNotMet, self).__init__(**kwargs)

        self.title = 'Hold Up!'
        self.title_align = 'center'

        label = Label(text='You haven\'t earned 500 points in one turn yet.\n\n Keep rolling!',
                      halign='center')

        self.content = label
        self.size_hint = (.4, .3)


class FarklePopup(Popup):
    def __init__(self, **kwargs):
        super(FarklePopup, self).__init__(**kwargs)

        self.title = 'Oh No!'
        self.title_align = 'center'

        label = Label(text='You did\'nt get any keepers! Your turn is over.\n\n:(',
                      halign='center')

        self.content = label
        self.size_hint = (.4, .3)


class NonKeeperKept(Popup):
    def __init__(self, **kwargs):
        super(NonKeeperKept, self).__init__(**kwargs)

        self.title = 'WARNING!!'
        self.title_align = 'center'

        label = Label(text='You have non-scoring dice in the scoring area.'
                           '\n\nRemove non-scoring dice to turn line green and continue',
                      halign='center',
                      pos_hint={'x': 0, 'y': .3})
        btn = RulesButton(text='See rules',
                          size_hint=(.5, .3),
                          pos_hint={'x': .25, 'y': .1})
        layout = FloatLayout()
        layout.add_widget(label)
        layout.add_widget(btn)

        self.content = layout
        self.size_hint = (.5, .4)


class EndTurn(Button):
    def __init__(self, **kwargs):
        super(EndTurn, self).__init__(**kwargs)

    def on_press(self, *args):
        base = self.parent.parent
        if (base.die_basket.valid_basket == rgba(colors['valid'])
                and base.current_player.total_score == 0
                and (base.current_player.round_score + base.die_basket.basket_score) < 500):
            popup = ThresholdNotMet()
            popup.open()

        elif (base.die_basket.valid_basket == rgba(colors['valid']) and
                ([die for die in base.active_game.choose_dice([die for die in base.dice.children
                                                               if die not in base.buttons.roll.proto_keepers])
                    if die not in base.die_basket.keepers])):
            popup = YouSurePopup()
            popup.open()

        elif (base.die_basket.valid_basket == rgba(colors['error']) and
              base.die_basket.keepers and
              base.active_game.validate_choice([int(die.id) for die in base.die_basket.keepers])):
            popup = NonKeeperKept()
            popup.open()

        else:
            base.parent.next_round()

        return True


class Roll(Button):
    proto_keepers = ListProperty()

    def __init__(self, **kwargs):
        super(Roll, self).__init__(**kwargs)

    def on_press(self, *args):
        die_basket = self.parent.parent.die_basket

        if die_basket.valid_basket == rgba(colors['valid']):
            for keeper in die_basket.keepers:
                self.proto_keepers.append(keeper)
            if len(self.proto_keepers) >= 6:
                self.proto_keepers.clear()
            self.parent.parent.dice.update_dice(6 - len(self.proto_keepers))

        self.parent.parent.update_round_score()

        for keeper in self.proto_keepers:
            keeper.locked = True

        for keeper in die_basket.keepers:
            gray = InstructionGroup()
            gray.add(Color(.9, .9, .9, .5))
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
    info = ObjectProperty()

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
        self.info.add_player_totals()
        return self.list_o_players

    def update_round_score(self, green_line=None):
        die_basket = self.die_basket
        if die_basket.valid_basket == rgba(colors['valid']):
            self.current_player.round_score += die_basket.basket_score
            self.update_display('round')
            die_basket.basket_score = 0

            if not green_line:
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

    def update_display(self, score_type):
        if score_type == 'round' or score_type == 'basket':
            self.update_round_display(score_type)
        if score_type == 'total':
            self.update_total_display()
        if score_type == 'progress':
            self.update_progress_display()
        if score_type == 'solo total':
            self.update_solo_total_display()

    def update_round_display(self, score_type):
        if score_type == 'basket':
            self.current_player.score_display.round.text = 'Round: {}'.format(str(self.current_player.round_score +
                                                                                  self.die_basket.basket_score))
            self.current_player.score_display.total_plus.text = 'Total + Round: {}'.format(
                str(self.current_player.total_score +
                    self.current_player.round_score +
                    self.die_basket.basket_score))
        if score_type == 'round':
            self.current_player.score_display.round.text = f'Round: {str(self.current_player.round_score)}'

    def update_total_display(self):
        self.current_player.info.children[0].text = str(self.current_player.total_score)
        self.current_player.score_display.text = f'Total: {str(self.current_player.total_score)}'

    def update_progress_display(self):
        self.current_player.score_display.progress.text = f'{self.parent.turn} / {self.parent.turn_limit}'

    def update_solo_total_display(self):
        self.current_player.score_display.total_plus.text = 'Total + Round: {}'.format(
                str(self.current_player.total_score +
                    self.current_player.round_score +
                    self.die_basket.basket_score))
        self.current_player.info.children[0].text = f'{self.current_player.total_score} / {self.parent.point_goal}'


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


class SoloPLayerScore(BoxLayout):
    def __init__(self, **kwargs):
        super(SoloPLayerScore, self).__init__(**kwargs)


class PointGoal(DropDown):
    def __init__(self, **kwargs):
        super(PointGoal, self).__init__(**kwargs)

    def select(self, data):
        self.parent.children[1].children[0].point_goal = data
        if self.parent.children[1].children[0].turn_limit:
            self.parent.children[1].children[0].cont.disabled = False


class TurnGoal(DropDown):
    def __init__(self, **kwargs):
        super(TurnGoal, self).__init__(**kwargs)

    def select(self, data):
        self.parent.children[1].children[0].turn_limit = data
        if self.parent.children[1].children[0].point_goal:
            self.parent.children[1].children[0].cont.disabled = False


class SoloGoalScreen(Screen):
    point_goal = NumericProperty()
    turn_limit = NumericProperty()

    def __init__(self, **kwargs):
        super(SoloGoalScreen, self).__init__(**kwargs)

    def on_enter(self):
        self.cont.disabled = True
        point_button = Button(pos_hint={'x': .1, 'y': .8},
                              size_hint=(.3, .1),
                              text='Set Points Goal',
                              font_size=30,
                              background_normal='',
                              background_color=rgba(colors['prime dark']))
        turn_button = Button(pos_hint={'x': .6, 'y': .8},
                             size_hint=(.3, .1),
                             text='Set Max Turns',
                             font_size=30,
                             background_normal='',
                             background_color=rgba(colors['prime dark']))
        self.add_widget(point_button)
        self.add_widget(turn_button)

        point_drop = PointGoal()
        for x in [2500, 5000, 7500, 10000, 15000]:
            btn = Button(text=str(x),
                         size_hint_y=None,
                         height=44,
                         background_normal='',
                         background_color=rgba(colors['second light']))
            btn.bind(on_release=lambda button: point_drop.select(int(button.text)))
            point_drop.add_widget(btn)
        point_button.bind(on_release=point_drop.open)

        turn_drop = TurnGoal()
        for x in [5, 10, 20, 30, 40]:
            btn = Button(text=str(x),
                         size_hint_y=None,
                         height=44,
                         background_normal='',
                         background_color=rgba(colors['second light']))
            btn.bind(on_release=lambda button: turn_drop.select(int(button.text)))
            turn_drop.add_widget(btn)
        turn_button.bind(on_release=turn_drop.open)

    def on_point_goal(self, thing, stuff):
        self.goals.points.text = f'Points goal: {self.point_goal}'
        if self.turn_limit and self.point_goal:
            self.set_difficulty()

    def on_turn_limit(self, thing, stuff):
        self.goals.turns.text = f'Turn limit: {self.turn_limit}'
        if self.point_goal and self.turn_limit:
            self.set_difficulty()

    def set_difficulty(self):
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


class SoloGameScreen(Screen):
    base = ObjectProperty()
    comp_player = StringProperty()
    turn = NumericProperty(0)
    point_goal = NumericProperty()
    turn_limit = NumericProperty()

    def __init__(self, **kwargs):
        super(SoloGameScreen, self).__init__(**kwargs)

    def on_enter(self, *args):
        self.base.get_active_game()
        self.base.get_active_game_players()

        for screen in self.parent.screens:
            if screen.name == 'goal':
                self.point_goal = screen.point_goal
                self.turn_limit = screen.turn_limit

        player = self.base.list_o_players[0]
        self.base.current_player = player
        player_score = SoloPLayerScore(id=player.name)

        name_area = player_score.name
        round_area = player_score.round
        total_plus_area = player_score.total_plus
        prog_area = player_score.progress

        name_area.text = player.name.title()
        name_area.font_size = 32
        name_area.bold = True

        round_area.text = f'Round: {str(0)}'
        total_plus_area.text = 'Total + Round: 0'
        prog_area.text = f'Turns: {self.turn} / {self.turn_limit}'

        player.score_display = player_score

        self.base.score_area.add_widget(player.score_display)
        self.next_round()

    def next_round(self, *args):
        self.base.update_round_score(green_line=True)
        self.base.update_total_score()
        self.base.die_basket.valid_basket = rgba(colors['valid'])
        self.base.buttons.roll.update_color()
        self.base.buttons.roll.text = 'Roll \'em!'
        self.base.current_player.round_score = 0
        self.base.die_basket.keepers.clear()
        self.base.buttons.roll.proto_keepers.clear()
        self.base.dice.remove_dice(self.base.dice.children)
        self.base.update_display('round')
        self.base.update_display('progress')
        self.base.update_display('solo total')

        if self.base.current_player.total_score >= self.point_goal or self.turn > self.turn_limit:
            if self.base.current_player.total_score >= self.point_goal:
                message = f'{self.base.current_player.name.title()} wins!\n\n' \
                    f'With {self.base.current_player.total_score} points!\n\nIn {self.turn - 1} turns!'
            else:
                message = f'Oh no, {self.base.current_player.name.title()}!\n\n' \
                    f'You\'re out of turns\n\nand only got {self.base.current_player.total_score} points.'
            for screen in self.parent.screens:
                if screen.name == 'results':
                    screen.message = message
            self.results_screen()
        self.turn += 1

    def results_screen(self):
        self.parent.current = 'results'


class Screens(ScreenManager):
    def __init__(self, **kwargs):
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

    def build(self):
        self.title = 'Ten Thousand'
        return self.root


if __name__ == '__main__':
    GameApp().run()
