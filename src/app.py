from dev import todo
from rendering import PianoKey
from synth import SquareSynth
from pygame import KEYDOWN
from csv import reader
from os import path


class App:
    def __init__(self):
        self._piano = Piano(SquareSynth())
        self._composer = Composer()

    def render(self, screen):
        self._piano.render(screen)

    def play(self, note):
        self._composer.play(note)
        self._piano.play(note)

    def start_audio(self):
        todo()

    def process_event(self, event):
        if event.type == KEYDOWN:
            self._piano.play_from_qwerty(event.unicode)


class Piano:
    """A piano is a collection of piano keys and a synthesizer."""

    def __init__(self, synthesizer):
        # initialize 88 piano keys
        self._keys = []
        for i in range(88):
            self._keys.append(PianoKey(i))
        self._synthesizer = synthesizer
        # load dictionary from file
        # this is later used to map qwerty keys to notes
        with open(
            path.join(path.dirname(path.abspath(__file__)), "./qwerty_to_midi.csv"),
            mode="r",
        ) as f:
            r = reader(f)
            self._qwerty_to_midi = {rows[0]: rows[1] for rows in r}
            print(self._qwerty_to_midi)

    def render(self, screen):
        # not optimized but keeps the code simple
        for key in self._keys:
            if key.is_white():
                key.render(screen)
        for key in self._keys:
            if key.is_black():
                key.render(screen)

    def play(self, note):
        self._synthesizer.play(note)

    def play_from_qwerty(self, key):
        self._synthesizer.play(self._qwerty_to_midi[key])


class Composer:
    """A composer contains information about the music being played and methods for composing music."""

    def __init__(self):
        self._notes = []
        self._key_signature = KeySignature()

    def add_note(self, note):
        self._key_signature.add_note(note)
        self._notes.append(note)


class KeySignature:
    def __init__(self):
        self._note_frequencies = [0] * 12

    def add_note(self, note):
        # old notes matter less
        for note in self._note_frequencies:
            note *= 0.9
        # new notes matter more
        self._note_frequencies[note % 12] += 1

    def get_key(self) -> tuple[int, str]:
        key_sig = (0, "major")

        # loop through major keys and find the maximum weight for each key based on the notes played
        max_weight = 0
        for i in range(12):
            weight = (
                [0, 2, 4, 5, 7, 9, 11]
                .map(lambda x: self._note_frequencies[(x + i) % 12])
                .sum()
            )
            if weight > max_weight:
                max_weight = weight
                key_sig = (i, "major")

        # TODO: minor keys

        return key_sig
