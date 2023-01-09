from abc import ABC, abstractmethod
from math import pi, sin
from queue import Queue
from random import random
from time import perf_counter, time

import numpy as np
import pyaudio

from midi import Note


class SynthVoice(ABC):
    """An abstract class that represents a synth voice. A synth voice is a single instrument that can play multiple notes at once. `get_summed_samples` returns the next samples for all the notes that are currently being played."""

    _freq: float = 0
    _sample_rate: int
    _sample_length: int

    def __init__(self, sample_rate: int = 44100, sample_length: int = 256):
        self._sample_rate = sample_rate
        self._sample_length = sample_length
        self._phase = 0

    def play(self, note: int or Note):
        if note is int:
            note = Note(note, 0)
        # make a temporary instance of the note class to calculate the pitch of the note
        self._freq = note.freq

    @abstractmethod
    def get_next_samples(self):
        return np.array(0 in range(100))


class SineSynth(SynthVoice):
    def get_next_samples(self):
        samples = [
            sin(2 * pi * self._freq * (i + self._phase) / self._sample_rate)
            for i in range(self._sample_length)
        ]
        self._phase += self._sample_length
        return samples


class SquareSynth(SynthVoice):
    def get_next_samples(self):
        samples = [0] * self._sample_length
        for i in range(self._sample_length):
            samples[i] = (
                1 if sin(2 * pi * self._freq * i / self._sample_rate) > 0 else -1
            )
        return samples


class SawSynth(SynthVoice):
    def get_next_samples(self):
        samples = [0] * self._sample_length
        for i in range(self._sample_length):
            samples[i] = 2 * (i / self._sample_rate * self._freq % 1) - 1
        return samples


class TriangleSynth(SynthVoice):
    def get_next_samples(self):
        samples = [0] * self._sample_length
        for i in range(self._sample_length):
            samples[i] = 2 * abs(2 * (i / self._sample_rate * self._freq % 1) - 1) - 1
        return samples


class NoiseSynth(SynthVoice):
    def get_next_samples(self):
        samples = [0] * self._sample_length
        for i in range(self._sample_length):
            samples[i] = random()
        return samples


class Processor(ABC):
    @abstractmethod
    def process(self, samples: list):
        return samples


class Gain(Processor):
    """A processor that multiplies the samples by a given gain."""

    def __init__(self, gain: float):
        self._gain = gain

    def process(self, samples: list):
        for i in range(len(samples)):
            samples[i] *= self._gain


class Compressor(Processor):
    """This might not be how a compressor actually works; I'm not sure if the negative sample values work how they should honestly."""

    def __init__(self, threshold: float, ratio: float):
        self._threshold = threshold
        self._ratio = ratio

    def process(self, samples: list):
        for sample in samples:
            if abs(sample) > self._threshold:
                sample = (
                    sample
                    / abs(sample)
                    * (self._threshold + (abs(sample) - self._threshold) / self._ratio)
                )


class AdsrEnvelope(Processor):
    """An envelope that can be used to control the gain of a synth voice. This is used for individual notes, not the synth voice as a whole."""

    def __init__(self, attack: float, decay: float, sustain: float, release: float):
        self._attack = attack
        self._decay = decay
        self._sustain = sustain
        self._release = release
        self._time = time()
        self._released_time = None
        self._value = 0

    def update_value(self):
        if time() - self._time < self._attack:
            self._value = (time() - self._time) / self._attack
        elif time() - self._time < self._attack + self._decay:
            self._value = 1 - (time() - self._time - self._attack) / self._decay * (
                1 - self._sustain
            )
        elif self._released_time is None:
            self._value = self._sustain
        elif time() - self._released_time < self._release:
            self._value = (
                self._sustain
                - (time() - self._released_time) / self._release * self._sustain
            )
        else:
            self._value = 0

    def release(self):
        self._released_time = time()

    def process(self, samples: list):
        return [sample * self._value for sample in samples]

    @property
    def is_dead(self):
        return (
            self._released_time is not None
            and time() - self._released_time > self._release
        )


class SynthManager:
    """A class that manages all the notes for a synth voice. This is semi-analogous to an instrument in a DAW."""

    # FIXME this datatype isn't very OOP of me
    _notes: list[(Note, SynthVoice, AdsrEnvelope)]

    def __init__(self):
        self._notes = []
        self._press_queue = Queue()
        self._release_queue = Queue()

    def play(self, note: Note):
        self._press_queue.put(note)

    def release(self, note: Note or int):
        """Take in either a `Note` object or a midi key number."""
        if type(note) == Note:
            note = Note.note
        self._release_queue.put(note)

    def get_next_samples(self, sample_rate: int, length: int):
        while self._press_queue.qsize():
            note = self._press_queue.get()
            self._notes.append((note, SineSynth(), AdsrEnvelope(0.1, 0.1, 0.5, 0.1)))
            self._notes[-1][1].play(note)

        while self._release_queue.qsize():
            note = self._release_queue.get()
            for i in range(len(self._notes)):
                if self._notes[i][0].note == note:
                    self._notes[i][2].release()
                    break

        for i in range(len(self._notes)):
            self._notes[i][2].update_value()
            if self._notes[i][2].is_dead:
                self._notes.pop(i)
                # this is a bit of a hack, but it work for now
                break
        samples = [0] * length
        for i in range(len(self._notes)):
            self._notes[i][2].update_value()
            note_samples = self._notes[i][1].get_next_samples()
            note_samples = self._notes[i][2].process(note_samples)
            # this is a goofy way to add two arrays, there's probably a better way
            samples = [samples[i] + note_samples[i] for i in range(length)]

        return samples


class AudioManager:
    def __init__(self):
        self._sample_rate = 44100
        self._length = 256
        self._synth_managers = []
        self._compressor = Compressor(0.5, 2)
        self._p = pyaudio.PyAudio()
        self._stream = self._p.open(
            output=True, format=pyaudio.paFloat32, channels=1, rate=self._sample_rate
        )

    def add_synth_manager(self, synth_manager: SynthManager):
        self._synth_managers.append(synth_manager)

    def get_next_samples(self):
        samples = [0] * self._length
        for synth in self._synth_managers:
            synth_samples = synth.get_next_samples(self._sample_rate, self._length)
            samples = [samples[i] + synth_samples[i] for i in range(self._length)]
        return samples

    def start(self):
        while True:
            # c = perf_counter()
            self._stream.write(np.float32(self.get_next_samples()).tobytes())
