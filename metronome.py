from time import time
from constants import *
import pygame


class Metronome:

    def __init__(self, measure_len, beats = 8):

        self.measure_len = measure_len
        self.beats = beats
        assert measure_len % beats == 0
        self.beat_len = measure_len // beats 
        self.sound = True

    
    def get_beat(self, buffer_number):
        return buffer_number // self.beat_len

    def is_beat(self, buffer_number):
        return buffer_number // self.beat_len != (buffer_number - 1) // self.beat_len

    def is_measure(self, buffer_number):
        return buffer_number == 0

    def paint_self(self, screen, buffer_number):
        height = 40
        m_width = self.measure_len * VISUAL_BUFFER_WIDTH
        b_width = m_width / self.beats
        x = 10
        y = 10
        for i in range(self.beats):
            color = METRONOME_ACTIVE_COLOR if self.get_beat(buffer_number) == i else METRONOME_INACTIVE_COLOR
            pygame.draw.rect(screen, color, (x,y,b_width, height), 0)
            x += b_width
        x = 10 + m_width * buffer_number / self.measure_len #TODO fix
        pygame.draw.line(screen, (0,0,0), (x,y), (x,y+height))




