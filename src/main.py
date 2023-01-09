from pygame import (
    DOUBLEBUF,
    FULLSCREEN,
    HWSURFACE,
    K_F11,
    KEYDOWN,
    QUIT,
    RESIZABLE,
    display,
)
from pygame import event as ev
from pygame import image
from pygame.time import Clock

import store
from app import App


def main():
    # initialize screen
    store.screen = display.set_mode((800, 600), RESIZABLE | HWSURFACE | DOUBLEBUF)
    display.set_caption("Interactive Piano Helper")
    display.set_icon(image.load("assets/textures/icon.png"))
    fullscreen = False
    running = True
    # used to store previous window size when switching to fullscreen
    prev_size = (800, 600)
    # initialize app context
    app = App()
    # clock to limit framerate
    clock = Clock()
    # main loop
    while running:
        clock.tick(60)
        app.render(store.screen)
        display.flip()
        # process events
        for event in ev.get():
            if event.type == QUIT:
                running = False
            else:
                app.process_event(event)
            if event.type == KEYDOWN and event.key == K_F11:
                fullscreen = not fullscreen
                if fullscreen:
                    prev_size = store.screen.get_size()
                    store.screen = display.set_mode(
                        (0, 0), FULLSCREEN | HWSURFACE | DOUBLEBUF
                    )
                else:
                    store.screen = display.set_mode(
                        prev_size, RESIZABLE | HWSURFACE | DOUBLEBUF
                    )


if __name__ == "__main__":
    main()
