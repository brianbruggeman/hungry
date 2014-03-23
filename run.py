#!/usr/bin/env python
"""
Diamon Divas

Usage:
    diamond_divas
    diamond_divas -h | --help
    diamond_divas -d | --debug
    diamond_divas --version

Options:
    -h --help      Show this screen
    --version      Show version
    -d --debug     Run in debug mode
"""
VERSION = "0.1-dev"

import logging
import math
import os
import random
import sys
import time

import pygame as pg
# from pygame.locals import *


# ----------------------------------------------------------------------
# Utility Structures
# ----------------------------------------------------------------------
keyboard_controls = {
    'north': [],
    'south': [],
    'east': [],
    'west': [],
    'inventory': [pg.K_i, pg.K_b],
    'attack': [pg.K_r],
    'strafe_left': [pg.K_RIGHT, pg.K_d],
    'strafe_right': [pg.K_LEFT, pg.K_a],
    'rotate_left': [pg.K_q],
    'rotate_right': [pg.K_e],
    'move_forward': [pg.K_UP, pg.K_w],
    'move_backward': [pg.K_DOWN, pg.K_s],
}

keyboard_events = [
    getattr(pg, d)
    for d in dir(pg)
    if d.lower().startswith('key')
]

mouse_events = [
    getattr(pg, d)
    for d in dir(pg)
    if d.lower().startswith("mouse")
]

keyboard_mods = dict(
    (getattr(pg, d), d.lower().replace('kmod_', ''))
    for d in dir(pg)
    if d.lower().startswith('kmod_')
    if not d.lower().endswith('none')
)

game_path = os.path.dirname(os.path.abspath(__file__))


# ----------------------------------------------------------------------
# Utility Functions
# ----------------------------------------------------------------------
def load_image(filename):
    """
    Loads an image;  guesses the type of image by the extension
    """
    resources = os.path.join(game_path, 'resources')
    for fname in os.listdir(resources):
        bname, ext = os.path.splitext(fname)
        if filename in [bname, fname]:
            fpath = os.path.join(resources, fname)
            image = pg.image.load(fpath)
            if image.get_alpha() is None:
                image = image.convert()
            else:
                image = image.convert_alpha()
            return image, image.get_rect()
    return [None, None]


# ----------------------------------------------------------------------
# Utility Classes
# ----------------------------------------------------------------------
class LoggerFacade(object):

    """
    Sets up a mocked logging facility in case logger gives me issues.
    """

    def facade(self, *args, **kwds):
        print >> sys.stderr, " ".join(str(a) for a in args)

interface = ['log', 'debug', 'info', 'warning', 'error', 'critical',
             'exception', 'filter', 'handle', '__call__']
for faked in interface:
    setattr(LoggerFacade, faked, LoggerFacade.facade)


class SpriteSheet(object):
    """
    A convenient way to access a sprite sheet
    """

    def __init__(self, filename, sprite_size=(24, 24)):
        self.filename = filename
        self.x_offset = sprite_size[0]
        self.y_offset = sprite_size[1]
        self.sheet, self.rect = load_image(filename)

    def __getitem__(self, value=(0, 0)):
        """
        Provides a nice way to index the sprite sheet assuming all sprites
        are the exact same size.
        """
        # split out the indices
        if len(value) > 1:
            if isinstance(value[0], (tuple, list)):
                images = [self[val] for val in value]
                return images
            else:
                x_index, y_index = value
                # calculate the row
                new_x = x_index * self.x_offset
                # x_offset = new_x + self.x_offset - 1
                # calculate the column
                new_y = y_index * self.y_offset
                # y_offset = new_y + self.y_offset - 1
                # grab the pixels
                rect = pg.Rect((new_x, new_y, self.x_offset-1, self.y_offset-1))
                img = pg.Surface(rect.size)
                img.blit(self.sheet, (0, 0), rect)
                return img, rect
        return [None, None]

