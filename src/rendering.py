from math import ceil, floor
from random import randint, random
from time import time

from pygame import Surface

import store


class Renderable:
    """A class that represents a renderable object. It has a position, a surface, and a sticky coordinate system."""

    # x and y are the coordinates of the top left corner of the sprite
    _x: float
    _y: float
    # sticky coords are 0-1, 0 being the left/top and 1 being the right/bottom of the screen. They are used to make the renderable stick to the center or edges of the screen
    _sticky_x: float
    _sticky_y: float
    # the surface stores the image data for the renderable
    _surface: Surface
    # the children of this renderable (other renderables)
    _children: list[
        "Renderable"
    ]  # this is a type hint, but the class is in the process of being defined so it has to be a string

    def __init__(
        self,
        x: float,
        y: float,
        surface: Surface,
        sticky_x: float = 0.0,
        sticky_y: float = 0.0,
    ):

        self._x = x
        self._y = y
        self._sticky_x = sticky_x
        self._sticky_y = sticky_y
        self._surface = surface
        self._children = []

    def render(self, screen):
        screen.blit(
            self._surface,
            (
                self._x + screen.get_width() * self._sticky_x,
                self._y + screen.get_height() * self._sticky_y,
            ),
        )
        for child in self._children:
            child.render(screen)

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value: float):
        self._x = value

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value: float):
        self._y = value

    @property
    def sticky_x(self):
        return self._sticky_x

    @sticky_x.setter
    def sticky_x(self, value: float):
        self._sticky_x = value

    @property
    def sticky_y(self):
        return self._sticky_y

    @sticky_y.setter
    def sticky_y(self, value: float):
        self._sticky_y = value

    @property
    def children(self):
        return self._children

    def add_child(self, child):
        self._children.append(child)

    def remove_child(self, child):
        self._children.remove(child)


class Particle(Renderable):
    def __init__(
        self,
        x,
        y,
        velocity=(0, 0),
        lifetime=5,
        size=5,
        color=store.COLOR_PALETTE["particle"],
    ):
        self._velocity = velocity
        self._lifetime = lifetime
        self._size = size
        self._color = color
        self._time_when_created = time()
        self._surface = Surface((size, size))
        self._surface.fill(color)
        super().__init__(x, y, self._surface, 0, 1)

    def render(self, screen):
        age = time() - self._time_when_created
        if age > self._lifetime:
            # .remove isn't that performant for this use case, but I'll fix it if it becomes a problem
            store.particles.remove(self)
            return
        # fade out at the very end of the lifetime
        if age > self._lifetime * 0.75:
            self._surface.set_alpha(255 * (1 - age / self._lifetime))
        super().render(screen)
        self._x += self._velocity[0]
        self._y += self._velocity[1]
        self._velocity = (self._velocity[0], self._velocity[1] + 0.2)


class NoteBar(Renderable):
    """A moving bar that shows a note that has been played. These are children of the `PianoKey` class."""

    _scroll_speed: int
    """The speed at which the note bar moves up the screen in pixels per second."""
    _velocity: int
    """The velocity of the note, from 0 to 127."""

    def __init__(self, note: int, x: float, velocity: int, scroll_speed=50):
        self._note = note
        self._scroll_speed = scroll_speed
        self._time_when_played = time()
        self._release_time = None
        self._has_static_surface = False
        self._velocity = max(0, min(velocity, 127))
        super().__init__(x, 0, None, 0, 1)

    def release(self):
        self._release_time = time()

    def render(self, screen):
        # update y position (the 230 pixel offset makes the note bar appear to be above the piano, but rounding makes 229 look better)
        self._y = -229 - (time() - self._time_when_played) * self._scroll_speed

        # calculate the height of the note bar based on if it has been released or not
        if not self._has_static_surface:
            if self._release_time is None:
                height = (time() - self._time_when_played) * self._scroll_speed
                # create a new surface with the calculated height
                if self.is_white:
                    self._surface = Surface((50, height))
                else:
                    self._surface = Surface((37.5, height))
                # calculate the color of the note bar based on the velocity
                self._surface.fill(store.COLOR_PALETTE["note_bar"])
                self._surface.set_alpha(self._velocity * 2)
                # make some particles
                for _ in range(ceil(self._velocity / 127 * 5)):
                    store.particles.append(
                        Particle(
                            self._x + random() * self._surface.get_width(),
                            self._y + self._surface.get_height(),
                            (
                                randint(-4, 4) * self._velocity / 127,
                                randint(-8, -2) * self._velocity / 127,
                            ),
                            0.5,
                            3,
                        )
                    )
            else:
                # this is the case where the note has been released for the first frame
                height = (
                    self._release_time - self._time_when_played
                ) * self._scroll_speed
                if self.is_white:
                    self._surface = Surface((50, height))
                else:
                    self._surface = Surface((37.5, height))
                # calculate the color of the note bar based on the velocity
                self._surface.fill(store.COLOR_PALETTE["note_bar"])
                self._surface.set_alpha(self._velocity * 2)
                self._has_static_surface = True

        # render the note bar
        super().render(screen)

    @property
    def is_white(self):
        return self._note % 12 not in [1, 3, 6, 8, 10]

    @property
    def is_black(self):
        return self._note % 12 in [1, 3, 6, 8, 10]

    def scroll_horiz(self, amount):
        self._x += amount


class PianoKey(Renderable):
    """A piano key is a renderable that has a note associated with it."""

    _children: list[NoteBar]

    def __init__(self, note):
        self._note = note
        if self.is_white:
            self._surface = Surface((50, 230))
        else:
            self._surface = Surface((37.5, 142.5))
        # fill the surface with white or black, depending on the note
        if self.is_white:
            self._surface.fill(store.COLOR_PALETTE["light_key"])
        else:
            self._surface.fill(store.COLOR_PALETTE["dark_key"])
        offsets = [0, 0.625, 1, 1.625, 2, 3, 3.625, 4, 4.625, 5, 5.625, 6]
        super().__init__(
            floor(note / 12) * 350 + offsets[note % 12] * 50,
            -230,
            self._surface,
            0,
            1,
        )

    @property
    def is_white(self):
        return self._note % 12 not in [1, 3, 6, 8, 10]

    @property
    def is_black(self):
        return self._note % 12 in [1, 3, 6, 8, 10]

    def press(self, velocity=80):
        if self.is_white:
            self._surface.fill(store.COLOR_PALETTE["pressed_light_key"])
        else:
            self._surface.fill(store.COLOR_PALETTE["pressed_dark_key"])
        self.add_child(NoteBar(self._note, self._x, velocity))

    def release(self):
        if self.is_white:
            self._surface.fill(store.COLOR_PALETTE["light_key"])
        else:
            self._surface.fill(store.COLOR_PALETTE["dark_key"])
        self._children[-1].release()

    def scroll_horiz(self, amount):
        self._x += amount
        for child in self._children:
            child.scroll_horiz(amount)
