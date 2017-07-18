from constants import *
from math import ceil


class OvertonePanel:

    def __init__(self, overtones):
        self.image = None
        self.image_needs_update = True
        self.overtones = overtones

    def paint_self(self, screen, rect):
        (x,y,w,h) = rect
        if self.image == None or self.image_needs_update:
            self.image = self.redraw_self(w,h)
        screen.blit(self.image, (x,y,w,h))
        #pygame.draw.rect(screen, ACTIVE_LOOP_OUTLINE_COLOR, rect, 1)

    def redraw_self(self, w, h):
        self.image_needs_update = False
        screen = pygame.Surface((w,h), pygame.SRCALPHA, 32)
        screen = screen.convert_alpha()
        bar_buffer = 2
        bar_width = min(5, w / 2 / len(self.overtones) - bar_buffer)
        for i,o in enumerate(self.overtones):
            x = (bar_width+bar_buffer)*i 
            bar_height = ceil(h * o)
            y = h - bar_height
            pygame.draw.rect(screen, OVERTONE_COLOR, (x,y,bar_width, bar_height))
        ## Draw sin
        x = w//2
        y_list, _ = sin(1, sample_count=w//2, fs=w//2, overtones=self.overtones)
        for i,y in enumerate(y_list):
            print(y,i)
            if i == len(y_list)-1:
                break
            this_y = y*h/4 + h/2
            next_y = y_list[i+1]*h/4 + h/2
            pygame.draw.line(screen, OVERTONE_COLOR, (x,this_y),(x+1,next_y))
            x+=1

        return screen
