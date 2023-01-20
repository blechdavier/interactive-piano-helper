from pygame import MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, surface
from pygame.event import Event
from pygame.font import Font

from rendering import Renderable

import store


class UiBase(Renderable):
    def process_event(self, event: Event):
        pass


class UiText(UiBase):
    def __init__(
        self,
        x,
        y,
        sticky_x,
        sticky_y,
        text,
        font: str = "SofiaSans-Regular.ttf",
    ):
        # draw the text to a surface
        self._text = text
        self._font = font

        font = Font(f"assets/fonts/{font}", 24)

        self._surface = font.render(self._text, True, (0, 0, 0), (255, 255, 255))

        super().__init__(x, y, self._surface, sticky_x, sticky_y)

    def render(self, surface: surface.Surface):
        super().render(surface)

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        if self._text == value:  # don't bother rendering if the text hasn't changed
            return
        # update the text
        self._text = value
        font = Font(f"assets/fonts/{self._font}", 24)
        self._surface = font.render(self._text, True, (0, 0, 0), (255, 255, 255))


def default_callback():
    print("Button pressed")


class UiButton(UiText):
    def __init__(
        self,
        x,
        y,
        sticky_x,
        sticky_y,
        text,
        callback=default_callback,
        font: str = "SofiaSans-Regular.ttf",
    ):
        super().__init__(x, y, sticky_x, sticky_y, text, font)
        self._callback = callback

    def process_event(self, event: Event):
        if event.type == MOUSEBUTTONDOWN:
            if (
                event.pos[0] > self.screenspace_x
                and event.pos[0] < self.screenspace_x + self._surface.get_width()
                and event.pos[1] > self.screenspace_y
                and event.pos[1] < self.screenspace_y + self._surface.get_height()
            ):
                self._callback()

    @property
    def screenspace_x(self):
        return self.x + self.sticky_x * store.screen.get_width()

    @property
    def screenspace_y(self):
        return self.y + self.sticky_y * store.screen.get_height()
