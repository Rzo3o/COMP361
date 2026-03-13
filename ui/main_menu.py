import pygame
import sys
import os

class MainMenu:

    def __init__(self):
        pygame.init()

        self.width, self.height = 800, 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Beyond Hex")

        self.clock = pygame.time.Clock()
        self.running = True

        self.font = pygame.font.Font(None, 72)
        self.button_font = pygame.font.Font(None, 40)

        self.text_color = (220, 220, 220)
        self.btn_color = (60, 60, 60)
        self.hover_color = (80, 80, 100)

        #colours
        self.bg_color = (28, 48, 41)

        # simple buttons
        self.play_btn = pygame.Rect(270, 250, 260, 65)
        self.rules_btn = pygame.Rect(270, 340, 260, 65)
        self.exit_btn = pygame.Rect(270, 430, 260, 65)

        #monster pic
        self.monster_img = pygame.image.load(os.path.join("assets", "assetBank", "Forest_Monsters_PREMIUM", "Forest_Monsters_PREMIUM", "Bush_Monster", "Bush Monster with VFX", "Bush_Monster-AttackTimeFrame.png")).convert_alpha()
        self.monster_img = pygame.transform.scale(self.monster_img, (200, 200))
        self.monster_rect = self.monster_img.get_rect(center=(400, 100))

    def draw_button(self, rect, text):

        mouse = pygame.mouse.get_pos()
        color = self.hover_color if rect.collidepoint(mouse) else self.btn_color

        pygame.draw.rect(self.screen, color, rect, border_radius=10)

        text_surf = self.button_font.render(text, True, self.text_color)
        text_rect = text_surf.get_rect(center=rect.center)
        self.screen.blit(text_surf, text_rect)

    def draw(self):

        self.screen.fill(self.bg_color)

        title = self.font.render("Beyond Hex", True, self.text_color)
        self.screen.blit(title, title.get_rect(center=(400,120)))
        
       
        self.draw_button(self.play_btn, "Play")
        self.draw_button(self.rules_btn, "Game Rules")
        self.draw_button(self.exit_btn, "Exit")
        #monster pic
        self.monster_img = pygame.image.load("/Users/yasmin/Downloads/361/assets/assetBank/Forest_Monsters_PREMIUM/Forest_Monsters_PREMIUM/Bush_Monster/Bush Monster with VFX/Bush_Monster-AttackTimeFrame.png").convert_alpha()
        self.monster_img = pygame.transform.scale(self.monster_img, (200, 200))
        self.monster_rect = self.monster_img.get_rect(center=(400, 100))
        #bring monster to right below
        self.monster_rect.bottomright = (self.width - 20, self.height - 20)
        self.screen.blit(self.monster_img, self.monster_rect)



        pygame.display.flip()

    def run(self):

        while self.running:

            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.MOUSEBUTTONDOWN:

                    if self.play_btn.collidepoint(event.pos):
                        print("Play clicked")

                    if self.rules_btn.collidepoint(event.pos):
                        print("Rules clicked")

                    if self.exit_btn.collidepoint(event.pos):
                        self.running = False

            self.draw()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    menu = MainMenu()
    menu.run()