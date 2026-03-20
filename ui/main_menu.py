import pygame
import sys
import os
from button import Button


class MainMenu:
    def __init__(self):
        pygame.init()

        # Window
        self.width, self.height = pygame.display.get_desktop_sizes()[0]
        self.screen = pygame.display.set_mode(
            (self.width, self.height - 60), pygame.RESIZABLE
        )
        pygame.display.set_caption("Main Menu")

        self.clock = pygame.time.Clock()
        self.running = True

        # colour (R G B)
        self.bg_color = (28, 48, 41)
        self.text_color = (240, 240, 240)

        # font 
        self.title_font = pygame.font.SysFont("arial", 100 , bold=True)
        self.button_font = pygame.font.SysFont("Roboto Mono", 50, bold=True)

        # Button sizes``
        self.button_width = 420
        self.button_height = 100
        self.button_gap = 30

        # Create buttons
        self.update_layout()

        # Monster image
        monster_path = os.path.join(
            "assets",
            "assetBank",
            "Forest_Monsters_PREMIUM",
            "Forest_Monsters_PREMIUM",
            "Bush_Monster",
            "Bush Monster with VFX",
            "Bush_Monster-AttackTimeFrame.png",
        )

        self.monster_img = pygame.image.load(monster_path).convert_alpha()
        # monster size image
        self.monster_img = pygame.transform.scale(self.monster_img, (260, 260))
        self.monster_rect = self.monster_img.get_rect()

    def update_layout(self):
        center_x = self.width // 2
        start_y = self.height // 2 - 60

        self.play_button = Button(
            center_x - self.button_width // 2,
            start_y,
            self.button_width,
            self.button_height,
            "PLAY",
            self.button_font,
            action_name="play",
            bg_color=(70, 70, 90),
            hover_color=(120, 100, 160), #purple when hover over
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
            bg_color=(70, 70, 90),
            hover_color=(120, 100, 160),
            text_color=(255, 255, 255),
        )

        self.exit_button = Button(
            center_x - self.button_width // 2,
            start_y + 2 * (self.button_height + self.button_gap),
            self.button_width,
            self.button_height,
            "EXIT",
            self.button_font,
            action_name="exit",
            bg_color=(70, 70, 90),
            hover_color=(120, 100, 160),
            text_color=(255, 255, 255),
        )

        self.buttons = [self.play_button, self.rules_button, self.exit_button]

    def draw(self):
        self.screen.fill(self.bg_color)

        # main menu title for screen
        title = self.title_font.render("MAIN MENU", True, self.text_color)
        title_rect = title.get_rect(center=(self.width // 2, 120))
        self.screen.blit(title, title_rect)

        # Buttons
        for button in self.buttons:
            button.draw(self.screen)

        # image
        self.monster_rect.bottomright = (self.width - 30, self.height - 20)
        self.screen.blit(self.monster_img, self.monster_rect)

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
                        print("Play clicked") #debugging but replace with the actual logic later to start

                    elif action == "rules":
                        print("Rules clicked") #debugging but replace with the actual logic later to show game rules

                    elif action == "exit":
                        self.running = False

            self.draw()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    menu = MainMenu()
    menu.run()