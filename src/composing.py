class ComposingContext:
    """A composing_context contains information about the music being played and methods for generating music."""

    def __init__(self):
        self._notes = []
        self._note_frequency = [0] * 12
        self._auto_instruments = []

    def add_note(self, note: int):
        # add this not to the list of the notes that are currently being played
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
        # print(f"You're playing in {key_sig[0]} {key_sig[1]}")
        return key_sig


class AutoInstrument(ABC):
    _instrument_audio: InstrumentAudio

    @abstractmethod
    def play(self, composing_context: ComposingContext):
        self._instrument_audio.play(Note(60, 80))
