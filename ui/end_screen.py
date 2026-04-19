import pygame
import os
import ui.button
from ui.base_screen import Screen

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class EndScreen(Screen):
    title = ""
    decoration_images = []

    def __init__(self, manager):
        super().__init__(manager)
        self.buttons = self.create_buttons()

    def create_buttons(self):
        button_height = 50
        button_width = 150
        button_font = pygame.font.Font(
            os.path.join(BASE_DIR, '..', 'assets', 'fonts', 'Jersey10-Regular.ttf'), size=30
        )
        x = (self.manager.width / 2) - 270 - (button_width / 2)
        y = (self.manager.height / 2) - (button_height / 2)
        return [ui.button.Button(
            x, y, button_width, button_height, "PLAY AGAIN", button_font,
            action_name="play_again", bg_color=(175, 143, 233),
            hover_color=(120, 100, 160), text_color=self.manager.text_color_white,
        )]

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.manager.switch_screen("main_menu")
        mouse_position = pygame.mouse.get_pos()
        for button in self.buttons:
            button.check_hover(mouse_position)
            if button.handle_event(event) == "play_again":
                self.manager.switch_screen("main_menu")

    def draw(self):
        self.manager.screen.fill(self.manager.bg_color)
        font = pygame.font.Font(
            os.path.join(BASE_DIR, '..', 'assets', 'fonts', 'Jersey10-Regular.ttf'), size=210
        )
        text = font.render(self.title, True, self.manager.text_color_green)
        rect = text.get_rect(midtop=(self.manager.width // 2 - 280, self.manager.height // 4))
        self.manager.screen.blit(source=text, dest=rect)
        center_x, center_y = self.manager.width // 2, self.manager.height // 2
        for image_name, dx, dy, angle, scale in self.decoration_images:
            self.draw_image(image_name, center_x + dx, center_y + dy, angle, scale)
        for button in self.buttons:
            button.draw(self.manager.screen)

    def draw_image(self, image_name, x, y, angle, scale):
        if "sprite1" in image_name:
            path = os.path.join(BASE_DIR, '..', 'assets', 'assetBank', 'Castles', image_name)
        else:
            path = os.path.join(BASE_DIR, '..', 'assets', 'assetBank', 'Hex Tiles', image_name)
        image = pygame.image.load(path)
        w, h = image.get_size()
        scaled = pygame.transform.scale(image, (int(w * scale), int(h * scale)))
        rotated = pygame.transform.rotate(scaled, angle)
        self.manager.screen.blit(rotated, rotated.get_rect(center=(x, y)))



        