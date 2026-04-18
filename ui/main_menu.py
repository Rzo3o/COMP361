import pygame
import sys
import os
from ui.button import Button
from ui.base_screen import Screen

# Constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # directory of this script

#screen resolution px for relative image 
SCREEN_W = 1512
SCREEN_H = 982


class MainMenu(Screen):
    def __init__(self, manager):
        super().__init__(manager)
     
        # Color
        self.button_color = (70, 70, 90)

        # (image name, x, y, angle, scale)
        self.decoration_images = [
        ('Water_Duck.png', 405/SCREEN_W, 75/SCREEN_H, 5, 2.3999999999999995),
        ('Grass.png', 360/SCREEN_W, 175/SCREEN_H, 20, 1.5999999999999996),
        ('Grass_Pine.png', 1089/SCREEN_W, 201/SCREEN_H, -15, 2.1),
        ('Magic_Crystals.png', 480/SCREEN_W, 200/SCREEN_H, -15, 2.8),
        ('Snow_Trees.png', 1073/SCREEN_W, 76/SCREEN_H, 10, 2.4999999999999996),
        ('Grass_Plants2.png', 1170/SCREEN_W, 145/SCREEN_H, 25, 1.5999999999999996)
        ]

         # text and font
        pygame.font.init()
        self.title_font = pygame.font.Font(os.path.join(BASE_DIR, '..', 'assets', 'fonts', 'Jersey10-Regular.ttf'), size=150)
        self.button_font = pygame.font.Font(os.path.join(BASE_DIR, '..', 'assets', 'fonts', 'Jersey10-Regular.ttf'), size=50)

        # Button sizes
        self.button_width = 420
        self.button_height = 100
        self.button_gap = 30

        # Create buttons
        self.create_button()

    def create_button(self):
        center_x = self.manager.width // 2
        self.title_y = 68
        start_y = 300
        self.button_width = 420
        self.button_height = 100
        self.button_gap = 30

        self.play_button = Button(
            center_x - self.button_width // 2,
            start_y,
            self.button_width,
            self.button_height,
            "PLAY",
            self.button_font,
            action_name="play",
            bg_color=(199, 234, 70),
            hover_color=(120, 100, 160),
            text_color=self.manager.text_color_white,
        )

        self.rules_button = Button(
            center_x - self.button_width // 2,
            start_y + (self.button_height + self.button_gap),
            self.button_width,
            self.button_height,
            "GAME RULES",
            self.button_font,
            action_name="rules",
            bg_color=(0, 191, 255),
            hover_color=(120, 100, 160),
            text_color=self.manager.text_color_white,
        )

        # quit button
        self.quit_button = Button(
            center_x - self.button_width // 2,
            start_y + 2 * (self.button_height + self.button_gap),
            self.button_width,
            self.button_height,
            "QUIT",
            self.button_font,
            action_name="quit",
            bg_color=(170, 40, 115),
            hover_color=(120, 100, 160),
            text_color=self.manager.text_color_white,
        )

        self.buttons = [self.play_button, self.rules_button, self.quit_button]

    def draw_image(self, image_name: str, x: int, y: int, angle: int, scale: float):
        """
        Draw image on the screen.
        """
        image_path = os.path.join(BASE_DIR, '..', 'assets', 'assetBank', 'Hex Tiles', image_name)

        image = pygame.image.load(image_path).convert_alpha()

        original_w, original_h = image.get_size()
        scaled_image = pygame.transform.scale(
            image, (int(original_w * scale), int(original_h * scale))
        )
        rotated_image = pygame.transform.rotate(scaled_image, angle)
        rect = rotated_image.get_rect(center=(x, y))

        self.manager.screen.blit(rotated_image, rect)

    def draw(self):
        self.manager.screen.fill(self.manager.bg_color)

        # Draw decorative images
        for image_name, x, y, angle, scale in self.decoration_images:
            self.draw_image(image_name, int(x * self.manager.width), int(y * self.manager.height), angle, scale)



        # Main menu title
        title = self.title_font.render("MAIN MENU", True, self.manager.text_color_green)
        title_rect = title.get_rect(center=(self.manager.width // 2, 120))
        self.manager.screen.blit(title, title_rect)

        # Draw buttons
        for button in self.buttons:
            button.draw(self.manager.screen)

    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()

        for button in self.buttons:
            button.check_hover(mouse_pos)
            action = button.handle_event(event)

            if action == "play":
                self.manager.switch_screen("save_menu")
            elif action == "rules":
                self.manager.switch_screen("game_rules")
            elif action == "quit":
                pygame.quit()
                sys.exit()

                  

            


