import pygame
from core.config import Config
from database.db_manager import DatabaseManager
from gameplay.engine import GameEngine
from visuals.asset_manager import AssetManager
from visuals.renderer import GameRenderer
from ui.button import Button


class GameWindow:
    def __init__(self, slot_id=1, selected_skin=None):
        pygame.init()
        self.screen = pygame.display.set_mode(
            (Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT)
        )
        pygame.display.set_caption(f"Hex RPG - Slot {slot_id}")
        self.clock = pygame.time.Clock()
        self.running = True

        db_file = f"game_data_{slot_id}.db"
        self.db = DatabaseManager(db_file)
        # Ensure session exists (auto-create slot 1)
        if not self.db.get_session(1):
            self.db.create_session(1)
            
        if selected_skin:
            self.db.cursor.execute("UPDATE player_state SET texture_file=? WHERE session_id=1", (selected_skin,))
            self.db.conn.commit()

        self.engine = GameEngine(self.db, 1)
        self.assets = AssetManager()
        self.renderer = GameRenderer(self.assets)

        self.font = pygame.font.SysFont("Arial", 18)
        self.frame_index = 0
        self.anim_timer = 0

    def run(self):
        while self.running:
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(60)  # 60 FPS cap

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            # Key Presses (Single Action)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

                action = None
                if event.key == pygame.K_w:
                    action = "MOVE_NORTH"
                elif event.key == pygame.K_s:
                    action = "MOVE_SOUTH"
                elif event.key == pygame.K_a:
                    action = "MOVE_WEST"
                elif event.key == pygame.K_d:
                    action = "MOVE_EAST"
                elif event.key == pygame.K_q:
                    action = "MOVE_SW"
                elif event.key == pygame.K_e:
                    action = "MOVE_NE"
                elif event.key == pygame.K_f or event.key == pygame.K_SPACE:
                    action = "INTERACT"
                elif event.key == pygame.K_i or event.key == pygame.K_TAB:
                    action = "INVENTORY"

                if action:
                    self.engine.handle_input(action)

    def update(self):
        # Animation tick
        self.anim_timer += self.clock.get_time()
        if self.anim_timer > 150:
            self.anim_timer = 0
            self.frame_index += 1

    def draw(self):
        # Render World
        self.renderer.render(self.screen, self.engine.world, self.frame_index)

        # Render UI Overlay
        self._draw_ui()

        # inventory
        if self.engine.show_inventory:
            self._draw_inventory()

        pygame.display.flip()

    def _draw_ui(self):
        p = self.engine.world.player
        if not p:
            return

        # Simple Stat Bar
        pygame.draw.rect(self.screen, (30, 30, 30), (0, 0, Config.WINDOW_WIDTH, 40))

        hp_text = self.font.render(f"HP: {p.hp}/{p.max_hp}", True, (255, 80, 80))
        hunger_text = self.font.render(
            f"Hunger: {p.hunger}/{p.max_hunger}", True, (255, 160, 50)
        )
        dmg_text = self.font.render(f"ATK: {p.total_damage}", True, (255, 200, 100))
        def_text = self.font.render(f"DEF: {p.total_defense}", True, (100, 200, 255))
        loc_text = self.font.render(f"Q:{p.q} R:{p.r}", True, (200, 200, 200))

        self.screen.blit(hp_text, (20, 10))
        self.screen.blit(hunger_text, (150, 10))
        self.screen.blit(dmg_text, (320, 10))
        self.screen.blit(def_text, (420, 10))
        self.screen.blit(loc_text, (Config.WINDOW_WIDTH - 100, 10))

    def _draw_inventory(self):
        # Semi-transparent dark overlay
        overlay = pygame.Surface(
            (Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT), pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        # Inventory panel
        panel_x, panel_y = 200, 80
        panel_w, panel_h = Config.WINDOW_WIDTH - 400, Config.WINDOW_HEIGHT - 160
        pygame.draw.rect(
            self.screen, (40, 40, 40), (panel_x, panel_y, panel_w, panel_h)
        )
        pygame.draw.rect(
            self.screen, (180, 180, 180), (panel_x, panel_y, panel_w, panel_h), 2
        )

        # Title
        title = self.font.render(
            "INVENTORY  (W/S scroll, F use/equip, A drop, I close)",
            True,
            (255, 255, 255),
        )
        self.screen.blit(title, (panel_x + 15, panel_y + 10))

        # Equipment summary
        p = self.engine.world.player
        equip_y = panel_y + 32
        equip_summary = f"ATK: {p.total_damage}  DEF: {p.total_defense}"
        eq_surf = self.font.render(equip_summary, True, (180, 220, 180))
        self.screen.blit(eq_surf, (panel_x + 15, equip_y))

        # Slot overview on the right side
        slot_x = panel_x + panel_w - 180
        slot_y = panel_y + 32
        for slot_name in ("weapon", "head", "chest", "legs"):
            equipped = p.equipment.get(slot_name)
            label = equipped.name if equipped else "--"
            color = (200, 255, 200) if equipped else (100, 100, 100)
            slot_surf = self.font.render(f"{slot_name}: {label}", True, color)
            self.screen.blit(slot_surf, (slot_x, slot_y))
            slot_y += 18

        items = self.engine.inventory
        if not items:
            empty = self.font.render("Your inventory is empty.", True, (150, 150, 150))
            self.screen.blit(empty, (panel_x + 15, equip_y + 30))
            return

        y = equip_y + 26
        for i, item in enumerate(items):
            selected = i == self.engine.selected_index
            color = (255, 255, 100) if selected else (200, 200, 200)
            prefix = "> " if selected else "  "

            equip_tag = " [E]" if item.equipped else ""
            slot_tag = f" [{item.slot}]" if item.is_equippable else ""
            label = f"{prefix}{item.name} x{item.quantity}  ({item.type}){slot_tag}{equip_tag}"
            text_surf = self.font.render(label, True, color)
            self.screen.blit(text_surf, (panel_x + 15, y))

            # Show item details for selected item
            if selected:
                y += 22
                details = []
                if item.description:
                    details.append(f"  {item.description}")
                if item.type == "weapon" or (item.type == "armor" and item.damage_bonus):
                    details.append(
                        f"  DMG: +{item.damage_bonus}  Durability: {item.durability}/{item.max_durability}"
                    )
                if item.defense:
                    details.append(
                        f"  DEF: +{item.defense}  Durability: {item.durability}/{item.max_durability}"
                    )
                if item.type == "food":
                    details.append(
                        f"  Heals: {item.healing_amount} HP  Hunger: +{item.hunger_restore}"
                    )
                if item.weight:
                    details.append(f"  Weight: {item.weight}")
                for d in details:
                    det_surf = self.font.render(d, True, (150, 180, 150))
                    self.screen.blit(det_surf, (panel_x + 15, y))
                    y += 20

            y += 26
