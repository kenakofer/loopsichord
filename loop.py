import numpy as np
from constants import *


class Loop:

    def __init__(self, length):
        self.length = length # Length in number of buffers
        self.buffers = [np.zeros(BUFFER_SIZE) for i in range(self.length)]
        self.recorded_notes = [[] for i in range(self.length)]
        self.volume = 1
        self.has_recorded = False # Flag for if anything has recorded to this loop
        self.muted = False
        self.image = None
        self.image_needs_update = True
        self.color = LOOP_PITCH_COLOR
        self.overtones = MY_OVERTONES

    def combine(self, other):
        self.image_needs_update = True
        for i in range(len(self.recorded_notes)):
            self.recorded_notes[i].extend(other.recorded_notes[i])
            self.recorded_notes[i].sort(key=lambda rn: rn.pitch, reverse=True) 
            self.buffers[i] += other.buffers[i]

    def toggle_mute(self):
        self.image_needs_update = True
        self.muted = not self.muted
        self.color = LOOP_PITCH_COLOR if not self.muted else LOOP_MUTED_PITCH_COLOR
        return self.muted

    def set_mute(self, on_off):
        self.image_needs_update = True
        self.muted = on_off
        self.color = LOOP_PITCH_COLOR if not self.muted else LOOP_MUTED_PITCH_COLOR
        return self.muted

    def adjust_volume(self, volume_adjustment):
        self.image_needs_update = True
        self.volume += volume_adjustment
        if self.volume < 0:
            self.volume = 0
        if self.volume > LOOP_MAX_VOLUME:
            self.volume = LOOP_MAX_VOLUME
        return self.volume

    def horizontal_shift(self, amount):
        self.image_needs_update = True
        slice_at = -1*amount
        self.buffers = self.buffers[slice_at:] + self.buffers[:slice_at]
        self.recorded_notes = self.recorded_notes[slice_at:] + self.recorded_notes[:slice_at]
        for rn in [rn for sublist in self.recorded_notes for rn in sublist]:
            rn.buffer_index -= slice_at
            rn.buffer_index %= self.length

    def pitch_shift(self):
        # TODO for all RecordedNotes, change pitch, recalculate
        assert False

    def paint_self(self, screen, rect, is_active, is_recording):
        (x,y,w,h) = rect
        if self.image == None or self.image_needs_update:
            self.image = self.redraw_self(w,h, is_recording)
        screen.blit(self.image, (x,y,w,h))
        if is_active:
            pygame.draw.rect(screen, ACTIVE_LOOP_OUTLINE_COLOR, rect, 1)

    def redraw_self(self, w, h, recording):
        self.image_needs_update = False
        screen = pygame.Surface((w,h))
        screen.fill(LOOP_BACK_COLOR) if not recording else screen.fill(LOOP_RECORDING_BACK_COLOR)
        flat_notes = [rn for sublist in self.recorded_notes for rn in sublist]
        if len(flat_notes) == 0:
            return screen
        pitches = set(map(lambda rn: rn.pitch, flat_notes))
        pitch_range = [min(pitches), max(pitches)]
        pitch_range[1] += 10
        if  pitch_range[1] - pitch_range[0] < 20:
            pitch_range[1] = pitch_range[0] + 20
        rnw = w / self.length
        for rn in flat_notes:
            rnx = rn.buffer_index * rnw
            rny = (pitch_range[1] - rn.pitch) / (pitch_range[1] - pitch_range[0]) * h
            rnh = max(1,int(rn.volume*20*self.volume))
            pygame.draw.rect(screen, (100,0,0), (rnx, rny-rnh-1, rnw+1, rnh+2))
            pygame.draw.rect(screen, self.color, (rnx, rny-rnh, rnw+1, rnh))
        return screen

    def add_recorded_note(self, index, pitch, volume, scale):
        self.image_needs_update = True
        self.recorded_notes[index].append(RecordedNote(index, pitch, volume, scale, self))
        self.recorded_notes[index].sort(key=lambda rn: rn.pitch, reverse=True) 
        

    '''
    TODO maybe wait on this
    def recalculate_buffers(self):
        self.buffers = [np.zeros(BUFFER_SIZE) for i in range(self.length)]
        percent_through_period = 0
        for i_l in range(len(self.recorded_notes)):
            previous = self.recorded_notes[(i-1)%self.length]
            previous_volume = previous[0].volume
            for rn in self.recorded_notes[i_l]:
                freq = musical_pitch_to_hertz(rn.pitch)
                samples, percent_through_period = AudioPlayer.sin(freq, sample_count=BUFFER_SIZE, fs=FS, volume=rn.volume, previous_volume=previous_volume percent_through_period=percent_through_period, overtones=self.overtones)
                volume[rn.buffer_index] = rn.volume
    '''

class RecordedNote:

    def __init__(self, buffer_index, pitch, volume, scale, loop):
        self.buffer_index = buffer_index
        self.pitch = pitch
        self.volume = volume
        self.scale = scale
        self.loop = loop

    def __repr__(self):
        return 'RecordedNote('+str(self.buffer_index)+', '+str(self.pitch)+', '+str(self.volume)+')'


