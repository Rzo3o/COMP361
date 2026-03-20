import pygame
import sys
import os
from pygame.draw import rect

from screen2_DELETE import Screen2
from ui.screen import Screen

# Constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # directory of this script


class Welcome(Screen):
    def __init__(self):
        pygame.init()

        # window size full screen 
        self.width, self.height = pygame.display.get_desktop_sizes()[0]
        self.screen = pygame.display.set_mode(size=(self.width, self.height - 60))
        # bit smaller for title bar and bottom icons
    
        
        pygame.display.set_caption("Beyond")
        self.clock = pygame.time.Clock()
        self.running = True
     
        # Colors
        #red, green, blue
        self.bg_color = (79, 79, 79)
        self.text_color = (154, 205, 50)

        # (image name, x, y , anngle, scale)
        self.decoration_images = [
            ('Water_Duck.png', 98, 68, 30, 4.7),
            ('Dirt_Pumpkins.png', 166, 372, 25, 3.7),
            ('Grass_Plants.png', 94, 247, 60, 2.8),
            ('Snow_Trees.png', 1270, 587, 25, 4.1),
            ('Magic_Crystals.png', 1421, 614, 40, 2.8),
            ('FrosenWater_Lilypads.png', 1297, 732, 20, 2.9),
            ('Magic.png', 265, 152, 20, 2.5),
            ('Snow.png', 286, 273, 35, 4.0),
            ('Grass_Plants2.png', 1452, 776, 30, 4.3)
        ]

        self.texts = [
            "Welcome",
            "Beyond"
        ]
        
    
    def draw(self):
        """
        Draw the welcome screen with title and images.
        Input: None
        Output: None
        """
        self.screen.fill(self.bg_color)

        self.draw_title()
        
        # images
        for image_name, x, y, angle, scale in self.decoration_images:
            self.draw_image(image_name, x, y, angle, scale)

        pygame.display.flip()
        

    def draw_title(self):
        """
        draw title on the screen
        Input: None
        Output: None
        """
        pygame.font.init()
        font = pygame.font.Font(os.path.join(BASE_DIR, '..', 'assets', 'fonts', 'Jersey10-Regular.ttf'), size=210)
        

        rendered_texts = []
        for text in self.texts:
            text = font.render(text, antialias=True, color=self.text_color)
            rendered_texts.append(text)

        spacing = -70
        total_text_height = 0

        for ren_text in rendered_texts:
            total_text_height += ren_text.get_height()
            
        total_text_height += spacing * (len(rendered_texts) - 1) 

        y_offset = (self.height - total_text_height) // 2

        # blit each line
        for text in rendered_texts:
            rect = text.get_rect(midtop=(self.width // 2, y_offset)) # middle
            self.screen.blit(source=text, dest=rect) 
            y_offset += text.get_height() + spacing
    

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
        image_path = os. path.join(BASE_DIR, '..', 'assets', 'assetBank', 'Hex Tiles', image_name)
        
        image = pygame.image.load(image_path)
        
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
            
            # time open
            #elapsed_time = (pygame.time.get_ticks() - start_time) / 1000
            #if elapsed_time >= 4:  
                #self.running = False
                       
            self.draw()
            self.clock.tick(80)
        
        pygame.quit()

if __name__ == "__main__":
    welcome_screen = Welcome()
    welcome_screen.run()

    #screen_2 = Screen2()
    #screen_2.run()



    