# ----------------------------------------------------------------------
# Object Classes
# ----------------------------------------------------------------------
class Player(pg.sprite.Sprite):

    """
    Player
    """
    STATES = [
        "standing",
        "sneaking",
        "walking",
        "talking",
        "climbing",
        "attacking",
        "being_attacked",
        "dancing",
        "dying",
        "dead",
    ]

    FACES = [
        "north",
        "south",
        "east",
        "west",
    ]

    @property
    def health(self):
        attr = '__health__'
        if not hasattr(self, attr):
            setattr(self, attr, self.default_health)
        return getattr(self, attr)
    
    @health.setter
    def health(self, value=0):
        attr = '__health__'
        setattr(self, attr, value)
        self.logger.debug('Player health = %s' % self.health)
        if self.health <= 0:
            self.logger.debug('Player died')
            pg.quit()


    def __init__(self, x=0, y=0, logger=None):
        # super(Player, self).__init__()
        pg.sprite.Sprite.__init__(self)
        self.logger = logger if logger is not None else LoggerFacade()
        self.sheet = SpriteSheet('player')
        self.image, self.rect = self.sheet[(0, 2)]
        self.area = pg.display.get_surface().get_rect()
        self.speed = 10
        self.orientation = "south"
        self.state = "standing"
        self.health = 3
        self.setup()

    def setup(self):
        self.state = "standing"
        self.movepos = [0, 0]
        # self.rect.center = self.movepos

    def update(self):
        moving = False
        newpos = self.rect.move(self.movepos)
        if self.area.contains(newpos):
            moving = True
            self.rect = newpos
        else:
            if self.area.x < newpos.x:
                newpos.x -= self.area.x
            if self.area.y < newpos.y:
                newpos.y -= self.area.y
            if self.area.contains(newpos):
                moving = True
                self.rect = newpos
        if moving is False:
            self.state = "standing"
        if self.orientation == "north":
            self.image, rect = self.sheet[(0, 3)]
        elif self.orientation == "east":
            self.image, rect = self.sheet[(0, 1)]
        elif self.orientation == "south":
            self.image, rect = self.sheet[(0, 2)]
        elif self.orientation == "west":
            self.image, rect = self.sheet[(0, 0)]
        if self.movepos == (0, 0):
            self.state = "standing"
        elif self.state == "standing":
            self.state = "walking"
        pg.event.pump()

    def move_north(self, event):
        self.movepos[1] -= self.speed
        self.orientation = "north"

    def move_south(self, event):
        self.movepos[1] += self.speed
        self.orientation = "south"

    def move_east(self, event):
        self.movepos[0] += self.speed
        self.orientation = "east"

    def move_west(self, event):
        self.movepos[0] -= self.speed
        self.orientation = "west"

    def move_forward(self, event):
        if self.orientation == "north":
            if event.type == 2:
                self.movepos[1] -= self.speed
            elif event.type == 3:
                self.movepos[1] = 0
        elif self.orientation == "south":
            if event.type == 2:
                self.movepos[1] += self.speed
            elif event.type == 3:
                self.movepos[1] = 0
        elif self.orientation == "east":
            if event.type == 2:
                self.movepos[0] += self.speed
            elif event.type == 3:
                self.movepos[0] = 0
        elif self.orientation == "west":
            if event.type == 2:
                self.movepos[0] -= self.speed
            elif event.type == 3:
                self.movepos[0] = 0

    def move_backward(self, event):
        if self.orientation == "north":
            if event.type == 2:
                self.movepos[1] += self.speed
            elif event.type == 3:
                self.movepos[1] = 0
        elif self.orientation == "south":
            if event.type == 2:
                self.movepos[1] -= self.speed
            elif event.type == 3:
                self.movepos[1] = 0
        elif self.orientation == "east":
            if event.type == 2:
                self.movepos[0] -= self.speed
            elif event.type == 3:
                self.movepos[0] = 0
        elif self.orientation == "west":
            if event.type == 2:
                self.movepos[0] += self.speed
            elif event.type == 3:
                self.movepos[0] = 0

    def rotate_right(self, event):
        move_event = 2
        if event.type == move_event:
            if self.orientation == "north":
                self.orientation = "east"
            elif self.orientation == "east":
                self.orientation = "south"
            elif self.orientation == "south":
                self.orientation = "west"
            elif self.orientation == "west":
                self.orientation = "north"

    def rotate_left(self, event):
        move_event = 2
        if event.type == move_event:
            if self.orientation == "north":
                self.orientation = "west"
            elif self.orientation == "west":
                self.orientation = "south"
            elif self.orientation == "south":
                self.orientation = "east"
            elif self.orientation == "east":
                self.orientation = "north"

    def strafe_left(self, event):
        move_event = 2
        facing = self.orientation
        speed = self.speed if event.type == move_event else 0
        speed = -speed if facing in ['south', 'west'] else speed
        pos_index = 0 if facing in ['north', 'south'] else 1
        # self.logger.debug("((%s) movepos[%s] += %s" % (event.type, pos_index, speed))
        self.movepos[pos_index] = speed

    def strafe_right(self, event):
        move_event = 2
        facing = self.orientation
        speed = self.speed if event.type == move_event else 0
        speed = -speed if facing in ['north', 'east'] else speed
        pos_index = 0 if facing in ['north', 'south'] else 1
        # self.logger.debug("((%s) movepos[%s] += %s" % (event.type, pos_index, speed))
        self.movepos[pos_index] = speed

    def handle_event(self, event):
        if event.type in keyboard_events:
            if event.key in keyboard_controls.get('strafe_left'):
                self.strafe_left(event)
            elif event.key in keyboard_controls.get('strafe_right'):
                self.strafe_right(event)
            if event.key in keyboard_controls.get('rotate_left'):
                self.rotate_left(event)
            elif event.key in keyboard_controls.get('rotate_right'):
                self.rotate_right(event)
            if event.key in keyboard_controls.get('move_forward'):
                self.move_forward(event)
            elif event.key in keyboard_controls.get('move_backward'):
                self.move_backward(event)
            if 0:
                etype = "pressed" if event.type == 2 else "released"
                key = pg.key.name(event.key)
                mods = [
                    keyboard_mods.get(m, '')
                    for m in sorted(keyboard_mods)
                    if m & event.mod
                    ]
                if key:
                    mods.append(key)
                key = "+".join(m for m in mods)
                self.logger.debug('<Event %s "%s">' % (etype, key))


