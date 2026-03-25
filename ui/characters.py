import pygame
import sys
import os
from pygame import font
from pygame.draw import rect


import button
from base_screen import Screen


# Constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # directory of this script


class Characters(Screen):
    def __init__(self, manager):
        super().__init__(manager)
     
        # Colors
        #red, green, blue
        self.bg_color = (79, 79, 79)
        self.text_color = (154, 205, 50)

        self.decoration_images = [
            # right
            ('Snow_Trees.png', 1150, 49, -10, 2.8),
            ('Grass_Pine.png', 1110, 183, 10, 2), 
            ('Grass_Plants2.png',1210, 130, 0, 2.0),

            # left
            ('Grass.png', 328, 167, 15, 1.9),
            ('Water_Duck.png', 437, 190, -10, 3.0),
            ('Magic_Crystals.png', 400, 60, -10, 3.0),

        ]

        self.character_images = [ os.path.join("Adviser", "Adviser_Attack_1.png"),
                                    os.path.join("Adviser", "Adviser_Attack_1.png"),
                                    os.path.join("Adviser", "Adviser_Attack_1.png"),
                                    os.path.join("Adviser", "Adviser_Attack_1.png"),
                                    os.path.join("Adviser", "Adviser_Attack_1.png"),
                                    os.path.join("Adviser", "Adviser_Attack_1.png"),
                                    os.path.join("Adviser", "Adviser_Attack_1.png"),
                                    os.path.join("Adviser", "Adviser_Attack_1.png")]
        
       

        self.button_names = ["character_1", "character_2", "character_3", "character 4", "Character_5", "character_6", "character_8", "character_9"]
        self.buttons = self.create_buttons()


    def handle_event(self, event):
        mouse_position = pygame.mouse.get_pos()
        for button in self.buttons:
            button.check_hover(mouse_position)
            action = button.handle_event(event)
            if action == "character_1":
                self.manager.switch_screen("game_rules")    
    
    def create_buttons(self):
        buttons = []

        button_height = 45
        button_width = 250
        button_font = pygame.font.Font(
            os.path.join(BASE_DIR, '..', 'assets', 'fonts', 'Jersey10-Regular.ttf'),
            size=30
        )

        # GRID SETTINGS
        cols = 4      # 4 per row
        rows = 2      # 2 rows
        gap_x = 350   # horizontal spacing
        gap_y = 300   # vertical spacing

        # Starting point (center the whole grid)
        grid_width = (cols - 1) * gap_x
        start_x = self.manager.width // 2 - grid_width // 2
        start_y = 500   # move grid down

        for index, button_name in enumerate(self.button_names):
            row = index // cols
            col = index % cols

            # Position for each button
            x = start_x + col * gap_x - button_width // 2
            y = start_y + row * gap_y

            btn = button.Button(
                x,
                y,
                button_width,
                button_height,
                "SELECT",
                button_font,
                action_name=button_name,
                bg_color=self.bg_color,
                hover_color=(120, 100, 160),
                text_color=(255, 255, 255),
            )

            buttons.append(btn)

        return buttons

    
    def draw(self):
        """
        Draw the welcome screen with title and images.
        Input: None
        Output: None
        """
        self.manager.screen.fill(self.bg_color) #fill covers the previous screen

        # text
        pygame.font.init()
        font = pygame.font.Font(os.path.join(BASE_DIR, '..', 'assets', 'fonts', 'Jersey10-Regular.ttf'), size=150)

        text = font.render("CHARACTERS", True, self.text_color)
        position = self.manager.width // 2, 130
        rect = text.get_rect(center=position) 
        self.manager.screen.blit(source=text, dest=rect) 
        
        # title images
        for image_name, x, y, angle, scale in self.decoration_images:
            self.draw_image(image_name, x, y, angle, scale)

        #character images
        # character images directly above buttons
        vertical_offset = 90  # perfect for 150px characters + 45px buttons

        for img_name, btn in zip(self.character_images, self.buttons):
            char_x = btn.rect.x + btn.rect.width // 2
            char_y = btn.rect.y - vertical_offset
            self.draw_character(img_name, char_x, char_y)

        
        # buttons
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
        hex_image_path = os. path.join(BASE_DIR, '..', 'assets', 'assetBank', 'Hex Tiles', image_name)
        image = pygame.image.load(hex_image_path)
        


        # adjust image
        original_w, original_h = image.get_size()
        scaled_image = pygame.transform.scale(image, (int(original_w * scale), int(original_h * scale)))
        rotated_image = pygame.transform.rotate(scaled_image, angle)
        rect = rotated_image.get_rect(center=(x, y))
        self.manager.screen.blit(rotated_image, rect)


    def draw_character(self, image_name, x, y):
        path = os.path.join(BASE_DIR, "..", "assets", "assetBank", "Classic China Characters", image_name)
        image = pygame.image.load(path).convert_alpha()

        # Optional: scale characters to a consistent size
        original_w, original_h = image.get_size()
        image = pygame.transform.scale(image, (int(original_w * 8), int(original_h * 8)))

        rect = image.get_rect(center=(x, y))
        self.manager.screen.blit(image, rect)
                