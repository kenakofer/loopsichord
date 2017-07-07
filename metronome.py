from time import time
from constants import *
import pygame


class Metronome:

    def __init__(self, measure_len, beats = 8):

        self.measure_len = measure_len
        self.beats = beats
        assert measure_len % beats == 0
        self.visual_buffer_width = VISUAL_BUFFER_WIDTH
        self.beat_len = measure_len // beats 
        self.sound = True

    def change_measure_length(self, change):
        self.measure_len += change
        self.measure_len = max(self.measure_len, 8)
        assert self.measure_len % self.beats == 0
        self.beat_len = self.measure_len // self.beats 
        return self.measure_len

    def change_beat_count(self, change):
        self.beats += change
        self.measure_len -= self.measure_len % self.beats
        assert self.measure_len % self.beats == 0
        self.beat_len = self.measure_len // self.beats 
        return self.beats
    
    def get_beat(self, buffer_number):
        return buffer_number // self.beat_len

    def is_beat(self, buffer_number):
        return buffer_number // self.beat_len != (buffer_number - 1) // self.beat_len

    def is_measure(self, buffer_number):
        return buffer_number == 0

    def paint_self(self, screen, buffer_number, is_active):
        height = 40
        m_width = self.measure_len * self.visual_buffer_width
        b_width = m_width // self.beats
        m_width = b_width * self.beats
        self.visual_buffer_width = m_width // self.measure_len
        x = 10
        y = 10
        ## Background
        pygame.draw.rect(screen, METRONOME_INACTIVE_COLOR, (x,y,m_width, height), 0)
        ## Active index outline
        if is_active:
            pygame.draw.rect(screen, ACTIVE_LOOP_OUTLINE_COLOR, (x-1,y-1,m_width+2,height+2), 1)
        #Draw beats
        for i in range(self.beats):
            if self.get_beat(buffer_number) == i:
                pygame.draw.rect(screen, METRONOME_ACTIVE_COLOR, (x,y,b_width, height), 0)
            pygame.draw.rect(screen, (0,0,0), (x,y,b_width, height), 1)
            x += b_width
        ## Exact position line
        x = 10 + m_width * buffer_number / self.measure_len
        pygame.draw.line(screen, (0,0,0), (x,y), (x,y+height))




