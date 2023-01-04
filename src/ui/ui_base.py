from pygame import MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, surface
from pygame.event import Event
from pygame.font import Font

from ..rendering import Renderable


class UiBase(Renderable):
    pass


class UiButton(UiBase):
    def __init__(
        self,
        x,
        y,
        sticky_x,
        sticky_y,
        width,
        height,
        text,
        callback,
        font: str = "Arial",
    ):
        self._width = width
        self._height = height
        self._text = text
        self._callback = callback
        self._surface = surface.Surface((width, height))
        self._surface.fill((255, 0, 255))

        font = Font(font, 24)

        text = font.render(self._text, True, (0, 0, 0), (255, 255, 255))
        if text.get_width() > width:
            font = Font(font, 24 * width / text.get_width())
            text = font.render(self._text, True, (0, 0, 0), (255, 255, 255))

        self._surface.blit(
            text, (width / 2 - text.get_width() / 2, height / 2 - text.get_height() / 2)
        )

        super().__init__(x, y, self._surface, sticky_x, sticky_y)

    def process_event(self, event: Event):
        if event.type == MOUSEBUTTONDOWN:
            if (
                event.pos[0] > self.x
                and event.pos[0] < self.x + self._width
                and event.pos[1] > self.y
                and event.pos[1] < self.y + self._height
            ):
                self._callback()
