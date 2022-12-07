import itertools
import math


def get_samples(notes_dict, num_samples=256):
    thread_dict = notes_dict.copy()
    return [
        sum([int(next(osc) * 32767) for _, osc in thread_dict.items()])
        for _ in range(num_samples)
    ]


def get_sin_oscillator(freq=440, amp=1, sample_rate=44100):
    increment = (2 * math.pi * freq) / sample_rate
    return (math.sin(v) * amp for v in itertools.count(start=0, step=increment))
