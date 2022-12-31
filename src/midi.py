from pygame import midi

from time import sleep

from queue import Queue


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
