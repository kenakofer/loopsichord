from constants import *

class InstructionsPanel:

    instruction_strings = [
        'Loopsichord Controls',
        '',
        ' Basics',
        'Left click: Sound a note',
        'Right click: Use chromatics',
        'Middle click: Center the mouse',
        'Scroll: adjust Volume',
        'S: use sliding Pitches',
        '',
        ' Looping',
        'Space: Hold to record on a new track',
        'Up/Down: Select a track',
        'Backspace/Del: Delete a track',
        'M: Mute/unmute a track',
        'P: Mute/unmute all tracks',
        'Shift-Up/Down: Adjust volume of track',
        'Ctrl-C: Copy a track',
        '+: Add a track to the one below',
        'Ctrl-Up/Down: Move a track',
        'Left/Right: Shift a track by beat',
        'Shift-Left/Right: Shift a track',
        '',
        ' Metronome (when no loops are present)',
        'Left/Right: Increase loop length',
        'Shift-Left/Right: Increase loop beats',
        '',
        ' Program',
        'Ctrl-S: Save the recorded tracks',
        'Esc: Quit',
        '?: Show/hide controls'
        ]

    def __init__(self, x, y, w,h):
        self.x = x
        self.y = y
        self.width = w
        self.height = h
        self.image = self.redraw_self()
        self.minimized_image = self.redraw_minimized_self()

    def paint_self(self, screen):
        screen.blit(self.image, (self.x, self.y))

    def redraw_self(self):
        font = pygame.font.SysFont("Verdana", 12)
        screen = pygame.Surface((self.width, self.height))
        screen.fill(INSTRUCTIONS_BACK_COLOR)
        y=10
        for line in self.instruction_strings:
            if not ':' in line:
                line_image = font.render(line, 1, INSTRUCTIONS_FORE_COLOR, INSTRUCTIONS_BACK_COLOR)
                screen.blit(line_image, (10,y)) 
                y+=line_image.get_height()+2
            else:
                control, effect = line.split(':')
                control_image = font.render(control, 1, INSTRUCTIONS_FORE_COLOR, INSTRUCTIONS_BACK_COLOR)
                effect_image = font.render(effect, 1, INSTRUCTIONS_FORE_COLOR, INSTRUCTIONS_BACK_COLOR)
                screen.blit(control_image, (10,y))
                pygame.draw.rect(screen, INSTRUCTIONS_FORE_COLOR, (10-4,y,control_image.get_width()+8, control_image.get_height()+1), 1)
                screen.blit(effect_image, (130,y))
                y+=effect_image.get_height()+2
        return screen

    def paint_minimized_self(self, screen):
        screen.blit(self.minimized_image, (self.x, self.y))

    def redraw_minimized_self(self):
        font = pygame.font.SysFont("Verdana", 14)
        control, effect = self.instruction_strings[-1].split(':')
        control_image = font.render(control, 1, INSTRUCTIONS_FORE_COLOR, INSTRUCTIONS_BACK_COLOR)
        effect_image = font.render(effect, 1, INSTRUCTIONS_FORE_COLOR, INSTRUCTIONS_BACK_COLOR)
        screen = pygame.Surface((self.width, effect_image.get_height()+20))
        screen.fill(INSTRUCTIONS_BACK_COLOR)
        screen.blit(control_image, (10,10))
        pygame.draw.rect(screen, INSTRUCTIONS_FORE_COLOR, (10-4,10,control_image.get_width()+8, control_image.get_height()+1), 1)
        screen.blit(effect_image, (130,10))
        return screen




