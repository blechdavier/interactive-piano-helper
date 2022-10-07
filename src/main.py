import pygame as pg
import midi


def main():
    pg.init()
    screen = pg.display.set_mode((800, 600), pg.HWSURFACE|pg.DOUBLEBUF|pg.RESIZABLE)
    pg.display.set_caption("Python Piano Helper")
    clock = pg.time.Clock()
    
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
        screen.fill((0, 255, 0))
        screen.blit(piano_surface, (0, screen.get_height()-230))
        # update the display
        pg.display.update()
        # limit the framerate to 60 fps
        clock.tick(60)
        # check for events
        for e in pg.event.get():
            if e.type == pg.KEYDOWN:
                if e.key == pg.K_ESCAPE:
                    running = False
            elif e.type == pg.VIDEORESIZE:
                screen = pg.display.set_mode(e.size, pg.HWSURFACE|pg.DOUBLEBUF|pg.RESIZABLE)
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