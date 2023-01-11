COLOR_PALETTE = {
    "background": (216, 220, 222),
    "dark_key": (26, 77, 208),
    "light_key": (255, 255, 255),
    "pressed_light_key": (240, 244, 247),
    "pressed_dark_key": (13, 39, 104),
    "note_bar": (26, 77, 208),
    "particle": (26, 77, 208),
}
"""A dictionary of colors used in the application."""

screen = None
"""Hold a reference to the screen so that we can access it from anywhere."""

scroll_offset = {"x": 0, "y": 0}

# the particles that are currently being rendered (used for the note bar)
particles = []

app = None
audio_manager = None
audio_thread = None
