from math import floor
from random import randint
from pygame import Surface


class Renderable:
    """A class that represents a renderable object. It has a position, a surface, and a sticky coordinate system."""

    def __init__(self, x, y, surface, sticky_x=0, sticky_y=0):
        # x and y are the coordinates of the top left corner of the sprite
        self._x = x
        self._y = y
        # sticky coords are 0-1, 0 being the left/top and 1 being the right/bottom of the screen at whatever size it is
        self._sticky_x = sticky_x
        self._sticky_y = sticky_y
        # the surface stores the image data for the renderable
        self.surface = surface

    def render(self, screen):
        screen.blit(
            self.surface,
            (
                self._x + screen.get_width() * self._sticky_x,
                self._y + screen.get_height() * self._sticky_y,
            ),
        )


class PianoKey(Renderable):
    """A piano key is a renderable that has a note associated with it."""

    def __init__(self, note):
        self._note = note
        if self.is_white():
            surface = Surface((50, 230))
            surface.fill((255, 255, 255))
        else:
            surface = Surface((37.5, 142.5))
            surface.fill((0, 0, 0))
        offsets = [0, 0.625, 1, 1.625, 2, 3, 3.625, 4, 4.625, 5, 5.625, 6]
        super().__init__(
            floor(note / 12) * 350 + offsets[note % 12] * 50,
            -230,
            surface,
            0,
            1,
        )

    def is_white(self):
        return self._note % 12 not in [1, 3, 6, 8, 10]

    def is_black(self):
        return self._note % 12 in [1, 3, 6, 8, 10]