class Bullet(object):

    def __init__(self, point, vector, logger=None):
        pass

class Zombie(pg.sprite.Sprite):

    def __init__(self, player, logger=None):
        # super(Player, self).__init__()
        pg.sprite.Sprite.__init__(self)
        self.logger = logger if logger is not None else LoggerFacade()
        self.sheet = SpriteSheet('zombie')
        self.image, self.rect = self.sheet[(0, 0)]
        self.area = pg.display.get_surface().get_rect()
        self.speed = 2
        self.health = 1
        self.attack = 1
        self.player = player
        self.spawn()

    def spawn(self):
        rect_x = self.rect[2]
        rect_y = self.rect[3]
        wx = self.area[2]
        wy = self.area[3]
        x, y = 0, 0
        x = random.randint(0, wx - 1)
        y = random.randint(0, wy - 1)
        if x > (wx - 24):
            x = wx - self.rect[3]
        x = 0 if x < (wx / 2.0) else wx - 24
        y = 0 if y < (wy / 2.0) else wy - 24
        self.rect.x = x
        self.rect.y = y
        self.movepos = [0, 0]
        # self.rect.center = self.movepos

    def find_player(self):
        xp = self.player.rect.x
        yp = self.player.rect.y
        xz = self.rect.x
        yz = self.rect.y
        dx = (xp - xz)
        dy = (yp - yz)
        if (dx == 0) and (dy == 0):
            pass
        else:
            dx, dy = ((xp - xz)/math.sqrt((xp - xz) ** 2 + (yp - yz) ** 2),
                      (yp - yz)/math.sqrt((xp - xz) ** 2 + (yp - yz) ** 2))
        return dx, dy

    def update(self):
        moving = False
        dx, dy = self.find_player()
        if pg.sprite.collide_rect(self, self.player):
            self.attack_player()
        dx = round(dx) if dx != 0 else 0
        dy = round(dy) if dy != 0 else 0
        self.movepos = (dx * self.speed, dy * self.speed)
        newpos = self.rect.move(self.movepos)
        if self.area.contains(newpos):
            self.rect = newpos
        else:
            if self.area.x < newpos.x:
                newpos.x -= self.area.x
            if self.area.y < newpos.y:
                newpos.y -= self.area.y
            if self.area.contains(newpos):
                self.rect = newpos
        pg.event.pump()

    def attack_player(self):
        self.player.health -= self.attack

def main(args):
    # Setup the logging
    dbg = args.get('debug')
    logger = logging.getLogger(__file__) if dbg else LoggerFacade()
    if not isinstance(logger, LoggerFacade):
        if dbg:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)

    # Create a window
    pg.init()
    window = pg.display.set_mode((800, 600))
    pg.display.set_caption('Basic Walkabout')

    # Add Background
    background = pg.Surface(window.get_size())
    background = background.convert()
    background.fill((0, 0, 0))
    width, height = window.get_size()
    w, h = int(width / 2.0), int(height / 2.0)
    player = Player(w, h, logger)
    zombies = [Zombie(player, window)]
    # player_sprites = pg.sprite.RenderPlain(player)
    clock = pg.time.Clock()
    frames_per_second = 60
    frames = 0
    spawn_rate = 300
    window.blit(background, (0, 0))
    old_rect = player.rect

    running = True
    while running:
        clock.tick(frames_per_second)
        frames += 1
        if frames > spawn_rate:
            frames = 0
            if spawn_rate > 21:
                spawn_rate -= 20
            zombies.append(Zombie(player, window))

        # Handle Events
        for event in pg.event.get():
            player.handle_event(event)
            if event.type in keyboard_events:
                if event.key == pg.K_ESCAPE:
                    logging.debug('ESCAPE pressed.  Quitting')
                    pg.quit()
                    running = False
            if hasattr(event, 'type') and event.type == pg.QUIT:
                running = False

        # Update display
        window.blit(background, (0, 0))
        player.update()
        [z.update() for z in zombies]
        [window.blit(z.image, z.rect) for z in zombies]
        window.blit(player.image, player.rect)
        pg.display.update()

    logger.debug('Done.')

if __name__ == "__main__":
    from docopt import docopt

    args = docopt(__doc__, version=VERSION)
    main(args)
