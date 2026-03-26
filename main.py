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


        # window size full screen 
        info = pygame.display.Info()
        self.width, self.height = info.current_w, info.current_h - TOP_MARGIN
        self.screen = pygame.display.set_mode(size=(self.width, self.height))
        
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
                else:
                    self.current_screen.handle_event(event)

            self.current_screen.draw()
            pygame.display.flip()  # Update the full display surface to the screen
           
            self.clock.tick(60)  # Limit to 60 FPS

        pygame.quit()

if __name__ == "__main__":
    manager = ScreenManager()
    manager.run()
