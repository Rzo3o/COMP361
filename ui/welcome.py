import pygame
import sys
import os
from pygame.draw import rect

from ui.base_screen import Screen

# Constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # directory of this script

class Welcome(Screen):
    def __init__(self, manager):
        super().__init__(manager)
    
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
            "WELCOME",
            "BEYOND"
        ]
    
    def handle_event(self, event):    
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.manager.switch_screen("characters")    
    
    def draw(self):
        """
        Draw the welcome screen with title and images.
        Input: None
        Output: None
        """
        self.manager.screen.fill(self.manager.bg_color) # fill backgroud 

        self.draw_title()
        
        # images
        for image_name, x, y, angle, scale in self.decoration_images:
            self.draw_image(image_name, x, y, angle, scale)

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
            text = font.render(text, True, self.manager.text_color_green)
            rendered_texts.append(text)

        spacing = -70
        total_text_height = 0

        for ren_text in rendered_texts:
            total_text_height += ren_text.get_height()
            
        total_text_height += spacing * (len(rendered_texts) - 1) 

        y_offset = (self.manager.height - total_text_height) // 2

        # blit each line
        for text in rendered_texts:
            rect = text.get_rect(midtop=(self.manager.width // 2, y_offset)) # middle
            self.manager.screen.blit(source=text, dest=rect) 
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
        self.manager.screen.blit(rotated_image, rect)

   
  