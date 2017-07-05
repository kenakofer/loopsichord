#!/usr/bin/env python3

import pygame
from constants import *
from music_maker import *
from tkinter import Tk

def main():

    # initialize game engine
    pygame.init()
    
    # set screen width/height and caption
    screen = pygame.display.set_mode(SCREEN_DIM)
    pygame.display.set_caption('Some digital instrument thing')
    print(pygame.font.get_init())
    root = Tk()
    root.withdraw() # won't need this
    while get_font() == None:
        init_font()
    MusicMaker(screen)

    # close the window and quit
    pygame.quit()
    print("Finished.")

if __name__ == '__main__':
    main()

