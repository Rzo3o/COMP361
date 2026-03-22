import pygame
import sys
import os
from button import Button

# Constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # directory of this script





class GameRules:
    def __init__(self):
        pygame.init()

        # Window
        self.width, self.height = pygame.display.get_desktop_sizes()[0]
        self.height -= 60
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("GAME RULES")

        self.clock = pygame.time.Clock()
        self.running = True

        # Colors
        self.bg_color = (79, 79, 79)
        self.text_color = (154, 205, 50)
        self.title_color = (255, 255, 255)
      

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

        self.update_layout()

        #create button
    def update_layout(self):
            self.next_button = Button(
            self.width - self.button_width - 30,      # 30px from right edge
            self.height - self.button_height - 30,    
            self.button_width,
            self.button_height,
            "NEXT",
            self.button_font,
            action_name="next",
            bg_color=(175, 143, 233),
            hover_color=(120, 100, 160),
            text_color=(255, 255, 255),
        )

            self.buttons = [self.next_button]

    def draw(self):
        self.screen.fill(self.bg_color)

        # Draw decorative images
        for image_name, x, y, angle, scale in self.decoration_images:
            self.draw_image(image_name, x, y, angle, scale)


        # Title
        title = self.title_font.render("Game Rules", True, self.title_color)
        title_rect = title.get_rect(center=(self.width // 2, 100))
        self.screen.blit(title, title_rect)

        # Rules text
        start_y = 280
        line_gap = 60

        for i, line in enumerate(self.rules_text):
            font = self.goal_font if i == 0 else self.rules_font  
            text_surface = font.render(line, True, self.text_color) 
            text_rect = text_surface.get_rect(center=(self.width // 2, start_y + i * line_gap))
            self.screen.blit(text_surface, text_rect)

        # Draw buttons
        for button in self.buttons:
            button.draw(self.screen)


    def draw_image(self, image_name: str, x: int, y: int, angle: int, scale: float):
        image_path = os.path.join(BASE_DIR, '..', 'assets', 'assetBank', 'Hex Tiles', image_name)
        image = pygame.image.load(image_path).convert_alpha()
        original_w, original_h = image.get_size()
        scaled_image = pygame.transform.scale(image, (int(original_w * scale), int(original_h * scale)))
        rotated_image = pygame.transform.rotate(scaled_image, angle)
        rect = rotated_image.get_rect(center=(x, y))
        self.screen.blit(rotated_image, rect)

    def run(self):
        while self.running:
            mouse_pos = pygame.mouse.get_pos()
            for button in self.buttons:
                button.check_hover(mouse_pos)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                for button in self.buttons:
                    action = button.handle_event(event)
                if action == "next": # placeholder will add logic
                    print("next clicked")
                    

            self.draw()
            pygame.display.flip()
            self.clock.tick(60)


        

        pygame.quit()
        sys.exit()




if __name__ == "__main__":
    rules = GameRules()
    rules.run()