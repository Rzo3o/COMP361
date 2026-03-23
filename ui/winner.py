import pygame
import sys
import os
from pygame import font
from pygame.draw import rect


from base_screen import Screen


# Constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # directory of this script


class Winner(Screen):
    def __init__(self, manager):
        super().__init__(manager)
     
        # Colors
        #red, green, blue
        self.bg_color = (79, 79, 79)
        self.text_color = (154, 205, 50)

        self.decoration_images = [
            ('sprite1.png', 1295, 550, 0, 8),
            ('Grass.png', 942, 491, -15, 2.6),
            ('Grass_Pine.png', 200, 350, -15, 3.4),
            ('Magic_Crystals.png', 270, 448, 20, 3.2),
            ('FrosenWater_Lilypads.png', 140, 460, 10, 2.2),
            ('Magic.png', 849, 474, -20, 1.9),
            ('Snow_Trees.png', 913, 378, 15, 3.0)
        ]

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.manager.switch_screen("game_rules")

    def draw(self):
        """
        Draw the welcome screen with title and images.
        Input: None
        Output: None
        """
        self.manager.screen.fill(self.bg_color) #fill covers the previous screen

        # text
        pygame.font.init()
        font = pygame.font.Font(os.path.join(BASE_DIR, '..', 'assets', 'fonts', 'Jersey10-Regular.ttf'), size=210)

        text = font.render("Winner!", True, self.text_color)
        rect = text.get_rect(midtop=(1/4 * self.manager.width + 200, self.manager.height // 4)) # middle
        self.manager.screen.blit(source=text, dest=rect) 
        
        # images
        for image_name, x, y, angle, scale in self.decoration_images:
            self.draw_image(image_name, x, y, angle, scale)

    
    
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
        self.manager.screen.blit(rotated_image, rect)
        

    