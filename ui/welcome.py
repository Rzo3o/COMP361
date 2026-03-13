import pygame
import sys
import os
from pygame.draw import rect


class Welcome:
    def __init__(self):
        pygame.init()

        # window size full screen 
        self.width, self.height = pygame.display.get_desktop_sizes()[0]
        self.screen = pygame.display.set_mode(size=(self.width, self.height - 60), flags=pygame.RESIZABLE)
        # bit smaller for title bar and bottom icons
    
        
        pygame.display.set_caption("Welcome Beyond")
        self.small_font = pygame.font.Font(size=190)
        self.clock = pygame.time.Clock()
        self.running = True
     
        # Colors
        #red, green, blue
        self.bg_color = (30, 30, 30)
        self.text_color = (80, 220, 120)

        self.decoration_images = [
            ('Water_Duck.png', 98, 68, 30, 4.7),
            ('Dirt_Pumpkins.png', 166, 372, 25, 3.7),
            ('Grass_Plants.png', 94, 247, 60, 2.8),
            ('Snow_Trees.png', 1270, 587, 25, 4.1),
            ('Magic_Crystals.png', 1421, 614, 40, 2.8),
            ('FrosenWater_Lilypads.png', 1297, 732, 20, 2.9),
            ('Magic.png', 265, 152, 20, 2.5),
            ('Snow.png', 286, 273, 35, 4.0),
            ('Grass_Plants2.png', 1452, 776, 30, 4.3)
        ]
        
    
    def draw(self):
        """
        Draw the welcome screen with title and images.
        Input: None
        Output: None
        """
        self.screen.fill(self.bg_color)
        
        # Title
        title = self.small_font.render("Welcome Beyond", True, self.text_color)
        title_rect = title.get_rect(center=(self.width // 2, self.height // 2)) # middle
        self.screen.blit(source=title, dest=title_rect) # dest source draw position
        
        # images
        for image_name, x, y, angle, scale in self.decoration_images:
            self.draw_image(image_name, x, y, angle, scale)


        pygame.display.flip()
    

    def draw_image(self, image_name: str, x: int, y: int, angle: int, scale: float):
        """
        draw image on the screen
        Inputs:
            image_name(str): name of the image file 
            x(int): x position
            y(int): y position
            angle(int): rotation angle in degrees
            scale(float): scaling factor (e.g., 0.5 for half size, 2 for double size)
        Output: None
        """
        # path
        base_dir = os.path.dirname(os.path.abspath(__file__)) # directory of this script
        image_path = os. path.join(base_dir, '..', 'assets', 'assetBank', 'Hex Tiles', image_name)
        
        image = pygame.image.load(image_path)
        
        # adjust image
        original_w, original_h = image.get_size()
        scaled_image = pygame.transform.scale(image, (int(original_w * scale), int(original_h * scale)))
        rotated_image = pygame.transform.rotate(scaled_image, angle)
        rect = rotated_image.get_rect(center=(x, y))
        self.screen.blit(rotated_image, rect)
        
   
    # main loop for testing
    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                       
            self.draw()
        
        pygame.quit()

if __name__ == "__main__":
    welcome_screen= Welcome()
    welcome_screen.run()
    