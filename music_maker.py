from constants import *
import pygame as pg
from time import sleep
from metronome import *
import math
import numpy as np
from copy import deepcopy
from audio import *
from instructions_panel import *

class MusicMaker:

    def __init__(self, screen):
        self.pitch = 0
        self.screen = screen
        self.pitch_range = PITCH_RANGE
        self.b_left = 0
        self.b_middle = 0
        self.b_right = 0
        self.events = set()
        self.metronome = Metronome(BUFFERS_PER_MEASURE)
        self.is_measure = False
        self.using_scales = list(range(1,6))
        self.scale = self.using_scales[3]
        self.scale_height = SCREEN_DIM[1] / len(self.using_scales)
        self.background = None
        self.background_needs_update = True
        self.instructions = InstructionsPanel(SCREEN_DIM[0] - 380, 10, 370, SCREEN_DIM[1]-20)
        self.show_instructions = True
        self.audio_player = None
        self.audio_player = AudioPlayer(self)
        self.audio_player.run()

    def do_step(self):
        ## Avoid the race condition
        while self.audio_player == None:
            sleep(.1)

        ## Gather information from metronome, mouse, and keyboard
        is_beat = self.metronome.is_beat(self.audio_player.loop_buffer_index)
        self.is_measure = self.metronome.is_measure(self.audio_player.loop_buffer_index)
        (m_x, m_y) = pygame.mouse.get_pos()
        (last_b_left, last_b_middle, last_b_right) = (self.b_left, self.b_middle, self.b_right)
        (self.b_left, self.b_middle, self.b_right) = pygame.mouse.get_pressed()
        last_keys = keys[:]
        keys.clear()
        keys.extend(pygame.key.get_pressed())

        ## Center scales around mouse
        if self.b_middle and not last_b_middle:
            self.background_needs_update = True
            m_x, m_y = self.center_scales_around(m_x, m_y)

        ## Run events scheduled for the beginning of the step
        for e in sorted(list(self.events), key=lambda e: e[0]):
            if e[2] == BEGIN_STEP:
                if e[1] == NEXT_BUFFER or ( is_beat and e[1] == NEXT_BEAT ) or ( self.is_measure and e[1] == NEXT_MEASURE ):
                    self.audio_player.do_action(e[0])
                    self.events.remove(e)

        ###########################
        ## Keyboard and mouse input

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
            ## These events aren't caught by the pygame.mouse methods
            if event.type == pygame.MOUSEBUTTONDOWN:
                ## Scroll down
                if event.button == 5:
                    self.audio_player.decrease_volume()
                ## Scroll up
                if event.button == 4:
                    self.audio_player.increase_volume()

        ## Get the exact pitch from the mouse x coordinate
        self.mouse_pitch = self.coord_to_pitch(m_x, coord=0, reverse=False)

        ## Close the application
        if is_key_mod(ESCAPE, None):
            self.audio_player.stop_stream()
            print("Ending stream...")

        ## Start and stop recording
        if not keys[SPACE] and self.audio_player.loop_recording:
            self.events.add(EVENT_STOP_LOOP_REC)
        if keys[SPACE] and not self.audio_player.loop_recording:
            self.events.add(EVENT_START_LOOP_REC)

        ## Start and stop playing of all loops
        if is_key_mod(K_P, None) and not last_keys[K_P]:
            if self.audio_player.loop_playing:
                self.events.add(EVENT_STOP_LOOP_PLAY)
            else:
                self.events.add(EVENT_START_LOOP_PLAY)

        ## Mute and unmute the active loop
        if is_key_mod(K_M, None) and not last_keys[K_M]:
            self.audio_player.loops[self.audio_player.active_loop_index].toggle_mute()

        ## Increase and decrease volume of the active looop
        if is_key_mod(UP, SHIFT):
            self.audio_player.loops[self.audio_player.active_loop_index].adjust_volume(.02)
        if is_key_mod(DOWN, SHIFT):
            self.audio_player.loops[self.audio_player.active_loop_index].adjust_volume(-.02)

        ## Copy the active loop below it, and mute the copy
        if is_key_mod(K_C, CTRL) and not last_keys[K_C]:
            loop = self.audio_player.loops[self.audio_player.active_loop_index]
            image = loop.image
            loop.image=None
            loop_copy = deepcopy(loop)
            loop.image = image
            self.audio_player.loops.insert(self.audio_player.active_loop_index+1, loop_copy)
            loop_copy.set_mute(True)

        ## Move the active loop left/right by one beat (with wrapping)
        if is_key_mod(LEFT, None) and not last_keys[LEFT]:
            self.audio_player.loops[self.audio_player.active_loop_index].horizontal_shift(-1*self.metronome.beat_len)
        if is_key_mod(RIGHT, None) and not last_keys[RIGHT]:
            self.audio_player.loops[self.audio_player.active_loop_index].horizontal_shift(self.metronome.beat_len)

        ## Move the active loop left/right by one buffer (with wrapping)
        if is_key_mod(LEFT, SHIFT) and not last_keys[LEFT]:
            self.audio_player.loops[self.audio_player.active_loop_index].horizontal_shift(-1)
        if is_key_mod(RIGHT, SHIFT) and not last_keys[RIGHT]:
            self.audio_player.loops[self.audio_player.active_loop_index].horizontal_shift(1)

        ## Move the active loop indicator up and down
        if is_key_mod(UP, None) and not last_keys[UP]:
            self.audio_player.active_loop_index -= 1
            self.audio_player.active_loop_index %= len(self.audio_player.loops)
        if is_key_mod(DOWN, None) and not last_keys[DOWN]:
            self.audio_player.active_loop_index += 1
            self.audio_player.active_loop_index %= len(self.audio_player.loops)

        ## Move the active loop up and down in the lineup
        if self.audio_player.active_loop_index >= 0:
            index = self.audio_player.active_loop_index
            other_index=-1
            if is_key_mod(UP, CTRL) and not last_keys[UP]:
                other_index = (index-1)%len(self.audio_player.loops)
            elif is_key_mod(DOWN, CTRL) and not last_keys[DOWN]:
                other_index = (index+1)%len(self.audio_player.loops)
            if other_index >= 0:
                loops = self.audio_player.loops
                loops[index], loops[other_index] = loops[other_index], loops[index]
                self.audio_player.active_loop_index = other_index

        ## Combine this loop with the one below it 
        if (keys[PLUS] and not last_keys[PLUS]) or (keys[pygame.K_KP_PLUS] and not last_keys[pygame.K_KP_PLUS]):
            loop_count = len(self.audio_player.loops)
            index = self.audio_player.active_loop_index
            if loop_count > 1 and index < loop_count-1:
                self.audio_player.loops[index].combine(self.audio_player.loops[index+1])
                del self.audio_player.loops[index+1]

        ## Delete the current loop with backspace or delete
        if (is_key_mod(BACKSPACE, None) and not last_keys[BACKSPACE]) or (is_key_mod(DELETE, None) and not last_keys[DELETE]):
            if self.audio_player.active_loop_index >= 0:
                del self.audio_player.loops[self.audio_player.active_loop_index]
                if self.audio_player.active_loop_index >= len(self.audio_player.loops):
                    self.audio_player.active_loop_index -= 1

        ## Articulating and continuing a note playing
        if self.b_left:
            if not self.audio_player.playing:
                self.audio_player.volume = ARTICULATION_FACTOR * self.audio_player.adjusted_base_volume()
                self.audio_player.previous_volume = self.audio_player.volume
                self.audio_player.playing=True
            else:
                self.audio_player.settle_to_volume()
        
        ## Allowing a note to fade away when not left clicking
        if not self.b_left:
            self.audio_player.volume_decay()

        ## Identify the current scale by mouse position
        self.scale_index = (self.using_scales[0] + int(m_y / SCREEN_DIM[1] * len(self.using_scales))) %12
        self.scale = SCALES[self.scale_index]

        ## Temporarily align to the chromatic scale on the current scale
        if (self.b_right):
            self.scale = CHROMATIC_SCALE

        ## Show and hide the instructions (really for QUESTION_MARK, but SLASH is more accepting)
        if (keys[SLASH] and not last_keys[SLASH]):
            self.show_instructions = not self.show_instructions

        #######################
        ## Pitch decisionmaking

        ## Get scale degree of closest pitch
        self.closest_pitch = sorted(self.scale, key=lambda x: min(abs((self.mouse_pitch%12)-x), 12 - abs((self.mouse_pitch%12)-x))) [0]
        ## Put closest pitch in correct octave
        self.closest_pitch += math.floor(self.mouse_pitch / 12) * 12
        ## Correct an error by rounding up if self.mouse_pitch > 11.5
        if abs(self.mouse_pitch - self.closest_pitch) > 10:
            self.closest_pitch += 12

        ## In case we switched scales for the chromatic scale, switch back now that we decided on a closest pitch
        self.scale = SCALES[self.scale_index]

        ## Decide whether to align to the closest pitch, or use the mouse pitch
        #if not last_b_middle:
        if is_key_mod(K_S, None):
            self.pitch = self.mouse_pitch
        elif self.b_left or self.audio_player.volume == 0: 
            self.pitch = self.closest_pitch

        ## Run events scheduled for the end of the step
        for e in sorted(list(self.events), key=lambda e: e[0]):
            if e[2] == END_STEP:
                if e[1] == NEXT_BUFFER or ( is_beat and e[1] == NEXT_BEAT ) or ( self.is_measure and e[1] == NEXT_MEASURE ):
                    self.audio_player.do_action(e[0])
                    self.events.remove(e)

        self.paint_screen()

    def center_scales_around(self, m_x, m_y):
        range_width = self.pitch_range[1] - self.pitch_range[0]
        range_middle = self.pitch_range[1] - range_width // 2
        diff = self.closest_pitch - range_middle
        self.pitch_range = (self.pitch_range[0]+diff, self.pitch_range[1]+diff)
        y_diff = self.scale_index - self.using_scales[len(self.using_scales)//2]
        self.using_scales = [(i+y_diff)%12 for i in self.using_scales]
        new_m_x = self.pitch_to_coord(self.mouse_pitch)
        new_m_y = m_y-y_diff*self.scale_height
        pygame.mouse.set_pos(new_m_x, new_m_y)
        return new_m_x, new_m_y

    def paint_screen(self):
        ## Draw the mostly unchanging buffered background
        if self.background == None or self.background_needs_update:
            self.background = self.redraw_background()
        self.screen.blit(self.background, (0,0))
        ## Draw the active notes
        y=0
        notes = [l.recorded_notes[self.audio_player.loop_buffer_index] for l in self.audio_player.loops if not l.muted]
        self.recorded_notes_to_draw = [rn for sublist in notes for rn in sublist]
        for i in self.using_scales:
            s = SCALES[i]
            self.draw_scale_activity(s, y, self.scale is s)
            y += self.scale_height
        ## Draw metronome
        self.metronome.paint_self(self.screen, self.audio_player.loop_buffer_index)
        ## Draw the loops
        y = 60
        x = 10
        w = self.metronome.measure_len * VISUAL_BUFFER_WIDTH
        h = 30
        v_margin = 10
        for i in range(len(self.audio_player.loops)):
            loop = self.audio_player.loops[i]
            loop.paint_self(self.screen, (x,y,w,h), i==self.audio_player.active_loop_index, self.audio_player.loop_recording)
            y += h + v_margin
        ## Draw the instruction panel
        if self.show_instructions:
            self.instructions.paint_self(self.screen)
        else:
            self.instructions.paint_minimized_self(self.screen)

        pygame.display.flip()
    
    '''
    Draws the active elements of a scale (row of notes) on the screen.
    '''
    def draw_scale_activity(self, scale, y, is_active):

        notes_to_draw = [rn for rn in self.recorded_notes_to_draw if rn.scale==scale]
        if self.scale == scale:
            notes_to_draw.append(RecordedNote(-1, self.pitch, self.audio_player.volume, self.scale, None))

        for p in range(self.pitch_range[0], self.pitch_range[1]+1):
            p_i = p % 12
            if p_i in scale:
                x = self.pitch_to_coord(p, coord=0, reverse=False)
                color = ACTIVE_COLORS[p_i] if is_active and self.closest_pitch == p else INACTIVE_COLORS[p_i]
                
                ##Determine line width based on notes_to_draw:
                on_this_pitch = [rn for rn in notes_to_draw if rn.pitch == p]
                notes_to_draw = [rn for rn in notes_to_draw if not rn in on_this_pitch]
                if len(on_this_pitch) > 0:
                    sum_volume = sum(map(lambda rn: rn.volume*rn.loop.volume if rn.loop else rn.volume, on_this_pitch))
                    line_width = max(INACTIVE_NOTE_WIDTH, int(sum_volume*ACTIVE_NOTE_STRETCH))
                    pygame.draw.line(self.screen, color, (x,y), (x,y+self.scale_height), line_width)
                    if get_font() and p_i == scale[0]:
                        l1 = get_font().render(NOTE_NAMES[p_i], 1, color)
                        self.screen.blit(l1, (x+10, y+self.scale_height-30))
        if is_active:
            pygame.draw.line(self.screen, HORIZONTAL_ACTIVE_COLOR, (0,y), (SCREEN_DIM[0],y), 1) 
            pygame.draw.line(self.screen, HORIZONTAL_ACTIVE_COLOR, (0,y+self.scale_height), (SCREEN_DIM[0],y+self.scale_height), 1) 

        ## The remaining pitches in notes_to_draw are not on a bar
        for rn in notes_to_draw:
            line_width = max(INACTIVE_NOTE_WIDTH, int(rn.volume * ACTIVE_NOTE_STRETCH))
            x = self.pitch_to_coord(rn.pitch)
            pygame.draw.line(self.screen, FREE_NOTE_COLOR, (x, y), (x,y+self.scale_height), line_width)

    '''
    Draws the inactive scale elements into a buffer image
    '''
    def redraw_background(self):
        self.background_needs_update = False
        screen = pygame.Surface(SCREEN_DIM)
        screen.fill(BACK_COLOR)
        y=0
        for i in self.using_scales:
            self.draw_scale_background(screen, SCALES[i], y)
            y += self.scale_height
        return screen
    
    '''
    Draws the inactive elements of one scale onto an image
    '''
    def draw_scale_background(self, screen, scale, y):
        for p in range(self.pitch_range[0], self.pitch_range[1]+1):
            p_i = p % 12
            if p_i in scale:
                x = self.pitch_to_coord(p, coord=0, reverse=False)
                pygame.draw.line(screen, INACTIVE_COLORS[p_i], (x,y), (x,y+self.scale_height), INACTIVE_NOTE_WIDTH)
                if get_font() and p_i == scale[0]:
                    l1 = get_font().render(NOTE_NAMES[p_i], 1, INACTIVE_COLORS[p_i])
                    screen.blit(l1, (x+10, y+self.scale_height-30))
      
    def coord_to_pitch(self, y, coord=0, reverse=False):
        if reverse:
            return (self.pitch_range[1] - self.pitch_range[0]) / SCREEN_DIM[coord] * (SCREEN_DIM[coord] - y) + self.pitch_range[0]
        else:
            return (self.pitch_range[1] - self.pitch_range[0]) / SCREEN_DIM[coord] * y + self.pitch_range[0]

    def pitch_to_coord(self, p, coord=0, reverse=False):
        if reverse:
            return SCREEN_DIM[coord] - (p - self.pitch_range[0]) / (self.pitch_range[1] - self.pitch_range[0]) * SCREEN_DIM[coord]
        else:
            return (p - self.pitch_range[0]) / (self.pitch_range[1] - self.pitch_range[0]) * SCREEN_DIM[coord]
