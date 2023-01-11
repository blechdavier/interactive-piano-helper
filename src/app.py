from abc import ABC, abstractmethod
from csv import reader
from math import floor
from os import path
from queue import Queue
from random import random
from threading import Thread, Timer, Event
from time import time

from pygame import K_LEFT, K_RIGHT, KEYDOWN, KEYUP, MOUSEWHEEL
from pygame import event as pygame_event

import store
from midi import MidiDeviceProcessor, Note
from rendering import PianoKey
from synth import (
    AudioManager,
    NoiseSynth,
    SineSynth,
    InstrumentAudio,
    SquareSynth,
    TriangleSynth,
)


class App:
    def __init__(self):
        self._piano = Piano(124)
        self._composing_context = ComposingContext()

    def render(self, screen):
        screen.fill(store.COLOR_PALETTE["background"])
        self._piano.render(screen)
        for particle in store.particles:
            particle.render(screen)

    def play(self, note):
        self._composing_context.play(note)
        self._piano.play(note)

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
    def composing_context(self):
        return self._composing_context


class Piano:
    """A piano is a collection of piano keys and a synthesizer."""

    def __init__(self, length: int):
        # initialize 88 piano keys
        self._keys: list[PianoKey] = []
        self._horizontal_scroll = 0.0
        for i in range(length):
            self._keys.append(PianoKey(i))
        self._instrument_audio = InstrumentAudio(SquareSynth, (0.1, 0.1, 0.5, 0.3))
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
        store.audio_manager.add_instrument_audio(self._instrument_audio)
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
            # this weird nested array datatype isn't my fault, blame pygame >:(((
            if event[0] == 144:
                self.play_from_midi(event[1], event[2])
            elif event[0] == 128:
                self.release_from_midi(event[1])

    def play_from_midi(self, note: int, velocity: int):
        self._keys[note].press(velocity)
        store.app.composing_context.add_note(note)
        note = Note(note, velocity)
        self._instrument_audio.play(note)

    def release_from_midi(self, note: int):
        self._keys[note].release()
        store.app.composing_context.remove_note(note)
        self._instrument_audio.release(note)

    def play_from_qwerty(self, key):
        if key in self._qwerty_to_midi:
            note: int = self._qwerty_to_midi[key]
            self._keys[note].press()
            store.app.composing_context.add_note(note)
            note: Note = Note(note, 80)
            self._instrument_audio.play(note)

    def release_from_qwerty(self, key):
        if key in self._qwerty_to_midi:
            note: int = self._qwerty_to_midi[key]
            self._keys[note].release()
            store.app.composing_context.remove_note(note)
            self._instrument_audio.release(note)

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


class ComposingContext:
    """A composing_context contains information about the music being played and methods for generating music."""

    def __init__(self):
        self._notes = []
        self._note_frequency = [0] * 12
        self._auto_instruments: list[AutoInstrument] = [
            AutoDrums(),
            AutoChords(),
            AutoBass(),
        ]
        self._bpm = 120
        self._last_tick = time()
        self._ticks = 0
        self._current_chord = 0

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

    def update(self):
        if (
            time() - self._last_tick > 60 / self._bpm / 4
        ):  # 4 ticks per beat (16th notes)
            self._last_tick = time()
            for instrument in self._auto_instruments:
                instrument.tick(self)
            self._ticks += 1

    # a bunch of utility functions for making new auto instrument logic
    @property
    def ticks(self) -> int:
        return self._ticks

    @property
    def beat_count(self) -> int:
        return self._ticks // 4

    @property
    def measure(self) -> int:
        return self._ticks // 16

    @property
    def beat_in_measure(self) -> int:
        return self._ticks % 16 // 4

    @property
    def tick_in_measure(self) -> int:
        return self._ticks % 16

    @property
    def current_chord(self) -> int:
        return self._current_chord

    @current_chord.setter
    def current_chord(self, value: int):
        self._current_chord = value


class AutoInstrument(ABC):
    _instrument_audio: InstrumentAudio

    @abstractmethod
    def tick(self, composing_context: ComposingContext):
        """This function is called every 16th note. It should play notes automatically in the instrument based on the composing_context."""
        raise NotImplementedError


