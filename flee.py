#!/usr/bin/env python
"""
Flee

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

import random
import logging
import math
import os
import sys

import pygame as pg


# ----------------------------------------------------------------------
# Utility Structures
# ----------------------------------------------------------------------
keyboard_controls = {
    'move_north': [pg.K_UP, pg.K_w],
    'move_south': [pg.K_DOWN, pg.K_s],
    'move_east': [pg.K_RIGHT, pg.K_d],
    'move_west': [pg.K_LEFT, pg.K_a],
    'inventory': [pg.K_i, pg.K_b],
    'attack': [pg.K_r],
    'strafe_left': [],
    'strafe_right': [],
    'rotate_left': [pg.K_q],
    'rotate_right': [pg.K_e],
    'move_forward': [],
    'move_backward': [],
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

KEY_PRESSED = 2
KEY_RELEASED = 3
Y_AXIS = 1
X_AXIS = 0


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
class PlayerDied(Exception):
    pass

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
        if self.health <= 0:
            setattr(self, attr, 0)
            logging.debug('Player is dead')
            raise PlayerDied()
            self.setup()
        else:
            logging.debug('Player health = %s' % self.health)

    def __init__(self, bullets, logger=None):
        # super(Player, self).__init__()
        pg.sprite.Sprite.__init__(self)
        self.logger = logger if logger is not None else LoggerFacade()
        self.sheet = SpriteSheet('player')
        self.image, self.rect = self.sheet[(0, 2)]
        self.area = pg.display.get_surface().get_rect()
        self.setup()

    def setup(self):
        if not hasattr(self, 'zombies'):
            self.zombies = []
        else:
            [self.zombies.pop() for z in self.zombies]
            self.zombies.append(Zombie(self, logging))
        self.image.get_rect().x = self.area.w/2.0
        self.image.get_rect().y = self.area.h/2.0
        self.state = "standing"
        self.movepos = [0, 0]
        self.speed = 10
        self.orientation = "south"
        self.state = "standing"
        self.health = 3
        self.score = 0
        # self.rect.center = self.movepos

    def update(self):
        moving = False
        self.score += 0.1 * len(self.zombies)
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
        if event.type == KEY_PRESSED:
            self.movepos[Y_AXIS] -= self.speed
        elif event.type == KEY_RELEASED:
            self.movepos[Y_AXIS] = 0

    def move_south(self, event):
        if event.type == KEY_PRESSED:
            self.movepos[Y_AXIS] += self.speed
        elif event.type == KEY_RELEASED:
            self.movepos[Y_AXIS] = 0

    def move_east(self, event):
        if event.type == KEY_PRESSED:
            self.movepos[X_AXIS] += self.speed
        elif event.type == KEY_RELEASED:
            self.movepos[X_AXIS] = 0

    def move_west(self, event):
        if event.type == KEY_PRESSED:
            self.movepos[X_AXIS] -= self.speed
        elif event.type == KEY_RELEASED:
            self.movepos[X_AXIS] = 0

    def move_forward(self, event):
        if self.orientation == "north":
            if event.type == KEY_PRESSED:
                self.movepos[Y_AXIS] -= self.speed
            elif event.type == KEY_RELEASED:
                self.movepos[Y_AXIS] = 0
        elif self.orientation == "south":
            if event.type == KEY_PRESSED:
                self.movepos[Y_AXIS] += self.speed
            elif event.type == KEY_RELEASED:
                self.movepos[Y_AXIS] = 0
        elif self.orientation == "east":
            if event.type == KEY_PRESSED:
                self.movepos[X_AXIS] += self.speed
            elif event.type == KEY_RELEASED:
                self.movepos[X_AXIS] = 0
        elif self.orientation == "west":
            if event.type == KEY_PRESSED:
                self.movepos[X_AXIS] -= self.speed
            elif event.type == KEY_RELEASED:
                self.movepos[X_AXIS] = 0

    def move_backward(self, event):
        if self.orientation == "north":
            if event.type == KEY_PRESSED:
                self.movepos[Y_AXIS] += self.speed
            elif event.type == KEY_RELEASED:
                self.movepos[Y_AXIS] = 0
        elif self.orientation == "south":
            if event.type == KEY_PRESSED:
                self.movepos[Y_AXIS] -= self.speed
            elif event.type == KEY_RELEASED:
                self.movepos[Y_AXIS] = 0
        elif self.orientation == "east":
            if event.type == KEY_PRESSED:
                self.movepos[X_AXIS] -= self.speed
            elif event.type == KEY_RELEASED:
                self.movepos[X_AXIS] = 0
        elif self.orientation == "west":
            if event.type == KEY_PRESSED:
                self.movepos[X_AXIS] += self.speed
            elif event.type == KEY_RELEASED:
                self.movepos[X_AXIS] = 0

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
        # logging.debug("((%s) movepos[%s] += %s" % (event.type, pos_index, speed))
        self.movepos[pos_index] = speed

    def strafe_right(self, event):
        move_event = 2
        facing = self.orientation
        speed = self.speed if event.type == move_event else 0
        speed = -speed if facing in ['north', 'east'] else speed
        pos_index = 0 if facing in ['north', 'south'] else 1
        # logging.debug("((%s) movepos[%s] += %s" % (event.type, pos_index, speed))
        self.movepos[pos_index] = speed

    def attack(self, event):
        b = Bullet()

    def is_alive(self):
        return self.health > 0

    def handle_event(self, event):
        if event.type in keyboard_events:
            for func, keys in keyboard_controls.items():
                if event.key in keys:
                    if hasattr(self, func):
                        func = getattr(self, func)
                        func(event)

class Bullet(object):

    def __init__(self, point, vector, logger=None):
        pass


class Zombie(pg.sprite.Sprite):

    def __init__(self, player, logger=None):
        # super(Player, self).__init__()
        pg.sprite.Sprite.__init__(self)
        logging = logger if logger is not None else LoggerFacade()
        self.sheet = SpriteSheet('zombie')
        self.image, self.rect = self.sheet[(0, 0)]
        self.area = pg.display.get_surface().get_rect()
        self.speed = 2
        self.health = 1
        self.attack = 1
        self.player = player
        self.spawn()

    def spawn(self):
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
        dx, dy = self.find_player()
        if pg.sprite.collide_rect(self, self.player):
            self.attack_player()
        if self.player.is_alive():
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
    pg.font.init()
    font_path = "resources/Tahoma.ttf"
    font_path = font_path if os.path.exists(font_path) else None
    myfont = pg.font.Font(font_path, 15)
    bigfont = pg.font.Font(font_path, 45)

    window = pg.display.set_mode((800, 600))
    # Add Background
    background = pg.Surface(window.get_size())
    background = background.convert()
    background.fill((0, 0, 0))
    window.blit(background, (0, 0))
    pg.display.set_caption('Flee')

    # player_sprites = pg.sprite.RenderPlain(player)
    clock = pg.time.Clock()
    frames_per_second = 60
    frames = 0

    running = True
    player_has_died = None
    while running:
        clock.tick(frames_per_second)
        if player_has_died is not False:
            # restart
            if player_has_died is True:
                # Keep game over and score up until a button is pressed
                etype = None
                while etype not in keyboard_events:
                    event = pg.event.wait()
                    etype = event.type
            player_has_died = False
            spawn_rate = 160
            bullets = []
            player = Player(bullets, logger)
            zombies = [Zombie(player, window)]
            player.zombies = zombies
            spawn_rate = 160
        try:
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
                        running = False
                if hasattr(event, 'type') and event.type == pg.QUIT:
                    running = False

            # Update display
            score = int(round(player.score))
            label = myfont.render("Score: %s" % score, 1, (255,255,127))
            zcount = len(zombies)
            zlabel = myfont.render("Zombies: %s" % zcount, 1, (255,255,127))
            window.blit(background, (0, 0))
            player.update()
            [z.update() for z in zombies]            
            [window.blit(z.image, z.rect) for z in zombies]
            window.blit(player.image, player.rect)
            window.blit(label, (window.get_rect().w - label.get_rect().w - 10, 10))
            window.blit(zlabel, (10, 10))
        except PlayerDied:
            player_has_died = True
            score = int(round(player.score))
            label = myfont.render("Score: %s" % score, 1, (255,255,127))
            zcount = len(zombies)
            zlabel = myfont.render("Zombies: %s" % zcount, 1, (255,255,127))
            window.blit(label, (window.get_rect().w - label.get_rect().w - 10, 10))
            window.blit(zlabel, (10, 10))
            game_over = bigfont.render("GAME OVER", 1, (255, 255, 127))
            wrect = window.get_rect()
            grect = game_over.get_rect()
            window.blit(game_over, (wrect.w/2.0 - grect.w/2.0, wrect.h/2.0 - grect.h/2.0))
        pg.display.update()
    pg.quit()
    logger.debug('Done.')

if __name__ == "__main__":
    try:
        from docopt import docopt

        args = docopt(__doc__, version=VERSION)
        main(args)
    except:
        args = {'debug': False}
        main(args)
