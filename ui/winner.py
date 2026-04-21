from ui.end_screen import EndScreen

ORIGINAL_SCREEN_W = 1536
ORIGINAL_SCREEN_H = 1024

class Winner(EndScreen):
    
    decoration_images = [
        ('sprite1.png', 1295, 580, 0, 8),
        ('Grass.png', 942/ORIGINAL_SCREEN_W, 491/ORIGINAL_SCREEN_H, -15, 2.6),
        ('Grass_Pine.png', 200/ORIGINAL_SCREEN_W, 350/ORIGINAL_SCREEN_H, -15, 3.4),
        ('Magic_Crystals.png', 270/ORIGINAL_SCREEN_W, 448/ORIGINAL_SCREEN_H, 20, 3.2),
        ('FrosenWater_Lilypads.png', 140/ORIGINAL_SCREEN_W, 460/ORIGINAL_SCREEN_H, 10, 2.2),
        ('Magic.png', 849/ORIGINAL_SCREEN_W, 474/ORIGINAL_SCREEN_H, -20, 1.9),
        ('Snow_Trees.png', 913/ORIGINAL_SCREEN_W, 378/ORIGINAL_SCREEN_H, 15, 3.0)
    ]

   