class AutoDrums(AutoInstrument):
    def __init__(self):
        self._instrument_audio = InstrumentAudio(NoiseSynth, (0.01, 0.0, 1.0, 0.1))
        store.audio_manager.add_instrument_audio(self._instrument_audio)

    def tick(self, composing_context: ComposingContext):
        # play a snare every beat
        if composing_context.ticks % 4 == 0:
            self._instrument_audio.play(Note(60, 40))
            # make a timer to release the note
            Timer(0.02, self._instrument_audio.release, args=(60,)).start()
        # play a hat every 8th note and also sometimes on 16th notes randomly
        elif (
            composing_context.ticks % 2 == 0
            or random() < 0.5
            and composing_context.ticks % 4 != 0
        ):
            self._instrument_audio.play(Note(60, 20))
            Timer(0.05, self._instrument_audio.release, args=(60,)).start()


class AutoChords(AutoInstrument):
    def __init__(self):
        self._instrument_audio = InstrumentAudio(SineSynth, (0.1, 0.2, 0.9, 0.4))
        store.audio_manager.add_instrument_audio(self._instrument_audio)

    def tick(self, composing_context: ComposingContext):
        # every beat, play the chord that is most likely to be played
        if composing_context.ticks % 4 == 0:
            max_val = max(composing_context.chord_likelihood_table)
            # don't play anything before notes have been played
            if max_val == 0:
                return
            most_likely_chord = composing_context.chord_likelihood_table.index(max_val)
            # release all notes
            self._instrument_audio.release_all()
            # update the current chord
            composing_context.current_chord = most_likely_chord
            # play new notes
            self._instrument_audio.play(
                Note(60 + composing_context.key_notes[most_likely_chord], 127)
            )
            self._instrument_audio.play(
                Note(
                    60 + (composing_context.key_notes[(most_likely_chord + 2) % 7]), 80
                )
            )
            self._instrument_audio.play(
                Note(
                    60 + (composing_context.key_notes[(most_likely_chord + 4) % 7]), 80
                )
            )


class AutoBass(AutoInstrument):
    def __init__(self):
        self._instrument_audio = InstrumentAudio(SineSynth, (0.1, 0.2, 0.9, 0.4))
        store.audio_manager.add_instrument_audio(self._instrument_audio)

    def tick(self, composing_context: ComposingContext):
        # only play bass notes on beats

        if composing_context.ticks % 4 == 0:
            # if the chord is being played, play some bass
            max_val = max(composing_context.chord_likelihood_table)
            if max_val == 0:
                return
            # match the root note
            root_note = composing_context.current_chord
            # on the first beat of every measure, play the root note of the chord
            if composing_context.ticks % 16 == 0:

                root_note = composing_context.key_notes[root_note]
                # play the note two octaves lower
                self._instrument_audio.play(Note(60 - 24 + root_note, 127))
                Timer(
                    0.5, self._instrument_audio.release, args=(60 - 24 + root_note,)
                ).start()
            # on other beats, 50% chance to play any note from the chord
            elif random() > 0.5:
                if random() > 1 / 3:
                    note = composing_context.key_notes[root_note]
                elif random() > 1 / 2:
                    note = composing_context.key_notes[(root_note + 2) % 7]
                else:
                    note = composing_context.key_notes[(root_note + 4) % 7]

                # play the note two octaves lower
                self._instrument_audio.play(Note(60 - 24 + note, 127))
                Timer(
                    0.5, self._instrument_audio.release, args=(60 - 24 + note,)
                ).start()


class App:
    def __init__(self):
        self._piano = Piano(124)
        self._composing_context = ComposingContext()
        store.app = self

    def render(self, screen):
        screen.fill(store.COLOR_PALETTE["background"])
        self._piano.render(screen)
        for particle in store.particles:
            particle.render(screen)
        self._composing_context.update()

    def play(self, note):
        self._composing_context.play(note)
        self._piano.play(note)

    def process_event(self, event):
        if event.type == KEYDOWN:
            self._piano.play_from_qwerty(event.unicode.lower())
            if event.key == K_LEFT:
                self._piano.scroll_horiz(50)
            elif event.key == K_RIGHT:
                self._piano.scroll_horiz(-50)
        elif event.type == KEYUP:
            self._piano.release_from_qwerty(event.unicode.lower())
        elif event.type == MOUSEWHEEL:
            self._piano.scroll_horiz(event.x * -10)
        else:
            pass
            # print("Unhandled event: " + str(event))

    @property
    def composing_context(self) -> ComposingContext:
        return self._composing_context
