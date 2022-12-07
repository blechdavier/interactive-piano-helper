from pygame import (
    display,
    event as ev,
    QUIT,
    image,
    RESIZABLE,
    HWSURFACE,
    DOUBLEBUF,
    KEYDOWN,
    FULLSCREEN,
    K_F11,
)
from random import randint
from app import App


def main():
    # initialize screen
    screen = display.set_mode((800, 600), RESIZABLE | HWSURFACE | DOUBLEBUF)
    display.set_caption("Interactive Piano Helper")
    display.set_icon(image.load("assets/textures/icon.png"))
    fullscreen = False
    running = True
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
                    screen = display.set_mode(
                        (0, 0), FULLSCREEN | HWSURFACE | DOUBLEBUF
                    )
                else:
                    screen = display.set_mode(
                        (800, 600), RESIZABLE | HWSURFACE | DOUBLEBUF
                    )


if __name__ == "__main__":
    main()
