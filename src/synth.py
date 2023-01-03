from abc import ABC, abstractmethod


class SynthVoice(ABC):
    @abstractmethod
    def __iter__(self):
        yield 0


class SquareSynth(SynthVoice):
    def __init__(self, freq, amp, sample_rate):
        self.freq = freq
        self.amp = amp
        self.sample_rate = sample_rate
        self.phase = 0
