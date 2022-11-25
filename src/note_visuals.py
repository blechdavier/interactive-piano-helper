from math import floor
from random import random
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

    def create_particles(self, init_y: float):
        particles = []

        (x, y, w, h) = self.get_sprite(init_y).rect

        for _ in range(randomly_to_int(w * h / 10000)):
            particles.append(
                Particle(
                    x + random() * w, y + random() * h, "#00ff00", 0.5 + random() * 0.5
                )
            )

        return particles


def randomly_to_int(v: float):
    if random() > v - floor(v):
        return floor(v)
    else:
        return floor(v) + 1


class Particle:
    x: float
    y: float
    xv: float
    yv: float
    color: str
    death_time: float
    sprite: pg.sprite.Sprite

    def __init__(self, x: float, y: float, color: str, life: float):
        self.x = x - 5
        self.y = y - 5
        self.xv = random() - 0.5
        self.yv = random() - 0.5
        self.color = color
        self.death_time = time() + life
        self.sprite = pg.sprite.Sprite()
        self.sprite.image = pg.Surface((10, 10))
        self.sprite.image.fill(self.color)
        self.sprite.rect = self.sprite.image.get_rect()
        self.sprite.rect.x = self.x
        self.sprite.rect.y = self.y

    def update(self):
        self.x += self.xv
        self.y += self.yv

    def get_sprite(self):
        self.sprite.rect.x = self.x
        self.sprite.rect.y = self.y
        return self.sprite
