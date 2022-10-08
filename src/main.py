import pygame as pg
import midi
import keyboard


def main():
    pg.init()
    screen = pg.display.set_mode((2000, 600), pg.HWSURFACE | pg.DOUBLEBUF | pg.RESIZABLE)
    pg.display.set_caption("Python Piano Helper")
    clock = pg.time.Clock()

    # load assets
    shadow = pg.image.load("assets/textures/shadow.png")

    # Create a container for the white keys
    white_key_container = pg.sprite.Group()
    # Create a container for the black keys
    black_key_container = pg.sprite.Group()

    # Create a list of all the keys
    keys = []
    for key_id in range(128):
        keys.append(midi.MidiKey(key_id, white_key_container, black_key_container))

    # create a surface to draw all the piano keys on
    piano_surface = pg.Surface((screen.get_width(), 350))
    # draw the white keys onto the surface
    white_key_container.draw(piano_surface)
    # draw the black keys onto the surface
    black_key_container.draw(piano_surface)

    running = True
    while running:
        # wipe the screen
        screen.fill((251, 251, 251))
        # this could be optimized further
        white_key_container.draw(piano_surface)
        black_key_container.draw(piano_surface)
        screen.blit(piano_surface, (0, screen.get_height() - 230))
        screen.blit(pg.transform.scale(shadow, (screen.get_width(), 6)), (0, screen.get_height() - 236))
        # update the display
        pg.display.update()
        # limit the framerate to 60 fps
        clock.tick(60)
        # check for events
        for e in pg.event.get():
            if e.type == pg.KEYDOWN:
                if e.key == pg.K_ESCAPE:
                    running = False
                elif e.key == pg.K_F11:
                    # bad code but it's python so whatever
                    if screen.get_flags() & pg.FULLSCREEN == 0:
                        print("not fullscreen")
                        old_res = (screen.get_width(), screen.get_height())
                        screen = pg.display.set_mode((0, 0), pg.FULLSCREEN
                                                     | pg.HWSURFACE | pg.DOUBLEBUF | pg.RESIZABLE)
                    else:
                        print("fullscreen")
                        screen = pg.display.set_mode(old_res, pg.HWSURFACE | pg.DOUBLEBUF | pg.RESIZABLE)
                    piano_surface = pg.Surface((screen.get_width(), 350))
                    white_key_container.draw(piano_surface)
                    black_key_container.draw(piano_surface)
                    print(old_res)
                else:
                    if pg.key.name(e.key) in keyboard.keys_to_midi:
                        print(pg.key.name(e.key) + " down")
                        key_id = keyboard.keys_to_midi[pg.key.name(e.key)]
                        keys[key_id].update_visuals(True)
            elif e.type == pg.KEYUP:
                if pg.key.name(e.key) in keyboard.keys_to_midi:
                    print(pg.key.name(e.key) + " up")
                    key_id = keyboard.keys_to_midi[pg.key.name(e.key)]
                    keys[key_id].update_visuals(False)
            elif e.type == pg.VIDEORESIZE:
                if screen.get_flags() & pg.FULLSCREEN == 0:
                    screen = pg.display.set_mode(e.size, pg.HWSURFACE | pg.DOUBLEBUF | pg.RESIZABLE)
                    # recreate the surface and redraw the keys
                    piano_surface = pg.Surface((screen.get_width(), 350))
                    white_key_container.draw(piano_surface)
                    black_key_container.draw(piano_surface)
            elif e.type == pg.QUIT:
                running = False
                pg.quit()
                quit()


if __name__ == "__main__":
    main()
