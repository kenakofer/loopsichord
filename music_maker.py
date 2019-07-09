from constants import *
import pygame as pg
from time import sleep
from metronome import *
import math
import numpy as np
from copy import deepcopy
from audio import *
from instructions_panel import *
from loop import *

class MusicMaker:

    def __init__(self, screen):
        self.pitch = 0
        self.screen = screen
        self.pitch_range = (
                int(PITCH_CENTER_START - PITCH_RANGE_SMALL//2), 
                int(PITCH_CENTER_START + PITCH_RANGE_SMALL//2)
                )
        self.b_left = 0
        self.b_middle = 0
        self.b_right = 0
        self.saved = None
        self.events = set()
        self.metronome = Metronome(BUFFERS_PER_MEASURE)
        self.is_measure = False
        self.using_scales = list(range(1,6))
        self.scale = self.using_scales[3]
        self.scale_height = SCREEN_DIM[1] / len(self.using_scales)
        self.chord = None
        self.background = None
        self.background_needs_update = True
        self.instructions = InstructionsPanel()
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
            elif event.type == pygame.MOUSEBUTTONDOWN:
                ## Scroll down
                if event.button == 5:
                    self.audio_player.decrease_volume()
                ## Scroll up
                if event.button == 4:
                    self.audio_player.increase_volume()
            ## Window resize
            elif event.type == pygame.VIDEORESIZE:
                w,h = event.size
                min_w, min_h = MIN_DIM
                w = max(min_w, w)
                h = max(min_h, h)
                update_screen_size((w,h))
                self.background_needs_update = True
                self.scale_height = SCREEN_DIM[1] / len(self.using_scales)
                self.screen = pygame.display.set_mode(SCREEN_DIM, pygame.RESIZABLE)

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


        ## If a loop is selected:
        if self.audio_player.active_loops[0] >= 0 and not self.audio_player.loop_recording:

            ## Move the active loops left/right by one beat (with wrapping)
            if is_key_mod(LEFT, None) and not last_keys[LEFT]:
                for i in self.audio_player.active_loops:
                    self.audio_player.loops[i].horizontal_shift(-1*self.metronome.beat_len)
            if is_key_mod(RIGHT, None) and not last_keys[RIGHT]:
                for i in self.audio_player.active_loops:
                    self.audio_player.loops[i].horizontal_shift(self.metronome.beat_len)

            ## Move the active loops left/right by one buffer (with wrapping)
            if is_key_mod(LEFT, SHIFT) and not last_keys[LEFT]:
                for i in self.audio_player.active_loops:
                    self.audio_player.loops[i].horizontal_shift(-1)
            if is_key_mod(RIGHT, SHIFT) and not last_keys[RIGHT]:
                for i in self.audio_player.active_loops:
                    self.audio_player.loops[i].horizontal_shift(1)

            ## Toggle mute on the active loops
            if is_key_mod(K_M, None) and not last_keys[K_M]:
                for i in self.audio_player.active_loops:
                    self.audio_player.loops[i].toggle_mute()

            ## Increase and decrease volume of the active loops
            if keys[EQUALS] or keys[PLUS] or keys[KP_PLUS]:
                for i in self.audio_player.active_loops:
                    self.audio_player.loops[i].adjust_volume(.02)
            if keys[MINUS] or keys[KP_MINUS]:
                for i in self.audio_player.active_loops:
                    self.audio_player.loops[i].adjust_volume(-.02)

            ## Copy the active loops below them as a group, and mute the copies
            if is_key_mod(K_C, CTRL) and not last_keys[K_C]:
                loop_copies = [self.audio_player.loops[i].get_copy() for i in self.audio_player.active_loops]
                for i,loop in enumerate(loop_copies):
                    loop.set_mute(True)
                    self.audio_player.loops.insert(self.audio_player.active_loops[-1]+1+i, loop)
                self.audio_player.active_loops = [x+len(loop_copies) for x in self.audio_player.active_loops]

            ## Move the active loops up and down in the lineup
            other_index = -1
            loops = self.audio_player.loops
            if is_key_mod(UP, ALT) and not last_keys[UP] and self.audio_player.active_loops[0] > 0:
                for index in self.audio_player.active_loops:
                    other_index = (index-1)%len(self.audio_player.loops)
                    loops[index], loops[other_index] = loops[other_index], loops[index]
                self.audio_player.active_loops = [x-1 for x in self.audio_player.active_loops]
            elif is_key_mod(DOWN, ALT) and not last_keys[DOWN] and self.audio_player.active_loops[-1] < len(loops)-1:
                for index in self.audio_player.active_loops[::-1]:
                    other_index = (index+1)%len(self.audio_player.loops)
                    loops[index], loops[other_index] = loops[other_index], loops[index]
                self.audio_player.active_loops = [x+1 for x in self.audio_player.active_loops]

            ## Add the selected loops 
            if is_key_mod(K_U, None) and not last_keys[K_U]:
                while len(self.audio_player.active_loops) > 1:
                    i = self.audio_player.active_loops[0]
                    other = self.audio_player.active_loops.pop()
                    self.audio_player.loops[i].combine(self.audio_player.loops[other])
                    del self.audio_player.loops[other]
                    
            ## Pitch shift the selected loops UP/DOWN
            if is_key_mod(UP, CTRL) and is_key_mod(UP, SHIFT) and not last_keys[UP]:
                for index in self.audio_player.active_loops:
                    #Shift up one eighth of a tone
                    self.audio_player.loops[index].pitch_shift(.25)
            elif is_key_mod(UP, CTRL) and not last_keys[UP]:
                for index in self.audio_player.active_loops:
                    #Shift up one semitone
                    self.audio_player.loops[index].pitch_shift(1)
            elif is_key_mod(DOWN, CTRL) and is_key_mod(DOWN, SHIFT) and not last_keys[DOWN]:
                for index in self.audio_player.active_loops:
                    #Shift up one eighth of a tone
                    self.audio_player.loops[index].pitch_shift(-.25)
            elif is_key_mod(DOWN, CTRL) and not last_keys[DOWN]:
                for index in self.audio_player.active_loops:
                    #Shift up one semitone
                    self.audio_player.loops[index].pitch_shift(-1)


            ## Delete the current loop with backspace or delete
            if (is_key_mod(BACKSPACE, None) and not last_keys[BACKSPACE]) or (is_key_mod(DELETE, None) and not last_keys[DELETE]):
                for i in self.audio_player.active_loops[::-1]:
                    del self.audio_player.loops[i]
                self.audio_player.active_loops = [self.audio_player.active_loops[0]]
                if self.audio_player.active_loops[0] >= len(self.audio_player.loops):
                    self.audio_player.active_loops[0] -= 1

        else: ## Metronome selected (index -1)

            ##Only allow changes to the metronome when there are no loops:
            if len(self.audio_player.loops) == 0:
                ## Add or subtract from the metronome length
                if is_key_mod(LEFT, None) and not last_keys[LEFT]:
                    self.metronome.change_measure_length(-self.metronome.beats)
                if is_key_mod(RIGHT, None) and not last_keys[RIGHT]:
                    self.metronome.change_measure_length(self.metronome.beats)
                ## Add or subtract from the metronome beat count
                if is_key_mod(LEFT, SHIFT) and not last_keys[LEFT]:
                    self.metronome.change_beat_count(-1)
                if is_key_mod(RIGHT, SHIFT) and not last_keys[RIGHT]:
                    self.metronome.change_beat_count(1)

        ## Toggle justify pitch
        if is_key_mod(K_J, None) and not last_keys[K_J]:
            self.audio_player.justify_pitch = not self.audio_player.justify_pitch
            self.background_needs_update = True
            for loop in self.audio_player.loops:
                loop.recalculate_buffers()

        

        if not self.audio_player.loop_recording:
            ## Move the active loop indicator up and down
            if is_key_mod(UP, None) and not last_keys[UP]:
                self.audio_player.active_loops = [ self.audio_player.active_loops[0] % (len(self.audio_player.loops)+1) - 1 ]
            if is_key_mod(DOWN, None) and not last_keys[DOWN]:
                self.audio_player.active_loops = [ (self.audio_player.active_loops[-1]+2) % (len(self.audio_player.loops)+1) - 1 ]

            ## Select a range of loops
            if is_key_mod(UP, SHIFT) and not is_key_mod(UP, CTRL) and not last_keys[UP] and self.audio_player.active_loops[0] > 0:
                self.audio_player.active_loops.insert(0, self.audio_player.active_loops[0]-1)
            if is_key_mod(DOWN, SHIFT) and not is_key_mod(DOWN, CTRL) and not last_keys[DOWN] and self.audio_player.active_loops[0] >= 0 and self.audio_player.active_loops[-1] < len(self.audio_player.loops) - 1:
                self.audio_player.active_loops.append(self.audio_player.active_loops[-1]+1)

            ## Multiply metronome and loops a given number of times
            for num in range(2,10):
                if is_key_mod(NUMS[num], None) and not last_keys[NUMS[num]]:
                    self.audio_player.multiply_tracks(num)

            ## Change horizontal zoom level (pitch ranges)
            if is_key_mod(NUMS[1], None) and not last_keys[NUMS[1]]:
                range_width = self.pitch_range[1] - self.pitch_range[0]
                range_middle = self.pitch_range[1] - range_width // 2

                if range_width == PITCH_RANGE_SMALL:
                    new_range = PITCH_RANGE_LARGE
                else:
                    new_range = PITCH_RANGE_SMALL
                self.pitch_range = (
                        int(range_middle - new_range//2), 
                        int(range_middle + new_range//2)
                        )
                self.background_needs_update = True



        ## Articulating and continuing a note playing
        if self.b_left:
            if not self.audio_player.playing:
                self.audio_player.articulate()
            else:
                self.audio_player.settle_to_volume()
        
        ## Allowing a note to fade away when not left clicking
        if not self.b_left:
            self.audio_player.volume_decay()

        ## Identify the current scale by mouse position
        self.scale_index = (self.using_scales[0] + int(m_y / SCREEN_DIM[1] * len(self.using_scales))) %12
        self.scale = SCALES[self.scale_index]

        if (is_key_mod(K_A, None)):
            self.chord = V[:]
        elif (is_key_mod(K_S, None)):
            self.chord = I[:]
        elif (is_key_mod(K_D, None)):
            self.chord = IV[:]
        elif (is_key_mod(K_F, None)):
            self.chord = VIIb[:]
        elif (is_key_mod(K_A, SHIFT)):
            self.chord = V[:]
            self.chord.append((self.chord[0]+10)%12)
        elif (is_key_mod(K_S, SHIFT)):
            self.chord = I[:]
            self.chord.append((self.chord[0]+10)%12)
        elif (is_key_mod(K_D, SHIFT)):
            self.chord = IV[:]
            self.chord.append((self.chord[0]+10)%12)
        elif (is_key_mod(K_F, SHIFT)):
            self.chord = VIIb[:]
            self.chord[0] += 1
            self.chord[0] %= 12
            self.chord.append((self.chord[0]+9)%12)
        elif (is_key_mod(K_Q, None)):
            self.chord = III[:]
            self.chord[1] += 11# Make minor
            self.chord[1] %= 12# Make minor
        elif (is_key_mod(K_W, None)):
            self.chord = VI[:]
            self.chord[1] += 11# Make minor
            self.chord[1] %= 12# Make minor
        elif (is_key_mod(K_E, None)):
            self.chord = II[:]
            self.chord[1] += 11# Make minor
            self.chord[1] %= 12# Make minor
        elif (is_key_mod(K_R, None)):
            self.chord = V[:]
            self.chord[1] += 11# Make minor
            self.chord[1] %= 12# Make minor
        elif (is_key_mod(K_Q, SHIFT)):
            self.chord = III[:]
            self.chord.append((self.chord[0]+10)%12)
        elif (is_key_mod(K_W, SHIFT)):
            self.chord = VI[:]
            self.chord.append((self.chord[0]+10)%12)
        elif (is_key_mod(K_E, SHIFT)):
            self.chord = II[:]
            self.chord.append((self.chord[0]+10)%12)
        elif (is_key_mod(K_R, SHIFT)):
            self.chord = V[:]
            self.chord.append((self.chord[0]+10)%12)
        else:
            self.chord = None

        ## Temporarily align to the chord or chromatic scale on the current scale
        ## Self.scale will be put back after pitch decision making
        if self.chord != None:
            self.scale = [(self.scale[0] + c) % 12 for c in self.chord] # put chord in current scale key
        if (self.b_right):
            self.scale = CHROMATIC_SCALE


        ## Show and hide the instructions (really for QUESTION_MARK, but SLASH is more accepting)
        if (keys[SLASH] and not last_keys[SLASH]):
            self.instructions.minimized = not self.instructions.minimized

        #######################
        ## Pitch decisionmaking

        ## Get scale degree of closest pitch
        self.closest_pitch = sorted(self.scale, key=lambda x: min(abs((self.mouse_pitch%12)-x), 12 - abs((self.mouse_pitch%12)-x))) [0]
        ## Put closest pitch in correct octave
        while abs(self.closest_pitch - self.mouse_pitch) > 6:
            if self.closest_pitch > self.mouse_pitch:
                self.closest_pitch -= 12
            else:
                self.closest_pitch += 12
        ## Correct an error by rounding up if self.mouse_pitch > 11.5
        if abs(self.mouse_pitch - self.closest_pitch) > 10:
            self.closest_pitch += 12

        ## In case we switched scales for the chromatic scale, switch back now that we decided on a closest pitch
        self.scale = SCALES[self.scale_index]

        ## Decide whether to align to the closest pitch, or use the mouse pitch
        #if not last_b_middle:
        if self.b_left or self.audio_player.volume == 0: 
            if is_key_mod(K_PERIOD, None): 
                self.pitch = self.mouse_pitch
            else:
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
        self.metronome.paint_self(self.screen, self.audio_player.loop_buffer_index, -1 in self.audio_player.active_loops)
        ## Draw the loops
        y = 60
        x = 10
        w = self.metronome.measure_len * self.metronome.visual_buffer_width
        h = 30
        v_margin = 10
        for i in range(len(self.audio_player.loops)):
            loop = self.audio_player.loops[i]
            loop.paint_self(self.screen, (x,y,w,h), i in self.audio_player.active_loops, self.audio_player.loop_recording)
            y += h + v_margin
        ## Draw the instruction panel
        self.instructions.paint_self(self.screen)

        pygame.display.flip()
    
    '''
    Draws the active elements of a scale (row of notes) on the screen.
    '''
    def draw_scale_activity(self, scale, y, is_active):

        notes_to_draw = [rn for rn in self.recorded_notes_to_draw if rn.scale==scale]
        if self.scale == scale:
            notes_to_draw.append(RecordedNote(-1, self.pitch, self.audio_player.volume, None, self.scale, None, None))


        for p in range(self.pitch_range[0], self.pitch_range[1]+1):
            p_i = p % 12
            absolute_chord = None
            if self.chord:
                absolute_chord = [(scale[0] + c) % 12 for c in self.chord] # put chord in current scale key
            in_chord = absolute_chord and p_i in absolute_chord
            if p_i in scale or in_chord:
                color = ACTIVE_COLORS[p_i] if is_active and self.closest_pitch == p else INACTIVE_COLORS[p_i]
                x = self.pitch_to_coord(p, coord=0, reverse=False, scale=scale[0])
                
                ## Determine line width based on notes_to_draw:
                on_this_pitch = [rn for rn in notes_to_draw if rn.pitch == p]
                notes_to_draw = [rn for rn in notes_to_draw if not rn in on_this_pitch]
                if len(on_this_pitch) > 0 or in_chord:
                    sum_volume = sum(map(lambda rn: rn.get_loudness(), on_this_pitch))
                    line_width = max(INACTIVE_NOTE_WIDTH, int(sum_volume*ACTIVE_NOTE_STRETCH))
                    pygame.draw.line(self.screen, color, (x,y), (x,y+self.scale_height), line_width)
                    if get_font() and p_i == scale[0]:
                        l1 = get_font().render(NOTE_NAMES[p_i], 1, color)
                        self.screen.blit(l1, (x+10, y+self.scale_height-30))
                ## Autoharp chord black out notes
                if absolute_chord and p_i not in absolute_chord: # pitch in current scale, not in chord 
                    pygame.draw.line(self.screen, (0,0,0), (x,y), (x,y+self.scale_height), INACTIVE_NOTE_WIDTH)

        if is_active:
            color = INACTIVE_COLORS[scale[0]]
            pygame.draw.line(self.screen, color, (0,y), (SCREEN_DIM[0],y), 4) 
            pygame.draw.line(self.screen, color, (0,y+self.scale_height), (SCREEN_DIM[0],y+self.scale_height), 4)

        ## The remaining pitches in notes_to_draw are not on a bar
        for rn in notes_to_draw:
            line_width = max(INACTIVE_NOTE_WIDTH, int(rn.get_loudness() * ACTIVE_NOTE_STRETCH))
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
        pygame.draw.rect(screen, DARK_COLORS[scale[0]], (0,y,SCREEN_DIM[0],self.scale_height))
        pygame.draw.line(screen, SCALE_INACTIVE_SEPARATOR_COLOR, (0,y), (SCREEN_DIM[0],y), 1) 
        pygame.draw.line(screen, SCALE_INACTIVE_SEPARATOR_COLOR, (0,y+self.scale_height), (SCREEN_DIM[0],y+self.scale_height), 1)
        for p in range(self.pitch_range[0], self.pitch_range[1]+1):
            p_i = p % 12
            if p_i in scale:
                x = self.pitch_to_coord(p, coord=0, reverse=False, scale=scale[0])
                pygame.draw.line(screen, INACTIVE_COLORS[p_i], (x,y), (x,y+self.scale_height), INACTIVE_NOTE_WIDTH)
                if get_font() and p_i == scale[0]:
                    l1 = get_font().render(NOTE_NAMES[p_i], 1, INACTIVE_COLORS[p_i])
                    screen.blit(l1, (x+10, y+self.scale_height-30))

      
    def coord_to_pitch(self, y, coord=0, reverse=False):
        if reverse:
            return (self.pitch_range[1] - self.pitch_range[0]) / SCREEN_DIM[coord] * (SCREEN_DIM[coord] - y) + self.pitch_range[0]
        else:
            return (self.pitch_range[1] - self.pitch_range[0]) / SCREEN_DIM[coord] * y + self.pitch_range[0]

    def pitch_to_coord(self, p, coord=0, reverse=False, scale=None):
        if scale != None and self.audio_player.justify_pitch:
            p = pitch_to_just_pitch(p, scale)
        if reverse:
            return SCREEN_DIM[coord] - (p - self.pitch_range[0]) / (self.pitch_range[1] - self.pitch_range[0]) * SCREEN_DIM[coord]
        else:
            return (p - self.pitch_range[0]) / (self.pitch_range[1] - self.pitch_range[0]) * SCREEN_DIM[coord]
