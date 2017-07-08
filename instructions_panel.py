from constants import *

class InstructionsPanel:

    instruction_strings = [
        'Loopsichord Controls',
        '',
        'Basics',
        'Left click: Play a note',
        'Right click: Use chromatics',
        'Middle click: Center the mouse',
        'Scroll: Adjust volume',
        'S: Use sliding pitches',
        '',
        'Loop tracks',
        'Space: HOLD to record',
        'Up/Down: Select a track',
        'Shift-Up/Down: Select several tracks',
        'Backspace/Del: Delete track(s)',
        'M: Mute/unmute track(s)',
        'P: Mute/unmute all tracks',
        '+/-: Adjust volume of track(s)',
        'Ctrl-C: Copy track(s)',
        'A: Add tracks together',
        'Ctrl-Up/Down: Move track(s)',
        'Left/Right: Shift track(s) by beat',
        'Shift-Left/Right: Shift track(s)',
        '\n',
        'Metronome (when no track present)',
        'Left/Right: Increase track length',
        'Shift-Left/Right: Increase track beats',
        '',
        'Program',
        'Ctrl-S: Save the recorded tracks',
        'Esc: Quit',
        '?: Hide this help menu'
        ]

    minimized_instruction_string = "?: Show/Hide controls"

    def __init__(self):
        self.open_bounds = INSTRUCTIONS_BOUNDS_OPEN
        self.closed_bounds = INSTRUCTIONS_BOUNDS_CLOSED
        self.image = self.redraw_self()
        self.minimized_image = self.redraw_minimized_self()
        self.minimized = INSTRUCTIONS_START_CLOSED

    def paint_self(self, screen):
        if self.minimized:
            screen.blit(self.minimized_image, self.closed_bounds[:2])
        else:
            screen.blit(self.image, self.open_bounds[:2])
            screen.blit(self.minimized_image, self.closed_bounds[:2])

    def redraw_self(self):
        title_font = pygame.font.SysFont("Gentium", 36)
        header_font = pygame.font.SysFont("Gentium", 25)
        body_font = pygame.font.SysFont("Verdana", 16)
        screen = pygame.Surface(self.open_bounds[2:])
        screen.fill(INSTRUCTIONS_BACK_COLOR)
        y=10
        x=15
        for index, line in enumerate(self.instruction_strings):
            if ':' in line:
                font = body_font
                control, effect = line.split(':')
                control_image = font.render(control, 1, INSTRUCTIONS_FORE_COLOR, INSTRUCTIONS_BACK_COLOR)
                effect_image = font.render(effect, 1, INSTRUCTIONS_FORE_COLOR, INSTRUCTIONS_BACK_COLOR)
                screen.blit(control_image, (x,y))
                pygame.draw.rect(screen, INSTRUCTIONS_FORE_COLOR, (x-4,y+1,control_image.get_width()+8, control_image.get_height()), 1)
                screen.blit(effect_image, (x + 135,y))
                y+=effect_image.get_height()+3
            elif line == '\n':
                x += 350
                y = 70
            elif line != '':
                font = title_font if index==0 else header_font
                # font = header_font if line[0] == ' ' else body_font
                line_image = font.render(line, 1, INSTRUCTIONS_FORE_COLOR, INSTRUCTIONS_BACK_COLOR)
                screen.blit(line_image, (x-5,y)) 
                y+=line_image.get_height()+3
            else:
                y+=15
        return screen

    def paint_minimized_self(self, screen):
        screen.blit(self.minimized_image, self.closed_bounds[:2])

    def redraw_minimized_self(self):
        font = pygame.font.SysFont("Verdana", 16)
        control, effect = self.minimized_instruction_string.split(':')
        control_image = font.render(control, 1, INSTRUCTIONS_FORE_COLOR, INSTRUCTIONS_BACK_COLOR)
        effect_image = font.render(effect, 1, INSTRUCTIONS_FORE_COLOR, INSTRUCTIONS_BACK_COLOR)
        screen = pygame.Surface(self.closed_bounds[2:])
        screen.fill(INSTRUCTIONS_BACK_COLOR)
        screen.blit(control_image, (10,10))
        pygame.draw.rect(screen, INSTRUCTIONS_FORE_COLOR, (10-4,10,control_image.get_width()+8, control_image.get_height()+1), 1)
        screen.blit(effect_image, (60,10))
        return screen




