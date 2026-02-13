import pygame

class Button:
    def __init__(self, x, y, width, height, text, font, action_name=None, bg_color=(50, 50, 50), hover_color=(70, 70, 70), text_color=(255, 255, 255)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.action_name = action_name
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False

    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.is_hovered:
                return self.action_name
        return None

    def draw(self, screen):
        color = self.hover_color if self.is_hovered else self.bg_color
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, (200, 200, 200), self.rect, 2) # Border

        if self.text:
            surf = self.font.render(self.text, True, self.text_color)
            rect = surf.get_rect(center=self.rect.center)
            screen.blit(surf, rect)
