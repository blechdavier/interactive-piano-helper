import time
from abc import ABC, abstractmethod
from cmath import pi, sin
from random import random


class SynthVoice(ABC):
    """An abstract class that represents a synth voice. A synth voice is a single instrument that can play multiple notes at once. `get_summed_samples` returns the next samples for all the notes that are currently being played."""

    _notes: list

    def __init__(self):
        self._notes = []

    def play(self, note):
        self._notes.append(note)

    def release(self, note):
        self._notes.remove(note)

    @abstractmethod
    def get_next_samples(self, freq: float, sample_rate: int, length: int):
        return 0

    def get_summed_samples(self, sample_rate: int, length: int):
        samples = [0] * length
        for i in range(len(self._notes)):
            note_samples = self.get_next_samples(self._notes[i], sample_rate, length)
            for j in range(length):
                samples[j] += note_samples[j]
        return samples


class SineSynth(SynthVoice):
    def get_next_samples(self, freq: float, sample_rate: int, length: int):
        samples = [0] * length
        for i in range(length):
            samples[i] = sin(2 * pi * freq * i / sample_rate)
        return samples


class SquareSynth(SynthVoice):
    def get_next_samples(self, freq: float, sample_rate: int, length: int):
        samples = [0] * length
        for i in range(length):
            samples[i] = 1 if sin(2 * pi * freq * i / sample_rate) > 0 else -1
        return samples


class SawSynth(SynthVoice):
    def get_next_samples(self, freq: float, sample_rate: int, length: int):
        samples = [0] * length
        for i in range(length):
            samples[i] = 2 * (i / sample_rate * freq % 1) - 1
        return samples


class TriangleSynth(SynthVoice):
    def get_next_samples(self, freq: float, sample_rate: int, length: int):
        samples = [0] * length
        for i in range(length):
            samples[i] = 2 * abs(2 * (i / sample_rate * freq % 1) - 1) - 1
        return samples


class NoiseSynth(SynthVoice):
    def get_next_samples(self, freq: float, sample_rate: int, length: int):
        samples = [0] * length
        for i in range(length):
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
        for i in range(len(samples)):
            if samples[i] > self._threshold:
                samples[i] = (
                    self._threshold + (samples[i] - self._threshold) / self._ratio
                )


class AdsrEnvelope(Processor):
    """An envelope that can be used to control the gain of a synth voice. This is used for individual notes, not the synth voice as a whole."""

    def __init__(self, attack: float, decay: float, sustain: float, release: float):
        self._attack = attack
        self._decay = decay
        self._sustain = sustain
        self._release = release
        self._time = time.time()
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
            print("Note has been released for too long.")
            self._value = 0

    def release(self):
        self._released_time = time.time()

    def process(self, samples: list):
        return [sample * self._value for sample in samples]
