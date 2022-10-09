import pygame as pg
import midi
import keyboard
import synth
import time
import daemon
import threading
import autoplay

def main():
    previous_notes = []

    bpm = 103

    pg.init()
    screen = pg.display.set_mode((2000, 600), pg.HWSURFACE | pg.DOUBLEBUF | pg.RESIZABLE)
    pg.display.set_caption("Python Piano Helper")
    clock = pg.time.Clock()

    # load assets
    shadow = pg.image.load("assets/textures/shadow.png").convert_alpha()
    display_font = pg.font.Font("assets/fonts/Shrikhand-Regular.ttf", 64)
    text_surface_obj = display_font.render(
        "", True, (0, 0, 0))

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

    # create a dictionary of all the notes that are currently being played
    notes_dict = {}

    # generate a list of all the key signatures
    key_signature_table = autoplay.get_key_signature_table()

    # create a lock for the notes_dict
    lock = threading.Lock()

    # create a thread for the daemon function
    thread = threading.Thread(target=daemon.daemon_function, args=(lock, notes_dict,), name="daemon_function")
    thread.start()

    start_time = time.time()

    running = True
    while running:
        # wipe the screen
        background_brightness = 251 - (int((start_time - time.time()) / 60 * bpm * 10) % 10)
        screen.fill((background_brightness, background_brightness, background_brightness))
        for i in range(int((start_time - time.time()) / 60 * bpm * 50) % 50, screen.get_height()-214, 50):
            screen.blit(pg.transform.scale(shadow, (screen.get_width(), 6 + (int((start_time - time.time()) / 60 * bpm * 50) % 50) / 5)), (0, i-(int((start_time - time.time()) / 60 * bpm * 50) % 50) / 5))
        # this could be optimized further
        white_key_container.draw(piano_surface)
        black_key_container.draw(piano_surface)
        screen.blit(piano_surface, (0, screen.get_height() - 230))
        screen.blit(pg.transform.scale(shadow, (screen.get_width(), 8)), (0, screen.get_height() - 238))
        screen.blit(text_surface_obj, (screen.get_width() - text_surface_obj.get_width() - 10, 10))
        # update the display
        pg.display.update()
        # limit the framerate to 60 fps
        clock.tick(60)
        # check for events
        for e in pg.event.get():
            if e.type == pg.KEYDOWN:
                if e.key == pg.K_ESCAPE:
                    running = False
                    pg.quit()
                    quit()
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
                        # print(pg.key.name(e.key) + " down")
                        key_id = keyboard.keys_to_midi[pg.key.name(e.key)]
                        keys[key_id].update_visuals(True)
                        notes_dict[key_id] = synth.get_sin_oscillator(keys[key_id].pitch, amp=0.1)
                        previous_notes.append(key_id)
                        text_surface_obj = display_font.render(["C major", "C# major", "D major", "D# major", "E major", "F major", "F# major", "G major", "G# major", "A major", "A# major", "B major", "C minor", "C# minor", "D minor", "D# minor", "E minor", "F minor", "F# minor", "G minor", "G# minor", "A minor", "A# minor", "B minor"][autoplay.find_key_signature(previous_notes, key_signature_table)], True, (0, 0, 0))
            elif e.type == pg.KEYUP:
                if pg.key.name(e.key) in keyboard.keys_to_midi:
                    # print(pg.key.name(e.key) + " up")
                    key_id = keyboard.keys_to_midi[pg.key.name(e.key)]
                    keys[key_id].update_visuals(False)
                    notes_dict.pop(key_id)
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
