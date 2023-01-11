from csv import reader
from math import floor
from os import path
from queue import Queue
from threading import Thread

from pygame import K_LEFT, K_RIGHT, KEYDOWN, KEYUP, MOUSEWHEEL
from pygame import event as pygame_event

import store
from dev import todo
from midi import MidiDeviceProcessor, Note
from rendering import PianoKey
from synth import AudioManager, SynthManager


class App:
    def __init__(self):
        self._piano = Piano(124)
        self._composer = Composer()

    def render(self, screen):
        screen.fill(store.COLOR_PALETTE["background"])
        self._piano.render(screen)
        for particle in store.particles:
            particle.render(screen)

    def play(self, note):
        self._composer.play(note)
        self._piano.play(note)

    def start_audio(self):
        todo()

    def process_event(self, event: pygame_event):
        print(event)
        if event.type == KEYDOWN:
            self._piano.play_from_qwerty(event.unicode.lower())
            if event.key == K_RIGHT:
                self._piano.scroll_horiz(50)
            elif event.key == K_LEFT:
                self._piano.scroll_horiz(-50)
        elif event.type == KEYUP:
            self._piano.release_from_qwerty(event.unicode.lower())
        elif event.type == MOUSEWHEEL:
            self._piano.scroll_horiz(event.x * -10)
        else:
            pass
            # print("Unhandled event: " + str(event))

    @property
    def composer(self):
        return self._composer


class Piano:
    """A piano is a collection of piano keys and a synthesizer."""

    def __init__(self, length: int):
        # initialize 88 piano keys
        self._keys: list[PianoKey] = []
        self._horizontal_scroll = 0.0
        for i in range(length):
            self._keys.append(PianoKey(i))
        self._synth_manager = SynthManager()
        # create a new AudioManager to deal with sound processing if it doesn't already exist and a new thread to calculate audio samples
        if store.audio_manager is None:
            store.audio_manager = AudioManager()
        if store.audio_thread is None:
            print("Starting audio thread")
            store.audio_thread = Thread(
                target=store.audio_manager.start,
                name="AudioThread",
                daemon=True,
            )
            store.audio_thread.start()

        # add the synth manager to the audio manager
        store.audio_manager.add_synth_manager(self._synth_manager)
        # load dictionary from file
        # this is later used to map qwerty keys to notes
        with open(
            path.join(path.dirname(path.abspath(__file__)), "./qwerty_to_midi.csv"),
            mode="r",
        ) as f:
            r = reader(f)
            self._qwerty_to_midi = {rows[0]: int(rows[1]) for rows in r}
        # poll for midi events on a separate thread and place them in a queue to process them on the main thread
        # apparently queues are thread safe src=https://www.geeksforgeeks.org/python-communicating-between-threads-set-1/
        self._midi_event_queue = Queue()
        Thread(
            target=MidiDeviceProcessor,
            args=(self._midi_event_queue,),
            name="MidiProcessorThread",
            daemon=True,
        ).start()

    def __str__(self):
        return len(self._keys) + " Key Piano"

    def render(self, screen):
        # process midi events on the main thread
        self.process_midi_events()
        # update horizontal position before rendering
        if self._horizontal_scroll > 0:
            self.scroll_horiz(-self._horizontal_scroll / 20)
        elif screen.get_width() - self.width - self._horizontal_scroll > 0:
            self.scroll_horiz(
                (screen.get_width() - self.width - self._horizontal_scroll) / 20
            )
        # not optimized but keeps the code simple so its fine
        for key in self._keys:
            if key.is_white:
                key.render(screen)
        for key in self._keys:
            if key.is_black:
                key.render(screen)

    def process_midi_events(self):
        while not self._midi_event_queue.empty():
            event = self._midi_event_queue.get()
            event = event[0][0]
            # this goofy datatype isn't my fault
            if event[0] == 144:
                self.play_from_midi(event[1], event[2])
            elif event[0] == 128:
                self.release_from_midi(event[1])

    def play_from_midi(self, note: int, velocity: int):
        self._keys[note].press(velocity)
        store.app.composer.add_note(note)
        note = Note(note, velocity)
        self._synth_manager.play(note)

    def release_from_midi(self, note: int):
        self._keys[note].release()
        store.app.composer.remove_note(note)
        self._synth_manager.release(note)

    def play_from_qwerty(self, key):
        if key in self._qwerty_to_midi:
            note: int = self._qwerty_to_midi[key]
            self._keys[note].press()
            store.app.composer.add_note(note)
            note: Note = Note(note, 80)
            self._synth_manager.play(note)

    def release_from_qwerty(self, key):
        # self._synthesizer.release(self._qwerty_to_midi[key])
        if key in self._qwerty_to_midi:
            note: int = self._qwerty_to_midi[key]
            self._keys[note].release()
            store.app.composer.remove_note(note)
            self._synth_manager.release(note)

    def scroll_horiz(self, amount):
        self._horizontal_scroll += amount
        for key in self._keys:
            key.scroll_horiz(amount)

    @property
    def width(self) -> float:
        return (
            floor(len(self._keys) / 12) * 7 * 50
            + [0, 50, 87.5, 100, 137.5, 150, 200, 237.5, 250, 287.5, 300, 337.5][
                len(self._keys) % 12
            ]
        )


