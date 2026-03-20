import pygame
import sys
import os
from pygame import font
from pygame.draw import rect

from screen2_DELETE import Screen2

# Constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # directory of this script


class Winner:
    def __init__(self):
        pygame.init()

        # window size full screen 
        self.width, self.height = pygame.display.get_desktop_sizes()[0]
        self.screen = pygame.display.set_mode(size=(self.width, self.height - 60))
        # bit smaller for title bar and bottom icons
    
        
        pygame.display.set_caption("Beyond")
        self.small_font = pygame.font.Font(size=190)
        self.clock = pygame.time.Clock()
        self.running = True
     
        # Colors
        #red, green, blue
        self.bg_color = (79, 79, 79)
        self.text_color = (154, 205, 50)

        self.decoration_images = [
            ('sprite1.png', 1295, 550, 0, 8),
            ('Grass.png', 942, 491, -15, 2.6999999999999997),
            ('Grass_Pine.png', 200, 350, -15, 3.4000000000000004),
            ('Magic_Crystals.png', 270, 448, 20, 3.2),
            ('FrosenWater_Lilypads.png', 140, 460, 10, 2.1999999999999993),
            ('Magic.png', 849, 474, -20, 1.9000000000000006),
            ('Snow_Trees.png', 913, 378, 15, 3.0)
        ]

    
    def draw(self):
        """
        Draw the welcome screen with title and images.
        Input: None
        Output: None
        """
        self.screen.fill(self.bg_color)

        # text
        pygame.font.init()
        font = pygame.font.Font(os.path.join(BASE_DIR, '..', 'assets', 'fonts', 'Jersey10-Regular.ttf'), size=210)

        text = font.render("Winner!", antialias=True, color=self.text_color)
        rect = text.get_rect(midtop=(1/4 * self.width + 200, self.height // 4)) # middle
        self.screen.blit(source=text, dest=rect) 
        
        # images
        for image_name, x, y, angle, scale in self.decoration_images:
            self.draw_image(image_name, x, y, angle, scale)

        pygame.display.flip()
        

    

    def draw_image(self, image_name: str, x: int, y: int, angle: int, scale: float):
        """
        draw image on the screen
        Inputs:
            image_name(str): name of the image file 
            x(int): x position
            y(int): y position
            angle(int): rotation angle in degrees
            scale(float): scaling factor (e.g., 0.5 for half size, 2 for double size)
        Output: None
        """
        # path
        if "sprite1" in image_name:
            castle_image_path = os. path.join(BASE_DIR, '..', 'assets', 'assetBank', 'Castles', image_name)
            image = pygame.image.load(castle_image_path)
        else:
            hex_image_path = os. path.join(BASE_DIR, '..', 'assets', 'assetBank', 'Hex Tiles', image_name)
            image = pygame.image.load(hex_image_path)

        # adjust image
        original_w, original_h = image.get_size()
        scaled_image = pygame.transform.scale(image, (int(original_w * scale), int(original_h * scale)))
        rotated_image = pygame.transform.rotate(scaled_image, angle)
        rect = rotated_image.get_rect(center=(x, y))
        self.screen.blit(rotated_image, rect)
        
    
   
    # main loop for testing
    def run(self):
        #milliseconds since pygame.init() was called
        start_time = pygame.time.get_ticks()  # record start time

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
            
            # # time open
            # elapsed_time = (pygame.time.get_ticks() - start_time) / 1000
            # if elapsed_time >= 4:  # after 7 seconds, exit
            #     self.running = False
                       
            self.draw()
            self.clock.tick(80)
        
        pygame.quit()

if __name__ == "__main__":
    winner_screen = Winner()
    winner_screen.run()


    