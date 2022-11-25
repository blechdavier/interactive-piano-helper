from math import floor
from time import time

import pygame as pg


class NoteRect:
    key_id: int
    time_pressed: float
    time_released: float = None
    sprite: pg.sprite.Sprite

    def __init__(self, key_id: int):
        self.key_id = key_id
        self.time_pressed = time()
        self.sprite = pg.sprite.Sprite()

    def release(self):
        self.time_released = time()

    def get_sprite(self, init_y: float):
        # maybe this is what getters are for?
        # like if there's a calculation that needs to be done

        if self.time_released is None:
            time_released = time()
        else:
            time_released = self.time_released

        key_width = 1 - float(self.key_id % 12 in [1, 3, 6, 8, 10]) * 0.25

        self.sprite.image = pg.Surface(
            (key_width * 50, (time_released - self.time_pressed) * 100)
        )
        self.sprite.image.fill("#0000ff")
        self.sprite.rect = self.sprite.image.get_rect()

        offsets = [0, 0.625, 1, 1.625, 2, 3, 3.625, 4, 4.625, 5, 5.625, 6]
        self.sprite.rect.x = (
            floor(self.key_id / 12) * 350 + offsets[self.key_id % 12] * 50
        )
        self.sprite.rect.y = init_y - (time() - self.time_pressed) * 100

        return self.sprite
