import pygame
import sys
import os
import json
from visuals.asset_manager import AssetManager

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
        self.selected_skin = None
        
        self.am = AssetManager()
        self._load_skins()
        self.current_skin_idx = 0
        
        # UI Rects for skin selector
        self.left_btn = pygame.Rect(self.width // 2 - 150, 150 - 20, 40, 40)
        self.right_btn = pygame.Rect(self.width // 2 + 110, 150 - 20, 40, 40)
        
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

    def _load_skins(self):
        self.skins = []
        player_def_dir = "assets/definitions/player"
        if os.path.exists(player_def_dir):
            for f in os.listdir(player_def_dir):
                if f.endswith(".json"):
                    try:
                        with open(os.path.join(player_def_dir, f), "r") as jf:
                            data = json.load(jf)
                            skin_name = data.get("name", f.replace(".json", ""))
                            tex = data.get("texture_file")
                            if not tex and "animations" in data:
                                tex = data["animations"].get("idle", {}).get("texture")
                            if tex:
                                self.skins.append({"name": skin_name, "texture": tex})
                    except Exception as e:
                        print(f"Error loading skin {f}: {e}")
        
        if not self.skins:
            self.skins.append({"name": "Default", "texture": None})

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
        title_rect = title_surf.get_rect(center=(self.width // 2, 70))
        self.screen.blit(title_surf, title_rect)
        
        mouse_pos = pygame.mouse.get_pos()
        
        # Skin Selector
        skin_y = 150
        skin_text = f"Skin: {self.skins[self.current_skin_idx]['name']}"
        skin_surf = self.small_font.render(skin_text, True, self.text_color)
        skin_rect = skin_surf.get_rect(center=(self.width // 2, skin_y))
        self.screen.blit(skin_surf, skin_rect)
        
        # Draw Left/Right Arrows for Skin Selector
        c_left = self.hover_color if self.left_btn.collidepoint(mouse_pos) else self.btn_color
        c_right = self.hover_color if self.right_btn.collidepoint(mouse_pos) else self.btn_color
        
        pygame.draw.rect(self.screen, c_left, self.left_btn, border_radius=5)
        pygame.draw.rect(self.screen, c_right, self.right_btn, border_radius=5)
        
        l_txt = self.font.render("<", True, self.text_color)
        r_txt = self.font.render(">", True, self.text_color)
        self.screen.blit(l_txt, l_txt.get_rect(center=self.left_btn.center))
        self.screen.blit(r_txt, r_txt.get_rect(center=self.right_btn.center))
        
        # Draw Skin Sprite Preview
        tex = self.skins[self.current_skin_idx]["texture"]
        if tex:
            skin_img = self.am.get_image(tex, scale=2.0)
            if skin_img:
                img_rect = skin_img.get_rect(center=(self.width // 2, skin_y - 40))
                self.screen.blit(skin_img, img_rect)
        
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
                            # Handle Skin Selection Arrows
                            if self.left_btn.collidepoint(event.pos):
                                self.current_skin_idx = (self.current_skin_idx - 1) % len(self.skins)
                            elif self.right_btn.collidepoint(event.pos):
                                self.current_skin_idx = (self.current_skin_idx + 1) % len(self.skins)
                                
                            # Handle Main Menu
                            for btn in self.buttons:
                                if btn["rect"].collidepoint(event.pos):
                                    if btn["type"] == "slot":
                                        self.selected_slot = btn["value"]
                                        self.selected_skin = self.skins[self.current_skin_idx]["texture"]
                                        self.running = False
                                        return self.selected_slot, self.selected_skin
                                    elif btn["type"] == "delete":
                                        self.confirm_delete_slot = btn["value"]
            
            self.draw()
            self.clock.tick(60)
        
        pygame.quit()
        return self.selected_slot, self.selected_skin

if __name__ == "__main__":
    menu = SaveSelectMenu()
    res = menu.run()
    if res and res[0]:
        print(f"Selected Slot: {res[0]}, Skin: {res[1]}")
    else:
        print("Cancelled")
