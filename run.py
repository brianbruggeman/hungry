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

import os
import logging
import sys
import time

import pygame as pg
from pygame.locals import *


# ----------------------------------------------------------------------
# Utility Structures
# ----------------------------------------------------------------------
keyboard_controls = {
    'north': [pg.K_UP, pg.K_w],
    'south': [pg.K_DOWN, pg.K_s],
    'east': [pg.K_RIGHT, pg.K_d],
    'west': [pg.K_LEFT, pg.K_a],
    'inventory': [pg.K_i, pg.K_b],
    'attack': [pg.K_r],
    'strafe_left': [pg.K_q],
    'strafe_right': [pg.K_e]
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
        pg.event.pump()

    def move_north(self):
        self.movepos[1] -= self.speed
        self.state = "walking"
        self.orientation = "north"
        self.image, rect = self.sheet[(0, 3)]

    def move_south(self):
        self.movepos[1] += self.speed
        self.state = "walking"
        self.orientation = "south"
        self.image, rect = self.sheet[(0, 2)]

    def move_east(self):
        self.movepos[0] += self.speed
        self.state = "walking"
        self.orientation = "east"
        self.image, rect = self.sheet[(0, 1)]

    def move_west(self):
        self.movepos[0] -= self.speed
        self.state = "walking"
        self.orientation = "west"
        self.image, rect = self.sheet[(0, 0)]

    def strafe_left(self):
        self.state = "walking"
        pos_states = ['south', 'west']
        speed = self.speed if self.orientation in pos_states else -(self.speed)
        mov_xy = 1 if self.orientation in ['east', 'west'] else 0
        self.movepos[mov_xy] += speed
        self.state = "walking"

    def strafe_right(self):
        self.state = "walking"
        pos_states = ['north', 'east']
        speed = self.speed if self.orientation in pos_states else -(self.speed)
        mov_xy = 1 if self.orientation in ['east', 'west'] else 0
        self.movepos[mov_xy] += speed
        self.state = "walking"

    def handle_event(self, event):
        if event.type in keyboard_events and event.type == 2:
            if event.key in keyboard_controls.get('north'):
                self.move_north()
            elif event.key in keyboard_controls.get('south'):
                self.move_south()
            elif event.key in keyboard_controls.get('east'):
                self.move_east()
            elif event.key in keyboard_controls.get('west'):
                self.move_west()
            elif event.key in keyboard_controls.get('strafe_left'):
                self.strafe_left()
            elif event.key in keyboard_controls.get('strafe_right'):
                self.strafe_right()
            else:
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


def main(args):
    # Setup the logging
    dbg = args.get('debug')
    logger = logging.getLogger(__file__) if dbg else LoggerFacade()
    if not isinstance(logger, LoggerFacade):
        logging.basicConfig(level=logging.DEBUG)

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
    # player_sprites = pg.sprite.RenderPlain(player)
    clock = pg.time.Clock()
    frames_per_second = 60

    window.blit(background, (0, 0))
    old_rect = player.rect

    running = True
    while running:
        clock.tick(frames_per_second)

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
        if old_rect != player.rect:
            logger.debug('Player pos: %s' % player.rect)
        window.blit(player.image, player.rect)
        old_rect = player.rect
        pg.display.update()

    logger.debug('Done.')

if __name__ == "__main__":
    from docopt import docopt

    args = docopt(__doc__, version=VERSION)
    main(args)
