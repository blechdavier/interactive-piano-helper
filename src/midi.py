from math import floor
from queue import Queue
from time import sleep

from pygame import midi

import store


class MidiDeviceProcessor:

    _midi_input: midi.Input

    def __init__(self, event_queue: Queue):
        # initialize midi input
        midi.init()
        self._midi_input = None
        self._event_queue = event_queue
        self.find_device()
        if self._midi_input is None:
            return
        while True:
            sleep(0.01)
            if self._midi_input.poll():
                self._event_queue.put(self._midi_input.read(1))

    def find_device(self):
        in_id = midi.get_default_input_id()
        if in_id != -1:
            print("Found default midi input device")
            self._midi_input = midi.Input(in_id)
        else:
            print("No default midi input device found")
            self._midi_input = None


class Note:
    notes = [
        ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"],
        ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"],
    ]

    def __init__(self, note: int, velocity: int):
        if type(note) != int:
            raise TypeError("Note must be an integer")
        if note < 0 or note > 127:
            raise ValueError("Note must be between 0 and 127")
        if velocity < 0 or velocity > 127:
            raise ValueError("Velocity must be between 0 and 127")
        self._note = note
        self._velocity = velocity

    def __str__(self):
        return self.notes[int(store.app.composer.get_sharp_mode())][
            self._note % 12
        ] + str(floor(self._note / 12) - 1)

    @property
    def freq(self) -> float:
        # https://en.wikipedia.org/wiki/MIDI_tuning_standard
        return 440 * 2 ** ((float(self._note) - 69) / 12)

    @property
    def note(self):
        return self._note
