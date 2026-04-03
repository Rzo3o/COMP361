import pygame
import sys
import os
from pygame import font
from pygame.draw import rect

import ui.button
from ui.base_screen import Screen
from database.db_manager import DatabaseManager

# Constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # directory of this script

class Characters(Screen):
    def __init__(self, manager):
        super().__init__(manager)
     
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

        self.character_images = [   os.path.join("Heavy_Cavalry", "Heavy_Cavalry_Attack_1.png"),
                                    os.path.join("Archer", "Archer_Attack_1.png"),
                                    os.path.join("Cavalry", "Cavalry_Attack_1.png"),
                                    os.path.join("Heavy_Archer", "Heavy_Archer_Attack_1.png"),
                                    
                                    os.path.join("Adviser", "Adviser_Attack_1.png"),
                                    os.path.join("Infantry", "Infantry_Attack_1.png"),
                                    os.path.join("Lancer", "Lancer_Attack_1.png"),
                                    os.path.join("Heavy_Infantry", "Heavy_Infantry_Attack_1.png")   
        ]
        
        self.button_names = ["character_1", "character_2", "character_3", "character_4", "character_5", "character_6", "character_7", "character_8"]
        
        # Internal mapping from button action to skin name
        self.skin_map = {
            "character_1": "heavy_cavalry",
            "character_2": "archer",
            "character_3": "cavalry",
            "character_4": "heavy_archer",
            "character_5": "adviser",
            "character_6": "infantry",
            "character_7": "lancer",
            "character_8": "heavy_infantry"
        }
        
        self.buttons = self.create_buttons()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.manager.switch_screen("save_menu")

        mouse_position = pygame.mouse.get_pos()
        for button in self.buttons:
            button.check_hover(mouse_position)
            action = button.handle_event(event)
            # valid option to parse
            if action and action in self.skin_map:
                skin_name = self.skin_map[action]
                print(f"Selected skin: {skin_name}")
                
                # Assign base character class based on skin
                if "archer" in skin_name:
                    self.manager.selected_character = "archer"
                elif "adviser" in skin_name:
                    self.manager.selected_character = "mage"
                else:
                    self.manager.selected_character = "warrior"
                
                # Save to database if slot is selected
                slot = self.manager.selected_slot
                if slot:
                    db_file = f"game_data_{slot}.db"
                    try:
                        db = DatabaseManager(db_file)
                        db.update_player_skin(1, skin_name)
                        db.close()
                        print(f"Saved skin {skin_name} to {db_file}")
                    except Exception as e:
                        print(f"Error saving skin to database: {e}")
                
                self.manager.selected_skin = skin_name
                self.manager.switch_screen("game_window")

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
        start_y = int(self.manager.height * 0.55)   # move grid down relative to height

        for index, button_name in enumerate(self.button_names):
            row = index // cols
            col = index % cols

            # Position for each button
            x = start_x + col * gap_x - button_width // 2
            y = start_y + row * gap_y

            btn = ui.button.Button(
                x,
                y,
                button_width,
                button_height,
                "SELECT",
                button_font,
                action_name=button_name,
                bg_color=self.manager.bg_color,
                hover_color=(120, 100, 160),
                text_color=self.manager.text_color_white,
            )

            buttons.append(btn)

        return buttons

    def draw(self):
        """
        Draw the welcome screen with title and images.
        Input: None
        Output: None
        """
        self.manager.screen.fill(self.manager.bg_color) #fill covers the previous screen

        # text
        pygame.font.init()
        font = pygame.font.Font(os.path.join(BASE_DIR, '..', 'assets', 'fonts', 'Jersey10-Regular.ttf'), size=150)

        text = font.render("CHARACTERS", True, self.manager.text_color_green)
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
            ground_y = btn.rect.top
            self.draw_character(img_name, char_x, ground_y)

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

        # scaling
        original_w, original_h = image.get_size()
        image = pygame.transform.scale(image, (int(original_w * 6.5), int(original_h * 6.5)))

       
        rect = image.get_rect(midbottom=(x, y))

        self.manager.screen.blit(image, rect)

                