class Composer:
    """A composer contains information about the music being played and methods for generating music."""

    def __init__(self):
        self._notes = []
        self._note_frequency = [0] * 12

    def add_note(self, note: int):
        # add this not to the list of the notes that are currently being played
        self._notes.append(note)

        # update the note frequency list
        # new notes matter more
        self._note_frequency[note % 12] += 1
        # old notes matter less
        for i in range(12):
            self._note_frequency[i] *= 0.9
        # print(self.chord_likelihood_table)

    def remove_note(self, note: int):
        self._notes.remove(note)

    @property
    def chord_likelihood_table(self) -> list[int]:
        """A table of the likelihood of a chord being played based on the notes that have been played recently."""
        output = [0] * 7

        def chord_likelihood(chord: list[int]) -> float:
            # the likelihood of a chord is the sum of the likelihood of each note in the chord
            return sum([self._note_frequency[note % 12] for note in chord])

        for i in range(len(self.key_notes)):
            # check the root, third, and fifth for each chord
            output[i] = chord_likelihood(
                [
                    self.key_notes[i],
                    self.key_notes[(i + 2) % 7],
                    self.key_notes[(i + 4) % 7],
                ]
            )
        return output

    # returns the notes in the key signature
    @property
    def key_notes(self) -> list[int]:
        return [x + self.key_sig[0] for x in [0, 2, 4, 5, 7, 9, 11]]

    @property
    def key_sig(self) -> tuple[int, str]:
        key_sig = (0, "major")

        # loop through major keys and find the maximum weight for each key based on the notes played
        max_weight = 0
        for i in range(12):
            weight = sum(
                [self._note_frequency[(i + x) % 12] for x in [0, 2, 4, 5, 7, 9, 11]]
            )
            if weight > max_weight:
                max_weight = weight
                key_sig = (i, "major")
        # print(f"You're playing in {key_sig[0]} {key_sig[1]}")
        return key_sig


class App:
    def __init__(self):
        self._piano = Piano(124)
        self._composer = Composer()
        store.app = self

    def render(self, screen):
        screen.fill(store.COLOR_PALETTE["background"])
        self._piano.render(screen)
        for particle in store.particles:
            particle.render(screen)

    def play(self, note):
        self._composer.play(note)
        self._piano.play(note)

    def start_audio(self):
        todo()

    def process_event(self, event):
        if event.type == KEYDOWN:
            self._piano.play_from_qwerty(event.unicode.lower())
            if event.key == K_RIGHT:
                self._piano.scroll_horiz(50)
            elif event.key == K_LEFT:
                self._piano.scroll_horiz(-50)
        elif event.type == KEYUP:
            self._piano.release_from_qwerty(event.unicode.lower())
        elif event.type == MOUSEWHEEL:
            self._piano.scroll_horiz(event.x * -10)
        else:
            pass
            # print("Unhandled event: " + str(event))

    @property
    def composer(self) -> Composer:
        return self._composer
