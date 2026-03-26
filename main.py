from abc import ABC, abstractmethod
import pygame

from ui.base_screen import Screen


#screens (only place all the screens are imported)
# add to available screen dictionaty attribute
import ui.welcome as screen1
import ui.winner as screen2
import ui.game_rules as screen3
import ui.main_menu as screen4
import ui.characters as screen5
import ui.save_menu as screen6
import ui.game_window as screen7

TOP_MARGIN = 60

# singleton (to do) and state design pattern
class ScreenManager:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption("Beyond") 

        # font has differnet sizes

        # background color (grey)
        self.bg_color = (79, 79, 79)
        # text color (green)
        self.text_color_green = (154, 205, 50)
        # text color (white)
        self.text_color_white = (255, 255, 255)


        from core.config import Config
        import os
        import platform
        
        # window size full screen windowed (maximized)
        info = pygame.display.Info()
        self.width, self.height = info.current_w, info.current_h
        
        # Initialize as resizable first
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        
        # Maximize window on Windows
        if platform.system() == "Windows":
            try:
                import ctypes
                hwnd = pygame.display.get_wm_info().get("window")
                if hwnd:
                    # 3 is SW_MAXIMIZE
                    ctypes.windll.user32.ShowWindow(hwnd, 3)
            except Exception as e:
                print(f"Could not maximize window: {e}")

        # Update width and height from the actual window surface after maximization
        self.width, self.height = self.screen.get_size()
        
        # Sync with Config for UI and Game logic
        Config.WINDOW_WIDTH = self.width
        Config.WINDOW_HEIGHT = self.height
        Config.CENTER_X = self.width // 2
        Config.CENTER_Y = self.height // 2
        
        self.clock = pygame.time.Clock()
        self.running = True
        #game window specific variables
        self.selected_slot = None
        self.selected_skin = None

       
        self.available_screens = {
            "welcome": screen1.Welcome,
            "winner": screen2.Winner,
            "game_rules": screen3.GameRules,
            "main_menu": screen4.MainMenu,
            "characters": screen5.Characters,
            "save_menu": screen6.SaveSelectMenu,
            "game_window": screen7.GameWindow 
        }

        #start screen
        self.current_screen = self.available_screens["welcome"](self)

    def switch_screen(self, new_screen: str):
            self.current_screen = self.available_screens[new_screen](self)

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.VIDEORESIZE:
                    from core.config import Config
                    self.width, self.height = event.w, event.h
                    Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT = self.width, self.height
                    Config.CENTER_X, Config.CENTER_Y = self.width // 2, self.height // 2
                    # The screen surface itself is automatically resized in Pygame 2+
                    # but we update current_screen if it needs re-init (optional, most screens draw dynamically)
                else:
                    self.current_screen.handle_event(event)

            self.current_screen.draw()
            pygame.display.flip()  # Update the full display surface to the screen
           
            self.clock.tick(60)  # Limit to 60 FPS

        pygame.quit()

if __name__ == "__main__":
    manager = ScreenManager()
    manager.run()
