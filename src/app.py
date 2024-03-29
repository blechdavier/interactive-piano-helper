from abc import ABC, abstractmethod
from csv import reader
from math import floor
from os import path
from queue import Queue
from random import random
from threading import Event, Thread, Timer
from time import sleep, time

from pygame import K_LEFT, K_RIGHT, KEYDOWN, KEYUP, MOUSEWHEEL
from pygame import event as pygame_event

import store
from midi import MidiDeviceProcessor, Note
from rendering import NoteBar, PianoKey
from synth import AudioManager, InstrumentAudio, NoiseSynth, SineSynth, SquareSynth

from ui import UiBase, UiButton, UiText


class Piano:
    """A piano is a collection of piano keys and a synthesizer."""

    def __init__(self, length: int):
        # initialize 88 piano keys
        self._keys: list[PianoKey] = []
        self._note_bars = []
        self._horizontal_scroll = 0.0
        for i in range(length):
            self._keys.append(PianoKey(i))
        self._instrument_audio = InstrumentAudio(SquareSynth, (0.1, 0.1, 0.5, 0.3))

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
            self.scroll_x(-self._horizontal_scroll / 20)
        elif screen.get_width() - self.width - self._horizontal_scroll > 0:
            self.scroll_x(
                (screen.get_width() - self.width - self._horizontal_scroll) / 20
            )

        for note_bar in self._note_bars:
            note_bar.render(screen)
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
        # play a note if the midi note number is mapped to a key
        if note >= len(self._keys):
            return
        self._keys[note].press(velocity)
        store.app.composing_context.add_note(note)
        note = Note(note, velocity)
        self._instrument_audio.play(note)

    def release_from_midi(self, note: int):
        # release the note based on the midi note number
        if note >= len(self._keys):
            return
        self._keys[note].release()
        store.app.composing_context.remove_note(note)
        self._instrument_audio.release(note)

    def play_from_qwerty(self, key):
        # play a note if the key is mapped to a note
        if key not in self._qwerty_to_midi:
            return
        if self._qwerty_to_midi[key] >= len(self._keys):
            return
        note: int = self._qwerty_to_midi[key]
        self._keys[note].press()
        store.app.composing_context.add_note(note)
        note: Note = Note(note, 80)
        self._instrument_audio.play(note)

    def release_from_qwerty(self, key):
        # release the note based on your keyboard input
        if key not in self._qwerty_to_midi:
            return
        if self._qwerty_to_midi[key] >= len(self._keys):
            return
        note: int = self._qwerty_to_midi[key]
        self._keys[note].release()
        store.app.composing_context.remove_note(note)
        self._instrument_audio.release(note)

    def scroll_x(self, amount):
        self._horizontal_scroll += amount
        for key in self._keys:
            key.scroll_x(amount)
        for note_bar in self._note_bars:
            note_bar.scroll_x(amount)

    @property
    def width(self) -> float:
        return (
            floor(len(self._keys) / 12) * 7 * 50
            + [0, 50, 87.5, 100, 137.5, 150, 200, 237.5, 250, 287.5, 300, 337.5][
                len(self._keys) % 12
            ]
        )

    def add_note_bar(self, note: int, velocity: int, instrument: str):
        offsets = [0, 0.625, 1, 1.625, 2, 3, 3.625, 4, 4.625, 5, 5.625, 6]
        x = self._horizontal_scroll + offsets[note % 12] * 50 + floor(note / 12) * 350
        self._note_bars.append(NoteBar(note, x, velocity, instrument))

    def release_note_bar(self, note: int, instrument: str):
        # release the note bar that is playing the note and instrument
        for note_bar in self._note_bars:
            if (
                note_bar.note == note
                and note_bar.instrument == instrument
                and not note_bar.released
            ):
                note_bar.release()
                break

    def release_all_note_bars(self, instrument: str):
        # release all the note bars that are playing the instrument
        for note_bar in self._note_bars:
            if note_bar.instrument == instrument:
                note_bar.release()


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
        # add this note to the list of the notes that are currently being played
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
        key_sig_text = f"We think you're playing in {['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G','G#', 'A', 'A#', 'B'][key_sig[0]]} {key_sig[1]}"
        store.app.ui[0].text = key_sig_text
        return key_sig

    def update(self):
        if (
            time() - self._last_tick > 60 / self._bpm / 4
        ):  # 4 ticks per beat (16th notes)
            self._last_tick = time()
            for instrument in self._auto_instruments:
                instrument.tick(self)
            self._ticks += 1

    def change_bpm(self, value: int):
        self._bpm += value
        store.app.ui[3].text = f"BPM: {self._bpm}"

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
            self._instrument_audio.play(Note(12, 40))
            store.app.piano.add_note_bar(12, 40, "drums")
            # make a timer to release the note
            Timer(0.02, self._instrument_audio.release, args=(12,)).start()
            Timer(0.02, store.app.piano.release_note_bar, args=(12, "drums")).start()
        # play a hat every 8th note and also sometimes on 16th notes randomly
        elif (
            composing_context.ticks % 2 == 0
            or random() < 0.5
            and composing_context.ticks % 4 != 0
        ):
            self._instrument_audio.play(Note(13, 20))
            store.app.piano.add_note_bar(13, 20, "drums")
            Timer(0.05, self._instrument_audio.release, args=(13,)).start()
            Timer(0.05, store.app.piano.release_note_bar, args=(13, "drums")).start()


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
            # release all notes
            self._instrument_audio.release_all()
            store.app.piano.release_all_note_bars("chords")
            most_likely_chord = composing_context.chord_likelihood_table.index(max_val)
            # update the current chord
            composing_context.current_chord = most_likely_chord
            # play new notes
            self._instrument_audio.play(
                Note(60 + composing_context.key_notes[most_likely_chord], 80)
            )
            store.app.piano.add_note_bar(
                60 + composing_context.key_notes[most_likely_chord], 80, "chords"
            )
            self._instrument_audio.play(
                Note(
                    60 + (composing_context.key_notes[(most_likely_chord + 2) % 7]), 60
                )
            )
            store.app.piano.add_note_bar(
                60 + (composing_context.key_notes[(most_likely_chord + 2) % 7]),
                60,
                "chords",
            )
            self._instrument_audio.play(
                Note(
                    60 + (composing_context.key_notes[(most_likely_chord + 4) % 7]), 55
                )
            )
            store.app.piano.add_note_bar(
                60 + (composing_context.key_notes[(most_likely_chord + 4) % 7]),
                55,
                "chords",
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
                store.app.piano.add_note_bar(60 - 24 + root_note, 127, "bass")
                Timer(
                    0.5, self._instrument_audio.release, args=(60 - 24 + root_note,)
                ).start()
                Timer(
                    0.5,
                    store.app.piano.release_note_bar,
                    args=(60 - 24 + root_note, "bass"),
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
                store.app.piano.add_note_bar(60 - 24 + note, 127, "bass")
                Timer(
                    0.5, self._instrument_audio.release, args=(60 - 24 + note,)
                ).start()
                Timer(
                    0.5, store.app.piano.release_note_bar, args=(60 - 24 + note, "bass")
                ).start()


class App:
    def __init__(self):
        # create a new AudioManager to deal with sound processing if it doesn't already exist and a new thread to calculate audio samples
        if store.audio_manager is None:
            store.audio_manager = AudioManager()
        self._piano = Piano(88)
        self._composing_context = ComposingContext()
        store.app = self
        store.audio_manager.start()
        self._ui = [
            UiText(
                0, 0, 0, 0, "Press any key to start composing"
            ),  # Displays the key signature after the user has pressed a key
            UiButton(
                0, -300, 0, 1, "<-", lambda: self._piano.scroll_x(50)
            ),  # Scroll the piano left
            UiButton(
                -25, -300, 1, 1, "->", lambda: self._piano.scroll_x(-50)
            ),  # Scroll the piano right
            UiText(
                0, 25, 0, 0, f"BPM: {self.composing_context._bpm}"
            ),  # Displays the BPM
            UiButton(
                0, 50, 0, 0, "BPM +", lambda: self._composing_context.change_bpm(1)
            ),  # Increase the BPM
            UiButton(
                0, 75, 0, 0, "BPM -", lambda: self._composing_context.change_bpm(-1)
            ),  # Decrease the BPM
        ]

    def render(self, screen):
        screen.fill(store.COLOR_PALETTE["background"])
        # render the piano and particles
        self._piano.render(screen)
        for particle in store.particles:
            particle.render(screen)
        # render the ui
        for ui_element in self._ui:
            ui_element.render(screen)
        # update the composing context (the only reason this is in the render function is because it needs to be called every frame)
        self._composing_context.update()

    def play(self, note):
        self._composing_context.play(note)
        self._piano.play(note)

    def process_event(self, event):
        for ui_element in self._ui:
            ui_element.process_event(event)
        if event.type == KEYDOWN:
            self._piano.play_from_qwerty(event.unicode.lower())
            if event.key == K_LEFT:
                self._piano.scroll_x(50)
            elif event.key == K_RIGHT:
                self._piano.scroll_x(-50)
        elif event.type == KEYUP:
            self._piano.release_from_qwerty(event.unicode.lower())
        elif event.type == MOUSEWHEEL:
            self._piano.scroll_x(event.x * -10)
        else:
            pass
            # print("Unhandled event: " + str(event))

    @property
    def composing_context(self) -> ComposingContext:
        return self._composing_context

    @property
    def ui(self):
        return self._ui

    @property
    def piano(self):
        return self._piano
