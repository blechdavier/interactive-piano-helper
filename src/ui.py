from pygame import MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, surface
from pygame.event import Event
from pygame.font import Font

from rendering import Renderable

import store


class UiBase(Renderable):
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
        self._text = text
        self._surface = surface.Surface((1, 1))
        self._surface.fill((255, 0, 255))

        font = Font(f"assets/fonts/{font}", 24)

        text_surface = font.render(self._text, True, (0, 0, 0), (255, 255, 255))

        self._surface = surface.Surface((text_surface.get_width(), text_surface.get_height()))
        self._surface.fill((255, 0, 255))
        self._surface.blit(text_surface, (0, 0))

        super().__init__(x, y, self._surface, sticky_x, sticky_y)
        
    def render(self, surface: surface.Surface):
        super().render(surface)
        
        
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
        callback = default_callback,
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