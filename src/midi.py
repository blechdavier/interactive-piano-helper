from math import floor
import pygame as pg

class MidiKey: 
    def __init__(self, key_id, white_key_container = None, black_key_container = None):
        '''A MidiKey is a class representing a key on a piano and its pitch. Its `init()` function calculates its information given its `key_id`.'''
        #TODO make these set in the functions and not by the return types of the functions
        self.pitch = 440 * 2 ** ((key_id - 69) / 12)
        self.key_id = key_id
        self.key_name = self.get_key_name()
        (self.key_color, self.key_width) = self.get_visuals()
        self.init_sprite()
        print("Initialized key " + str(self.key_id) + " with pitch " + str(self.pitch) + " and name " + str(self.key_name))
        if(white_key_container != None and black_key_container != None):
            self.add_to_rendering(white_key_container, black_key_container)

    def get_key_name(self):
        '''Get the MidiKey's `key_name` tuple. This will later be indexed based on whether the key has sharps or flats.'''
        key_names = [("C", "C"), ("C#", "Db"), ("D", "D"), ("D#", "Eb"), ("E", "E"), ("F", "F"), ("F#", "Gb"), ("G", "G"), ("G#", "Ab"), ("A", "A"), ("A#", "Bb"), ("B", "B")]
        return key_names[self.key_id % 12]

    def get_visuals(self):
        '''Get the MidiKey's `key_color` and `key_width` in a tuple.'''
        if self.key_id % 12 in [1, 3, 6, 8, 10]:
            return ("#000000", 0.75)
        else:
            return ("#ffffff", 1)

    def init_sprite(self):
        self.sprite = pg.sprite.Sprite()
        self.sprite.image = pg.Surface((self.key_width * 50, self.key_width*350-120))
        self.sprite.image.fill(self.key_color)
        self.sprite.rect = self.sprite.image.get_rect()
        offsets = [0, 0.625, 1, 1.625, 2, 3, 3.625, 4, 4.625, 5, 5.625, 6]
        self.sprite.rect.x = floor(self.key_id/12) * 350 + offsets[self.key_id % 12] * 50
        self.sprite.rect.y = 0

    def add_to_rendering(self, white_key_container, black_key_container):
        '''Add the MidiKey as a piano key to the `white_key_container` and `black_key_container`. This is done by checking the `key_color` of the key.'''
        if self.key_color == "#000000":
            black_key_container.add(self.sprite)
        else:
            white_key_container.add(self.sprite)
    
    def update_visuals(self, is_pressed):
        '''Update the visuals of the key based on whether it is being pressed or not.'''
        if is_pressed:
            self.sprite.image.fill("#ff0000")
        else:
            self.sprite.image.fill(self.key_color)