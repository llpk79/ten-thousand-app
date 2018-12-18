import pymunk
from random import randint
import matplotlib.pyplot as plt

# Setup space and space variables.
space = pymunk.Space()
space.gravity = 0, 0
space.damping = 0.95  # Dice will lose velocity * (1 - damping)/sec. Imitates top-down physics.
size = (5, 5)
density = 0.25
elasticity = 0.5  # Bounciness.

# Create an area to throw dice in.
l_wall = pymunk.Segment(space.static_body, (0, 0), (25, -5), 5)
l_wall.collision_type = 2
l_wall.elasticity = 0.5
space.add(l_wall)

floor = pymunk.Segment(space.static_body, (0, 0), (-5, 50), 5)
floor.collision_type = 2
floor.elasticity = 0.5
space.add(floor)

r_wall = pymunk.Segment(space.static_body, (0, 50), (25, 55), 5)
r_wall.collision_type = 2
r_wall.elasticity = 0.5
space.add(r_wall)

ceiling = pymunk.Segment(space.static_body, (25, 0), (30, 50), 5)
ceiling.collision_type = 2
ceiling.elasticity = 0.5
space.add(ceiling)


# Make some dice models.
def make_box(density, position, elasticity):
    body = pymunk.Body()
    body.position = position
    box = pymunk.Poly.create_box(body, size=size)
    box.density = density
    box.collision_type = 1
    box.elasticity = elasticity
    return box


# Get a notification when we hit a wall or dice bounce off each other.


def touch_block(arbiter, space, stuff):
    # plt.plot(arbiter.shapes[1].body.position.int_tuple[1], arbiter.shapes[1].body.position.int_tuple[0], 'mp')
    print('block')
    return True


def touch_wall(arbiter, space, stuff):
    # plt.plot(arbiter.shapes[1].body.position.int_tuple[1], arbiter.shapes[1].body.position.int_tuple[0], 'bp')
    print('wall')
    return True


# Setup handlers.
handle = space.add_collision_handler(1, 1)
handle.begin = touch_block

handle1 = space.add_collision_handler(1, 2)
handle1.begin = touch_wall

# Dice starting positions.
positions = [(15, 30), (15, 35), (15, 45), (5, 45), (10, 30), (10, 40)]

# Add dice to dict as we make em.
box_dict = {i: make_box(density, position, elasticity) for i, position in enumerate(positions)}

# Need access to bodies as well.
body_dict = {key: box.body for key, box in box_dict.items()}

# Add boxes and their bodies to space.
for box, body in zip(box_dict.values(), body_dict.values()):
    space.add(box, body)

# Get things moving.
for shape in space.shapes:
    shape.body.apply_impulse_at_local_point((randint(300, 600), randint(-600, -300)))

# For plotting dice movement.
colors = {0: 'bo', 1: 'go', 2: 'co', 3: 'yo', 4: 'ko', 5: 'ro'}

# Track where dice until one slows down.
while abs(body_dict[0].velocity[1]) > 2:
    space.step(0.02)
    for i, box in enumerate(body_dict.values()):
        # print(box.position.int_tuple, box.velocity)
        plt.plot(box.position.int_tuple[1], box.position.int_tuple[0], colors[i])

plt.show()
