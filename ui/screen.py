from abc import ABC, abstractmethod
import pygame

from base_screen import Screen


#screens (only place all the screens are imported)
# add to available screen dictionaty attribute
import welcome as screen1
import winner as screen2
import game_rules as screen3
import main_menu as screen4

TOP_MARGIN = 60

# singleton and state design pattern
class ScreenManager:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption("Beyond") 

        # window size full screen 
        info = pygame.display.Info()
        self.width, self.height = info.current_w, info.current_h - TOP_MARGIN
        self.screen = pygame.display.set_mode(size=(self.width, self.height))
        
        self.clock = pygame.time.Clock()
        self.running = True

       
        self.available_screens = {
            "welcome": screen1.Welcome,
            "winner": screen2.Winner,
            "game_rules": screen3.GameRules,
            "main_menu": screen4.MainMenu
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