import pygame
import os

pygame.init()

# -----------------------------
# MATCH YOUR REAL GAME WINDOW
# -----------------------------
screen_w, screen_h = pygame.display.get_desktop_sizes()[0]
window_h = screen_h - 60
screen = pygame.display.set_mode((screen_w, window_h), pygame.RESIZABLE)
pygame.display.set_caption("Decoration Editor")

BG_COLOR = (30, 30, 30)

# -----------------------------
# ALL IMAGES YOU USE IN YOUR GAME
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(BASE_DIR, "..", "assets", "assetBank", "Hex Tiles")

IMAGE_NAMES = [
    "Grass.png",
    "Grass.png",
    "Grass_Pine.png",
    "Magic_Crystals.png",
    "FrosenWater_Lilypads.png",
    "Magic.png",
    "Snow_Trees.png",
    "Snow_Snowman.png",
    "Grass_Plants2.png",
]

# -----------------------------
# INITIAL POSITIONS (FIXED)
# Images now spawn across screen width
# -----------------------------
decorations = []

margin = 120
usable_width = screen_w - (margin * 2)
spacing = usable_width // (len(IMAGE_NAMES) + 1)

start_y = window_h // 2 - 300

for i, name in enumerate(IMAGE_NAMES):
    x = margin + spacing * (i + 1)
    y = start_y
    decorations.append([name, x, y, 0, 3.0])

selected = 0


def load_and_transform(name, angle, scale):
    path = os.path.join(ASSET_DIR, name)
    img = pygame.image.load(path).convert_alpha()

    w, h = img.get_size()
    img = pygame.transform.smoothscale(img, (int(w * scale), int(h * scale)))
    img = pygame.transform.rotate(img, angle)
    return img


running = True
drag_offset_x = 0
drag_offset_y = 0
dragging = False

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Switch selected image
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                selected = (selected + 1) % len(decorations)

            if event.key == pygame.K_LEFT:
                selected = (selected - 1) % len(decorations)

            # Rotate
            if event.key == pygame.K_q:
                decorations[selected][3] -= 5

            if event.key == pygame.K_e:
                decorations[selected][3] += 5

            # Print final data
            if event.key == pygame.K_x:
                print("\nFINAL DECORATION DATA:")
                for d in decorations:
                    print(tuple(d))
                print("\nCopy these into your game.\n")

        # Scale with mouse wheel
        if event.type == pygame.MOUSEWHEEL:
            decorations[selected][4] += event.y * 0.1
            decorations[selected][4] = max(0.1, decorations[selected][4])

        # Start dragging
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mx, my = event.pos
                name, x, y, angle, scale = decorations[selected]

                img = load_and_transform(name, angle, scale)
                rect = img.get_rect(center=(x, y))

                if rect.collidepoint(mx, my):
                    dragging = True
                    drag_offset_x = x - mx
                    drag_offset_y = y - my

        # Stop dragging
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                dragging = False

        # Drag movement
        if event.type == pygame.MOUSEMOTION and dragging:
            mx, my = event.pos
            decorations[selected][1] = mx + drag_offset_x
            decorations[selected][2] = my + drag_offset_y

    # Draw
    screen.fill(BG_COLOR)
    
    for i, (name, x, y, angle, scale) in enumerate(decorations):

        img = load_and_transform(name, angle, scale)
        rect = img.get_rect(center=(x, y))

        # Highlight selected
        if i == selected:
            pygame.draw.rect(screen, (255, 255, 0), rect, 3)

        screen.blit(img, rect)

    pygame.display.flip()
   

pygame.quit()

