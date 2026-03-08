import pygame
import sys
import os

class SaveSelectMenu:
    def __init__(self):
        pygame.init()
        self.width, self.height = 800, 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Select Save Slot")
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 32)
        self.clock = pygame.time.Clock()
        self.running = True
        self.selected_slot = None
        
        # Confirmation State
        self.confirm_delete_slot = None  # None or slot_id
        
        # Colors
        self.bg_color = (30, 30, 30)
        self.btn_color = (60, 60, 60)
        self.hover_color = (80, 80, 100)
        self.del_color = (150, 50, 50)
        self.del_hover = (200, 50, 50)
        self.text_color = (220, 220, 220)
        
        self.slots = [1, 2, 3]
        self.buttons = []
        self._create_buttons()

    def _create_buttons(self):
        self.buttons = []
        start_y = 200
        for slot in self.slots:
            # Slot Button
            rect = pygame.Rect(200, start_y, 300, 60)
            # Delete Button (small square to the right)
            del_rect = pygame.Rect(520, start_y, 60, 60)
            
            self.buttons.append({
                "type": "slot",
                "rect": rect,
                "text": f"Save Slot {slot}",
                "value": slot
            })
            self.buttons.append({
                "type": "delete",
                "rect": del_rect,
                "text": "X",
                "value": slot
            })
            start_y += 80

    def draw(self):
        self.screen.fill(self.bg_color)
        
        # Title
        title_surf = self.font.render("Select Save Slot", True, self.text_color)
        title_rect = title_surf.get_rect(center=(self.width // 2, 100))
        self.screen.blit(title_surf, title_rect)
        
        mouse_pos = pygame.mouse.get_pos()
        
        for btn in self.buttons:
            rect = btn["rect"]
            is_hover = rect.collidepoint(mouse_pos)
            
            if btn["type"] == "slot":
                color = self.hover_color if is_hover else self.btn_color
                pygame.draw.rect(self.screen, color, rect, border_radius=10)
                pygame.draw.rect(self.screen, (100, 100, 100), rect, 2, border_radius=10)
                
                text_surf = self.small_font.render(btn["text"], True, self.text_color)
                text_rect = text_surf.get_rect(center=rect.center)
                self.screen.blit(text_surf, text_rect)
            
            elif btn["type"] == "delete":
                color = self.del_hover if is_hover else self.del_color
                pygame.draw.rect(self.screen, color, rect, border_radius=10)
                pygame.draw.rect(self.screen, (100, 100, 100), rect, 2, border_radius=10)
                
                text_surf = self.small_font.render("X", True, self.text_color)
                text_rect = text_surf.get_rect(center=rect.center)
                self.screen.blit(text_surf, text_rect)

        # Confirmation Dialouge
        if self.confirm_delete_slot:
            self._draw_confirmation()

        pygame.display.flip()

    def _draw_confirmation(self):
        # Darken background
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Popup Box
        box_rect = pygame.Rect(200, 200, 400, 200)
        pygame.draw.rect(self.screen, (50, 50, 50), box_rect, border_radius=15)
        pygame.draw.rect(self.screen, (200, 50, 50), box_rect, 2, border_radius=15)
        
        # Text
        msg = f"Delete Save Slot {self.confirm_delete_slot}?"
        text_surf = self.font.render(msg, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=(self.width // 2, 250))
        self.screen.blit(text_surf, text_rect)
        
        # Yes / No Buttons
        yes_rect = pygame.Rect(250, 320, 100, 50)
        no_rect = pygame.Rect(450, 320, 100, 50)
        
        mouse_pos = pygame.mouse.get_pos()
        
        # Yes
        c_yes = (200, 50, 50) if yes_rect.collidepoint(mouse_pos) else (150, 50, 50)
        pygame.draw.rect(self.screen, c_yes, yes_rect, border_radius=5)
        yes_txt = self.small_font.render("YES", True, (255, 255, 255))
        self.screen.blit(yes_txt, yes_txt.get_rect(center=yes_rect.center))
        
        # No
        c_no = (100, 100, 100) if no_rect.collidepoint(mouse_pos) else (80, 80, 80)
        pygame.draw.rect(self.screen, c_no, no_rect, border_radius=5)
        no_txt = self.small_font.render("NO", True, (255, 255, 255))
        self.screen.blit(no_txt, no_txt.get_rect(center=no_rect.center))
        
        self.confirm_buttons = {"yes": yes_rect, "no": no_rect}

    def _delete_save(self, slot):
        filename = f"game_data_{slot}.db"
        if os.path.exists(filename):
            try:
                os.remove(filename)
                print(f"Deleted {filename}")
            except Exception as e:
                print(f"Error deleting {filename}: {e}")
        else:
             print(f"File {filename} does not exist.")

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return None
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if self.confirm_delete_slot:
                            # Handle Confirmation
                            if self.confirm_buttons["yes"].collidepoint(event.pos):
                                self._delete_save(self.confirm_delete_slot)
                                self.confirm_delete_slot = None
                            elif self.confirm_buttons["no"].collidepoint(event.pos):
                                self.confirm_delete_slot = None
                        else:
                            # Handle Main Menu
                            for btn in self.buttons:
                                if btn["rect"].collidepoint(event.pos):
                                    if btn["type"] == "slot":
                                        self.selected_slot = btn["value"]
                                        self.running = False
                                        return self.selected_slot
                                    elif btn["type"] == "delete":
                                        self.confirm_delete_slot = btn["value"]
            
            self.draw()
            self.clock.tick(60)
        
        pygame.quit()
        return self.selected_slot

if __name__ == "__main__":
    menu = SaveSelectMenu()
    slot = menu.run()
    if slot:
        print(f"Selected Slot: {slot}")
    else:
        print("Cancelled")
