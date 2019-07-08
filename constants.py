import pygame
import pygame.image
import numpy as np
from math import log
import os


LAYOUT_DVORAK = True
FS = 44100
BUFFER_SIZE = 1024
BUFFERS_PER_MEASURE = 160
VISUAL_BUFFER_WIDTH = 1.5
#SCREEN_DIM = (1800,600)              #Dimensions of the window
SCREEN_DIM = [1100,600]              #Dimensions of the window
INSTRUCTIONS_PADDING = 10
INSTRUCTIONS_BOUNDS_OPEN = [SCREEN_DIM[0] - 750 - INSTRUCTIONS_PADDING, INSTRUCTIONS_PADDING, 750, SCREEN_DIM[1]-2*INSTRUCTIONS_PADDING]
INSTRUCTIONS_BOUNDS_CLOSED = [SCREEN_DIM[0] - 250 - INSTRUCTIONS_PADDING, INSTRUCTIONS_PADDING, 250, 40]
MIN_DIM = [640, 600]
INSTRUCTIONS_START_CLOSED = True
PITCH_SPEED = .02
PITCH_RANGE = (-4, 24)
VOLUME = .005
ARTICULATION_FACTOR = 2.5
ARTICULATION_DECAY = .1
LOOP_MAX_VOLUME = 10
CUTOFF = .01
REVERB = .9
assert ARTICULATION_DECAY > 0
assert REVERB < 1

def update_screen_size(DIM):
    global SCREEN_DIM, INSTRUCTIONS_BOUNDS_OPEN, INSTRUCTIONS_BOUNDS_CLOSED
    SCREEN_DIM[:] = DIM
    INSTRUCTIONS_BOUNDS_OPEN[:] = [SCREEN_DIM[0] - 750 - INSTRUCTIONS_PADDING, INSTRUCTIONS_PADDING, 750, SCREEN_DIM[1]-2*INSTRUCTIONS_PADDING]
    INSTRUCTIONS_BOUNDS_CLOSED[:] = [SCREEN_DIM[0] - 250 - INSTRUCTIONS_PADDING, INSTRUCTIONS_PADDING, 250, 40]

SCALES = [
            #list(range(12)),
            [0,2,4,5,7,9,11],  # A 440 Major
            [5,7,9,10,0,2,4],  # D
            [10, 0,2,3,5,7,9], # G
            [3,5,7,8,10,0,2],  # C
            [8,10,0,1,3,5,7],  # F
            [1,3,5,6,8,10,0],  # Bb
            [6,8,10,11,1,3,5], # Eb
            [11,1,3,4,6,8,10], # Ab 
            [4,6,8,9,11,1,3],  # Db 
            [9,11,1,2,4,6,8],  # Gb 
            [2,4,6,7,9,11,1],  # B 
            [7,9,11,0,2,4,6],  # E
        ]
NOTE_NAMES = ['A','Bb','B','C','Db','D','Eb','E','F','Gb','G','Ab']

CHROMATIC_SCALE = list(range(0,12))

METRONOME_RELATIVE_VOLUME = 5 ## Relative to VOLUME
INACTIVE_NOTE_WIDTH = 3
ACTIVE_NOTE_STRETCH = 1600
LOOP_VISUAL_NOTE_STRETCH = 500

INACTIVE_COLORS = [
        (64,0,100), #A
        (70,0,70),
        (100,0,64),
        (127,0,0), #C
        (100,64,0),
        (70,70,0),
        (64,100,0), 
        (0,127,0),
        (0,100,64), #F
        (0,70,70),
        (0,64,100),
        (0,0,127),
        ]

ACTIVE_COLORS = [
        (c[0]+100, c[1]+100, c[2]+100) for c in INACTIVE_COLORS
        ]

