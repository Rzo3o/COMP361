import pygame
from core.config import Config
from database.db_manager import DatabaseManager
from gameplay.engine import GameEngine
from visuals.asset_manager import AssetManager
from visuals.renderer import GameRenderer
from ui.button import Button

class GameWindow:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT))
        pygame.display.set_caption("Hex RPG - Pygame Edition")
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.db = DatabaseManager()
        # Ensure session exists (auto-create slot 1)
        if not self.db.get_session(1):
            self.db.create_session(1)

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
            self.clock.tick(60) # 60 FPS cap

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            # Key Presses (Single Action)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                
                action = None
                if event.key == pygame.K_w: action = "MOVE_NORTH"
                elif event.key == pygame.K_s: action = "MOVE_SOUTH"
                elif event.key == pygame.K_a: action = "MOVE_WEST"
                elif event.key == pygame.K_d: action = "MOVE_EAST"
                elif event.key == pygame.K_q: action = "MOVE_SW"
                elif event.key == pygame.K_e: action = "MOVE_NE"
                elif event.key == pygame.K_f or event.key == pygame.K_SPACE: action = "INTERACT"
                elif event.key == pygame.K_i or event.key == pygame.K_TAB: action = "INVENTORY"

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

        pygame.display.flip()

    def _draw_ui(self):
        p = self.engine.world.player
        if not p:
            return

        # Simple Stat Bar
        pygame.draw.rect(self.screen, (30, 30, 30), (0, 0, Config.WINDOW_WIDTH, 40))
        
        hp_text = self.font.render(f"HP: {p.hp}/{p.max_hp}", True, (255, 80, 80))
        hunger_text = self.font.render(f"Hunger: {p.hunger}/{p.max_hunger}", True, (255, 160, 50))
        loc_text = self.font.render(f"Q:{p.q} R:{p.r}", True, (200, 200, 200))

        self.screen.blit(hp_text, (20, 10))
        self.screen.blit(hunger_text, (150, 10))
        self.screen.blit(loc_text, (Config.WINDOW_WIDTH - 100, 10))
