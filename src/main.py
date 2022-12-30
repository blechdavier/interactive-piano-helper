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

from app import App


def main():
    # initialize screen
    screen = display.set_mode((800, 600), RESIZABLE | HWSURFACE | DOUBLEBUF)
    display.set_caption("Interactive Piano Helper")
    display.set_icon(image.load("assets/textures/icon.png"))
    fullscreen = False
    running = True
    # used to store previous window size when switching to fullscreen
    prev_size = (800, 600)
    # initialize app context
    app = App()
    # main loop
    while running:
        app.render(screen)
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
                    prev_size = screen.get_size()
                    screen = display.set_mode(
                        (0, 0), FULLSCREEN | HWSURFACE | DOUBLEBUF
                    )
                else:
                    screen = display.set_mode(
                        prev_size, RESIZABLE | HWSURFACE | DOUBLEBUF
                    )


if __name__ == "__main__":
    main()
