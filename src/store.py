COLOR_PALETTE = {
    "background": (255, 235, 59),
    "dark_key": (255, 89, 22),
    "light_key": (255, 173, 54),
    "pressed_key": (255, 61, 0),
}
"""A dictionary of colors used in the application."""

screen = None
"""Hold a reference to the screen so that we can access it from anywhere."""

scroll_offset = {"x": 0, "y": 0}

# the particles that are currently being rendered (used for the note bar)
particles = []
