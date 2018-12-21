# Copyright 2018 Paul Kutrich. All rights reserved.
import pymunk
from random import randint
import matplotlib.pyplot as plt


class DicePhysics:

    def __init__(self):
        # Setup space and space variables.
        print('init')
        self.space = pymunk.Space()
        self.space.gravity = 0, 0
        self.space.damping = 0.9  # Dice will lose velocity * (1 - damping)/sec. Imitates top-down physics.
        self.size = 10, 10
        self.density = 0.1
        self.elasticity = 0.5  # Bounciness.
        self.body_dict = {}
        self.box_dict = {}

        # Create an area to throw dice in.
        self.l_wall = pymunk.Segment(self.space.static_body, (0, 0), (60, 0), 1)
        self.l_wall.collision_type = 2
        self.l_wall.elasticity = 0.5
        self.space.add(self.l_wall)

        self.floor = pymunk.Segment(self.space.static_body, (0, 0), (0, 120), 1)
        self.floor.collision_type = 2
        self.floor.elasticity = 0.5
        self.space.add(self.floor)

        self.r_wall = pymunk.Segment(self.space.static_body, (0, 120), (60, 120), 1)
        self.r_wall.collision_type = 2
        self.r_wall.elasticity = 0.5
        self.space.add(self.r_wall)

        self.ceiling = pymunk.Segment(self.space.static_body, (60, 0), (60, 120), 1)
        self.ceiling.collision_type = 2
        self.ceiling.elasticity = 0.5
        self.space.add(self.ceiling)

        # Setup handlers.
        self.handle = self.space.add_collision_handler(1, 1)
        self.handle.begin = self.touch_block

        self.handle1 = self.space.add_collision_handler(1, 2)
        self.handle1.begin = self.touch_wall

    # Make some dice models.
    def make_box(self):
        body = pymunk.Body()
        body.position = 5, 5
        box = pymunk.Poly.create_box(body, size=self.size)
        box.density = self.density
        box.collision_type = 1
        box.elasticity = self.elasticity
        return box

    # Get a notification when we hit a wall or dice bounce off each other.
    def touch_block(self, arbiter, space, stuff):
        print('block')
        return True

    def touch_wall(self, arbiter, space, stuff):
        print('wall')
        return True

    def add_dice(self, num_dice):
        print('add', num_dice)
        # Add dice to dict as we make em.
        self.box_dict = {i: self.make_box() for i, position in enumerate(range(num_dice))}

        # Need access to bodies as well.
        self.body_dict = {key: box.body for key, box in self.box_dict.items()}

        # Add boxes and their bodies to space.
        print('a', self.body_dict, self.box_dict)
        for box, body in zip(self.box_dict.values(), self.body_dict.values()):
            self.space.add(box, body)

    def start_dice(self):
        print('start')
        # Get things moving.
        for shape in self.space.shapes:
            self.space.step(0.005)
            shape.body.apply_impulse_at_local_point((randint(450, 600), randint(750, 900)))
        # for body in self.space.shapes:

    def roll_dice(self):
        print('roll')
        # For plotting dice movement.
        colors = {0: 'bo', 1: 'go', 2: 'co', 3: 'yo', 4: 'ko', 5: 'ro'}
        dice = []
        for _ in range(len(self.box_dict)):
            dice.append(list())

        # Track where dice until one slows down.
        while any([abs(body.velocity.int_tuple[1]) > 10 for body in self.body_dict.values()]):
            self.space.step(1/60)
            for i, box in enumerate(self.body_dict.values()):
                # print(box.angle)
                dice[i].append(box.position.int_tuple)
                plt.plot(box.position.int_tuple[1], box.position.int_tuple[0], colors[i])

        plt.show()
        return dice
