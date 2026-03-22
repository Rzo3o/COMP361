import pygame
import sys
import os
from button import Button

# Constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # directory of this script


class MainMenu:
    def __init__(self):
        pygame.init()

        # Window
        self.width, self.height = pygame.display.get_desktop_sizes()[0]
        self.height -= 60
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)

        pygame.display.set_caption("Main Menu")

        self.clock = pygame.time.Clock()
        self.running = True

        # Colors
        self.bg_color = (79, 79, 79)
        self.text_color = (154, 205, 50)
        self.button_color = (70, 70, 90)

        # (image name, x, y, angle, scale)
        self.decoration_images = [
    ('Water_Duck.png', 405, 75, 5, 2.3999999999999995),
    ('Grass.png', 360, 175, 20, 1.5999999999999996),
    ('Grass_Pine.png', 1089, 201, -15, 2.1),
    ('Magic_Crystals.png', 480, 200, -15, 2.8),
    ('Snow_Trees.png', 1073, 76, 10, 2.4999999999999996),
    ('Grass_Plants2.png', 1170, 145, 25, 1.5999999999999996)
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
        self.update_layout()

    def update_layout(self):
        center_x = self.width // 2
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
            text_color=(255, 255, 255),
        )

        self.rules_button = Button(
            center_x - self.button_width // 2,
            start_y + self.button_height + self.button_gap,
            self.button_width,
            self.button_height,
            "GAME RULES",
            self.button_font,
            action_name="rules",
            bg_color=(0, 191, 255),
            hover_color=(120, 100, 160),
            text_color=(255, 255, 255),
        )

        self.exit_button = Button(
            center_x - self.button_width // 2,
            start_y + 2 * (self.button_height + self.button_gap),
            self.button_width,
            self.button_height,
            "SAVED GAMES",
            self.button_font,
            action_name="exit",
            bg_color=(147, 112, 219),
            hover_color=(120, 100, 160),
            text_color=(255, 255, 255),
        )

        self.buttons = [self.play_button, self.rules_button, self.exit_button]

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

        self.screen.blit(rotated_image, rect)

    def draw(self):
        self.screen.fill(self.bg_color)

        # Draw decorative images
        for image_name, x, y, angle, scale in self.decoration_images:
            self.draw_image(image_name, x, y, angle, scale)

        # Main menu title
        title = self.title_font.render("MAIN MENU", True, self.text_color)
        title_rect = title.get_rect(center=(self.width // 2, 120))
        self.screen.blit(title, title_rect)

        # Draw buttons
        for button in self.buttons:
            button.draw(self.screen)

        pygame.display.flip()

    def run(self):
        while self.running:
            mouse_pos = pygame.mouse.get_pos()

            for button in self.buttons:
                button.check_hover(mouse_pos)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                elif event.type == pygame.VIDEORESIZE:
                    self.width, self.height = event.w, event.h
                    self.screen = pygame.display.set_mode(
                        (self.width, self.height), pygame.RESIZABLE
                    )
                    self.update_layout()

                for button in self.buttons:
                    action = button.handle_event(event)

                    if action == "play":
                        print("Play clicked")

                    elif action == "rules":
                        print("Rules clicked")

                  

            self.draw()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    menu = MainMenu()
    menu.run()