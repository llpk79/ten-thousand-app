from pydice import DicePhysics
import pymunk as pm

space = DicePhysics()
NUM_DICE = 6


def is_space(space):
    return isinstance(space.space, pm.Space)


def has_four_walls(space):
    for shape in space.space.shapes:
        shape.cache_bb()
        # print(shape.bb)
    return len([shape for shape in space.space.shapes if isinstance(shape, pm.Segment)]) == 4


space.add_dice(NUM_DICE)


def has_six_dice(space):
    return len([shape for shape in space.space.shapes if isinstance(shape, pm.Poly)]) == NUM_DICE


space.start_dice()


def dice_are_moving(space):
    return all([abs(shape.body.velocity[0]) > 0 for shape in space.space.shapes if isinstance(shape, pm.Poly)])


def dice_stay_in_box(space):
    die_paths = space.roll_dice()
    outside_box = []
    for die_path in die_paths:
        print(die_path)
        for point in die_path:
            if point[0] > 500 or point[1] > 1000:
                outside_box.append(point)
    return len(outside_box) == 0


print(has_four_walls(space), is_space(space), has_six_dice(space), dice_are_moving(space), dice_stay_in_box(space))
