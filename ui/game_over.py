import pygame
import sys
import os
from pygame import font
from pygame.draw import rect


import ui.button
from ui.base_screen import Screen


# Constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # directory of this script

class GameOver(Screen):
    def __init__(self, manager):
        super().__init__(manager)
    
        self.decoration_images = [
            # upsidedown castle
            ('sprite1.png', 1295, 450, 180, 8),
            
        ]

        self.buttons = self.create_buttons()
        
    def create_buttons(self):
        # 1 button on this screen
        button_height = 50
        button_width = 150
        button_font = pygame.font.Font(os.path.join(BASE_DIR, '..', 'assets', 'fonts', 'Jersey10-Regular.ttf'), size=30)
        x = ((self.manager.width / 3) + 50) - (button_width / 2)
        y = (self.manager.height / 2) - (button_height/ 2)
    
        # create the button
        play_again_button = ui.button.Button(
            x,      
            y,    
            button_width,
            button_height,
            "PLAY AGAIN", # text on the button
            button_font,
            action_name ="play_again",
            bg_color = (175, 143, 233),
            hover_color = (120, 100, 160),
            text_color = self.manager.text_color_white,
        )

        return [play_again_button]
    


    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.manager.switch_screen("main_menu")

        mouse_position = pygame.mouse.get_pos()
        for button in self.buttons:
            button.check_hover(mouse_position)
            action = button.handle_event(event)
            if action == "play_again":
                self.manager.switch_screen("main_menu")


    def draw(self):
        """
        Draw the welcome screen with title and images.
        Input: None
        Output: None
        """
        self.manager.screen.fill(self.manager.bg_color) #fill covers the previous screen

        # text
        pygame.font.init()
        font = pygame.font.Font(os.path.join(BASE_DIR, '..', 'assets', 'fonts', 'Jersey10-Regular.ttf'), size=210)

        text = font.render("Game Over!", True, self.manager.text_color_green)
        rect = text.get_rect(midtop=(1/4 * self.manager.width + 200, self.manager.height // 4)) # middle
        self.manager.screen.blit(source=text, dest=rect) 
        
        # images
        for image_name, x, y, angle, scale in self.decoration_images:
            self.draw_image(image_name, x, y, angle, scale)

        for button in self.buttons:
            button.draw(self.manager.screen)

    
    
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
        

        
       
    