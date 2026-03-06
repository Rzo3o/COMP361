import pygame
import sys

from ui.button import Button
from ui.menu import SaveSelectMenu
from ui.game_window import GameWindow


class MainMenu:
    def __init__(self):
        pygame.init()

        self.width, self.height = 800, 600
        self.screen = pygame.display.set_mode((self.width, self.height))
       # pygame.display.set_caption("Main Menu")

        self.clock = pygame.time.Clock()
        self.running = True

        self.title_font = pygame.font.Font(None, 72)
        self.subtitle_font = pygame.font.Font(None, 32)
        self.button_font = pygame.font.Font(None, 40)
        

        # Colors
        self.bg_color = (30, 30, 30)
        self.text_color = (220, 220, 220)

        # Buttons
        button_width = 260
        button_height = 65
        button_x = (self.width - button_width) // 2
        start_y = 240
        gap = 90

        self.buttons = [
            Button(
                button_x, start_y,
                button_width, button_height,
                "Play", self.button_font,
                action_name="PLAY"
            ),
            Button(
                button_x, start_y + gap,
                button_width, button_height,
                "Game Rules", self.button_font,
                action_name="RULES"
            ),
            Button(
                button_x, start_y + 2 * gap,
                button_width, button_height,
                "Exit", self.button_font,
                action_name="EXIT"
            ),
        ]

    def draw(self):
        self.screen.fill(self.bg_color)

        # Title
        title_surf = self.title_font.render("Beyond Hex", True, self.text_color)
        title_rect = title_surf.get_rect(center=(self.width // 2, 120))
        self.screen.blit(title_surf, title_rect)

        
        

        # Update hover and draw buttons
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.check_hover(mouse_pos)
            button.draw(self.screen)

        pygame.display.flip()

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                        break

                for button in self.buttons:
                    action = button.handle_event(event)

                    if action == "PLAY":
                        self._open_save_select()

                    elif action == "RULES":
                        # Replace this print with your GameRulesPage later
                        print("Open Game Rules page here")

                    elif action == "EXIT":
                        self.running = False

            self.draw()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()

    def _open_save_select(self):
        save_menu = SaveSelectMenu()
        selected_slot = save_menu.run()

        # If user selected a slot, start the game
        if selected_slot is not None:
            game = GameWindow(slot_id=selected_slot)
            game.run()

            # Recreate main menu window after gameplay closes
            self.screen = pygame.display.set_mode((self.width, self.height))
            pygame.display.set_caption("Main Menu")


if __name__ == "__main__":
    menu = MainMenu()
    menu.run()