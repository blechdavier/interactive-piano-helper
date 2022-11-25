import numpy as np
import pyaudio

import synth


def daemon_function(lock, notes_dict):
    # initiate a pyaudio stream
    stream = pyaudio.PyAudio().open(
        rate=44100,
        channels=1,
        format=pyaudio.paInt16,
        output=True,
        frames_per_buffer=256,
    )

    while True:
        # Play the notes
        with lock:
            notes = notes_dict
        samples = synth.get_samples(notes)
        samples = np.int16(samples).tobytes()
        stream.write(samples)
