import pygame
import sys
import os
from ui.button import Button
from ui.base_screen import Screen

# Constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # directory of this script

class GameRules(Screen):
    def __init__(self, manager):
        super().__init__(manager)

        # Fonts
        self.title_font = pygame.font.Font(
            os.path.join(BASE_DIR, "..", "assets", "fonts", "Jersey10-Regular.ttf"),
        150,
        )
        self.goal_font = pygame.font.Font(
            os.path.join(BASE_DIR, "..", "assets", "fonts", "Jersey10-Regular.ttf"),
            60,
        )

        self.rules_font = pygame.font.Font(
            os.path.join(BASE_DIR, "..", "assets", "fonts", "Jersey10-Regular.ttf"),
            40,
        )

        self.rules_font = pygame.font.Font(
            os.path.join(BASE_DIR, "..", "assets", "fonts", "Jersey10-Regular.ttf"),
            40,
        )

        self.button_font = pygame.font.Font(
            os.path.join(BASE_DIR, "..", "assets", "fonts", "Jersey10-Regular.ttf"),
            40,
        )

        # green
        self.rules_text = [
            "Goal: Conquer all castles, defeat the final castle, and win!",
            "1. Choose a character to begin your adventure.",
            "2. Move across hex tiles with arrow keys (6 directions).",
            "3. Attack enemies with A when on an adjacent tile.",
            "4. Open your inventory with I to manage items and equipment.",
            "5. Walk over power-ups to collect them, then press P to activate.",
        ]

        self.decoration_images = [
        ('Grass.png', 1102, 69, 15, 2.5999999999999996),
        ('Grass.png', 385, 163, 20, 1.5999999999999996),
        ('Grass_Pine.png', 1076, 179, -30, 1.4999999999999991),
        ('Magic.png', 1142, 160, 10, 1.7999999999999994),
        ('Magic.png', 480, 170, -20, 2.3999999999999995),
        ('Snow_Snowman.png', 400, 75, -20, 2.2999999999999994),
        ]

        #button size
        self.button_width = 150
        self.button_height = 50
        self.button_gap = 30

        self.create_button()

        #create button
    def create_button(self):
            self.next_button = Button(
            self.manager.width - self.button_width - 30,      # 30px from right edge
            self.manager.height - self.button_height - 30,    
            self.button_width,
            self.button_height,
            "NEXT",
            self.button_font,
            action_name="next",
            bg_color=(175, 143, 233),
            hover_color=(120, 100, 160),
            text_color=self.manager.text_color_white,
        )

            self.buttons = [self.next_button]

    def draw(self):

        self.manager.screen.fill(self.manager.bg_color) #fill covers the previous screen

        # Draw decorative images
        for image_name, x, y, angle, scale in self.decoration_images:
            self.draw_image(image_name, x, y, angle, scale)

        # Title
        title = self.title_font.render("GAME RULES", True, self.manager.text_color_white)
        title_rect = title.get_rect(center=(self.manager.width // 2, 100))
        self.manager.screen.blit(title, title_rect)

        # Rules text
        start_y = 280
        line_gap = 60

        for i, line in enumerate(self.rules_text):
            font = self.goal_font if i == 0 else self.rules_font  
            text_surface = font.render(line, True, self.manager.text_color_green) 
            text_rect = text_surface.get_rect(center=(self.manager.width // 2, start_y + i * line_gap))
            self.manager.screen.blit(text_surface, text_rect)

        # Draw buttons
        for button in self.buttons:
            button.draw(self.manager.screen)

    def draw_image(self, image_name: str, x: int, y: int, angle: int, scale: float):
        image_path = os.path.join(BASE_DIR, '..', 'assets', 'assetBank', 'Hex Tiles', image_name)
        image = pygame.image.load(image_path).convert_alpha()
        original_w, original_h = image.get_size()
        scaled_image = pygame.transform.scale(image, (int(original_w * scale), int(original_h * scale)))
        rotated_image = pygame.transform.rotate(scaled_image, angle)
        rect = rotated_image.get_rect(center=(x, y))
        self.manager.screen.blit(rotated_image, rect)

    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.check_hover(mouse_pos)
        for button in self.buttons:
            action = button.handle_event(event)
            if action == "next":
                self.manager.switch_screen("main_menu")


    

            

        

      


