from abc import ABC, abstractmethod
from math import pi, sin
from queue import Queue
from random import random

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

    def play(self, note: int or Note or float):
        # if the note is an integer, convert it to a Note object
        if note is int:
            note = Note(note, 0)
        # make a temporary instance of the note class to calculate the pitch of the note
        self._freq = note.freq

    @abstractmethod
    def get_next_samples(self, length) -> list[float]:
        return [0.0 in range(length)]


class SineSynth(SynthVoice):
    def get_next_samples(self, length):
        samples = [
            sin(2 * pi * self._freq * (i + self._phase) / self._sample_rate)
            for i in range(length)
        ]
        self._phase += length
        return samples


class SquareSynth(SynthVoice):
    def get_next_samples(self, length):
        samples = [
            1
            if sin(2 * pi * self._freq * (i + self._phase) / self._sample_rate) > 0
            else -1
            for i in range(length)
        ]
        self._phase += length
        return samples


class SawSynth(SynthVoice):
    def get_next_samples(self, length):
        samples = [
            2 * (self._freq * (i + self._phase) / self._sample_rate % 1 - 0.5)
            for i in range(length)
        ]
        self._phase += length
        return samples


class TriangleSynth(SynthVoice):
    def get_next_samples(self, length):
        samples = [
            2 * abs(self._freq * (i + self._phase) / self._sample_rate % 1 - 0.5) - 1
            for i in range(length)
        ]
        self._phase += length
        return samples


class NoiseSynth(SynthVoice):
    def get_next_samples(self, length):
        samples = [random() * 2 - 1 for i in range(length)]
        self._phase += length
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
    """Makes loud sounds quieter above a certain threshold."""

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
        return samples


class AdsrEnvelope(Processor):
    """An envelope that can be used to control the gain of a synth voice. This is used for individual notes, not the synth voice as a whole. [Read more about this.](https://en.wikipedia.org/wiki/Envelope_(music)#ADSR)"""

    _sample_rate = 44100

    def __init__(
        self, attack: float, decay: float, sustain: float, release: float, amp: float
    ):
        self._attack = attack
        self._decay = decay
        self._sustain = sustain
        self._release = release
        self._released_samples = None
        self._samples = 0
        self._amp = amp

    def release(self):
        self._released_samples = 0

    def process(self, samples: list):
        return [sample * self.value for sample in samples]

    @property
    def is_dead(self):
        return (
            self._released_samples is not None
            and self._released_samples >= self._release * self._sample_rate
        )

    @property
    def value(self):
        # calculate the volume based on which section the envelope is in:
        # release:
        if self._released_samples is not None:
            value = (
                1 - self._released_samples / self._release / self._sample_rate
            ) * self._sustain
            value = max(0, value)
            self._released_samples += 1
        # attack:
        elif self._samples < self._attack * self._sample_rate:
            value = self._samples / self._attack / self._sample_rate
        # decay:
        elif self._samples < (self._attack + self._decay) * self._sample_rate:
            value = 1 - (
                self._samples - self._attack * self._sample_rate
            ) / self._decay / self._sample_rate * (1 - self._sustain)
        # sustain:
        else:
            value = self._sustain
        self._samples += 1
        return value * self._amp


class InstrumentAudio:
    """A class that manages all the notes for a synth voice. This is semi-analogous to an instrument in a DAW."""

    # FIXME this datatype isn't very OOP of me
    _notes: list[(Note, SynthVoice, AdsrEnvelope)]

    def __init__(self, synth_voice, envelope_values: tuple[float, float, float, float]):
        self._notes = []
        self._press_queue = Queue()
        self._release_queue = Queue()
        self._synth_voice = synth_voice
        self._envelope_values = envelope_values

    def play(self, note: Note):
        self._press_queue.put(note)

    def release(self, note: Note or int):
        """Take in either a `Note` object or a midi key number."""
        if type(note) == Note:
            note = Note.note
        self._release_queue.put(note)

    def release_all(self):
        for note in self._notes:
            self._release_queue.put(note[0].note)

    def get_next_samples(self, length: int):
        while self._press_queue.qsize():
            note: Note = self._press_queue.get()
            self._notes.append(
                (
                    note,
                    (
                        self._synth_voice
                    )(),  # call the synth voice class to create a new instance
                    AdsrEnvelope(*self._envelope_values, note.velocity / 127),
                )
            )
            self._notes[-1][1].play(note)

        # FIXME bug with releasing notes where notes can get stuck as pressed
        while self._release_queue.qsize():
            note = self._release_queue.get()
            for i in range(len(self._notes)):
                if self._notes[i][0].note == note:
                    self._notes[i][2].release()

        # remove dead notes
        self._notes = [note for note in self._notes if not note[2].is_dead]

        samples = [0] * length
        for i in range(len(self._notes)):
            note_samples = self._notes[i][1].get_next_samples(length)
            note_samples = self._notes[i][2].process(note_samples)
            samples = [samples[i] + note_samples[i] for i in range(length)]
        return samples

    @property
    def notes(self):
        return self._notes


class AudioManager:

    _compressor = Compressor(0.5, 5)

    def __init__(self):
        self._sample_rate = 44100
        self._length = 256
        self._instrument_audios = []
        self._max_sample = 0.0
        self._p = pyaudio.PyAudio()
        self._stream = self._p.open(
            output=True, format=pyaudio.paInt16, channels=1, rate=self._sample_rate
        )
        # self._waveform = []

    def add_instrument_audio(self, instrument_audio: InstrumentAudio):
        self._instrument_audios.append(instrument_audio)

    def get_next_samples(self, count: int):
        samples = [0] * count
        for synth in self._instrument_audios:
            synth: InstrumentAudio
            synth_samples = synth.get_next_samples(count)
            samples = [samples[i] + synth_samples[i] for i in range(count)]

        # Global FX chain:
        # compressor
        samples = self._compressor.process(samples)
        # dynamic limiter
        samples = [min(max(sample, -5), 5) for sample in samples]

        samples = [sample * 0.2 for sample in samples]

        samples = [int(sample * 32767) for sample in samples]

        return samples

    def callback(self, in_data, frame_count, time_info, status):
        samples = self.get_next_samples(frame_count)
        return (np.int16(samples).tobytes(), pyaudio.paContinue)

    def start(self):
        self._stream = self._p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=44100,
            output=True,
            stream_callback=self.callback,
        )