DARK_COLORS = [
        (c[0]//4, c[1]//4, c[2]//4) for c in INACTIVE_COLORS
        ]

SATURATED_COLORS = [
        (c[0]*2, c[1]*2, c[2]*2) for c in INACTIVE_COLORS
        ]

INSTRUCTIONS_BACK_COLOR = (50,50,80)
INSTRUCTIONS_FORE_COLOR = (200,200,255)
FREE_NOTE_COLOR = (150,150,150)
ACTIVE_LOOP_OUTLINE_COLOR = (255,255,200)
#LOOP_BACK_COLOR = (50,50,50)
ACTIVE_LOOP_BACK_COLOR = INSTRUCTIONS_BACK_COLOR
INACTIVE_LOOP_BACK_COLOR = (100,100,110)
LOOP_RECORDING_BACK_COLOR = (0,0,80)
LOOP_PITCH_COLOR = (255,0,0)
LOOP_MUTED_PITCH_COLOR = (255,255,255)
METRONOME_ACTIVE_COLOR = (255,255,255)
#METRONOME_INACTIVE_COLOR = (100,100,100)
METRONOME_INACTIVE_COLOR = (80,80,90)
SCALE_ACTIVE_SEPARATOR_COLOR = (255,255,200) 
SCALE_INACTIVE_SEPARATOR_COLOR = (50,50,50)


def get_color(scale_index, spectrum):
    scale_index %= 12
    if scale_index == int(scale_index):
        return spectrum[int(scale_index)]
    else:
        color1 = spectrum[int(scale_index)]
        color2 = spectrum[int(scale_index+1)%12]
        weight2 = scale_index % 1
        weight1 = 1 - weight2
        r,g,b = (color1[0]*weight1 + color2[0]*weight2, color1[1]*weight1 + color2[1]*weight2, color1[2]*weight1 + color2[2]*weight2)
        return (int(r), int(g), int(b))


ACTION_CHANGE_NOTE = 0
ACTION_RELEASE_NOTE = 1
ACTION_ARTICULATE_NOTE = 2
ACTION_STOP_LOOP_REC = 3
ACTION_START_LOOP_REC = 4
ACTION_START_LOOP_PLAY = 5
ACTION_STOP_LOOP_PLAY = 6

NEXT_BUFFER = 100
NEXT_BEAT = 101
NEXT_MEASURE = 102

BEGIN_STEP = 200
END_STEP = 201




EVENT_CHANGE_NOTE = (ACTION_CHANGE_NOTE, NEXT_BUFFER, BEGIN_STEP)
EVENT_RELEASE_NOTE = (ACTION_RELEASE_NOTE, NEXT_BUFFER, BEGIN_STEP)
EVENT_ARTICULATE_NOTE = (ACTION_ARTICULATE_NOTE, NEXT_BUFFER, BEGIN_STEP)

EVENT_START_LOOP_REC = (ACTION_START_LOOP_REC, NEXT_BUFFER, END_STEP)
EVENT_STOP_LOOP_REC = (ACTION_STOP_LOOP_REC, NEXT_BUFFER, BEGIN_STEP)
EVENT_START_LOOP_PLAY = (ACTION_START_LOOP_PLAY, NEXT_BUFFER, END_STEP)
EVENT_STOP_LOOP_PLAY = (ACTION_STOP_LOOP_PLAY, NEXT_BUFFER, BEGIN_STEP)


font=None
def init_font():
    global font
    font = pygame.font.SysFont("Arial", 20)

def get_font():
    return font

#def volume_factor_by_freq(freq):
def loud_to_volume(loud, freq):
    return loud*1000/((freq+5)**.75)
def volume_to_loud(volume, freq):
    return volume * ((freq+5)**.75) / 1000

BEAT_LEN = 30

BACK_COLOR = (20,20,20)


def musical_pitch_to_hertz(mp, justify_by_scale=None):
    if justify_by_scale == None:
        ## Use equal temperament that places A4 at 440 hertz
        return (2**(mp/12)) * 440.0
    else:
        ## Use just diatonic scale (notes that give just major triads on I, IV, V) See https://en.wikipedia.org/wiki/Just_intonation#Diatonic_scale
        p_i = (mp - justify_by_scale) % 12
        tonic_pitch = mp - p_i
        tonic_freq = musical_pitch_to_hertz(tonic_pitch, justify_by_scale=None)
        just_semitone_factor = {0:1, 2:9/8, 4:5/4, 5:4/3, 7:3/2, 9:5/3, 11:15/8}
        if p_i in just_semitone_factor:
            return tonic_freq * just_semitone_factor[p_i]
        else:
            return musical_pitch_to_hertz(mp, justify_by_scale=None)

'''
Given a pitch (integer) and a scale tonic, give the floating point pitch index of where the justified pitch would be in that scale
'''
def pitch_to_just_pitch(pitch, tonic):
        freq = musical_pitch_to_hertz(pitch, justify_by_scale=tonic)
        just_pitch = 12 * log(freq/440, 2)
        return just_pitch

def sin(freq, sample_count=FS, fs=FS, volume=1, previous_volume=1, percent_through_period=0, overtones=[1]):
    count = sample_count
    samples = [
        (overtones[i] * np.sin(2*np.pi*np.arange(count)*freq*(i+1)/fs + percent_through_period*2*np.pi*(i+1))).astype(np.float32)
        for i in range(len(overtones))
        ]
    new_ptp = (percent_through_period + count*freq/fs) % 1
    samples = np.sum(samples, axis=0)
    samples *= np.linspace(previous_volume, volume, num=count)
    samples = samples.astype(np.float32)
    return  samples, new_ptp

#MY_OVERTONES = [1, .940, .425, .480, 0, .365, .040, .085, 0, .090]
#MY_OVERTONES = [1, .50, .425, 0, .4, 0, .040, .085, .05 ]
MY_OVERTONES = [1, .50, .425, 0, .4, 0, .040]

################
#INDEX CONSTANTS
RIGHT   =pygame.K_RIGHT
DOWN    =pygame.K_DOWN
LEFT    =pygame.K_LEFT
UP      =pygame.K_UP
SPACE      =pygame.K_SPACE
RETURN  =pygame.K_RETURN
CTRL    =pygame.KMOD_CTRL
ALT     =pygame.KMOD_ALT
SHIFT   =pygame.KMOD_SHIFT
BACKSPACE = pygame.K_BACKSPACE
DELETE  = pygame.K_DELETE
ESCAPE  = pygame.K_ESCAPE
EQUALS  = pygame.K_EQUALS
EQUALS  = pygame.K_EQUALS
PLUS = pygame.K_PLUS
KP_PLUS = pygame.K_KP_PLUS
MINUS   = pygame.K_MINUS
KP_MINUS = pygame.K_KP_MINUS
SLASH   = pygame.K_SLASH
NUMS = [pygame.K_0, pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9]

def is_key_mod(key, mod=None):
    if mod == None:
        return keys[key] and pygame.key.get_mods() == 0
    else:
        return keys[key] and pygame.key.get_mods() & mod

if not LAYOUT_DVORAK:
    K_A     =pygame.K_a
    K_B     =pygame.K_b
    K_C     =pygame.K_c
    K_D     =pygame.K_d
    K_E     =pygame.K_e
    K_F     =pygame.K_f
    K_G     =pygame.K_g
    K_H     =pygame.K_h
    K_I     =pygame.K_i
    K_J     =pygame.K_j
    K_K     =pygame.K_k
    K_L     =pygame.K_l
    K_M     =pygame.K_m
    K_N     =pygame.K_n
    K_O     =pygame.K_o
    K_P     =pygame.K_p
    K_Q     =pygame.K_q
    K_R     =pygame.K_r
    K_S     =pygame.K_s
    K_T     =pygame.K_t
    K_U     =pygame.K_u
    K_V     =pygame.K_v
    K_W     =pygame.K_w
    K_X     =pygame.K_x
    K_Y     =pygame.K_y
    K_Z     =pygame.K_z
else:
    K_A     =pygame.K_a
    K_B     =pygame.K_x
    K_C     =pygame.K_j
    K_D     =pygame.K_e
    K_E     =pygame.K_PERIOD
    K_F     =pygame.K_u
    K_G     =pygame.K_i
    K_H     =pygame.K_d
    K_I     =pygame.K_c
    K_J     =pygame.K_h
    K_K     =pygame.K_t
    K_L     =pygame.K_n
    K_M     =pygame.K_m
    K_N     =pygame.K_b
    K_O     =pygame.K_r
    K_P     =pygame.K_l
    K_Q     =pygame.K_QUOTE
    K_R     =pygame.K_p
    K_S     =pygame.K_o
    K_T     =pygame.K_y
    K_U     =pygame.K_g
    K_V     =pygame.K_k
    K_W     =pygame.K_COMMA
    K_X     =pygame.K_q
    K_Y     =pygame.K_f
    K_Z     =pygame.K_SEMICOLON
    K_PERIOD=pygame.K_v



#Initializations
keys=[]
MOUSEPOS = [-1,-1]


