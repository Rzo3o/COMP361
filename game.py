import warnings

# Suppress specific deprecation warnings
warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API")

import pygame
import sys
import os
from GameDB import GameDB
from hexmath import HexMath

# ==========================================
# 1. CONFIGURATION
# ==========================================
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800
GAME_SCALE = 3
BASE_HEX_RADIUS = 16

# --- YOUR CALIBRATED NUMBERS ---
ISO_SQUASH = 0.9280
IMG_SCALE_MODIFIER = 3.010
VERTICAL_OFFSET = -13.5
# -------------------------------

HEX_SIZE = BASE_HEX_RADIUS * GAME_SCALE

# ==========================================
# 2. ASSET MANAGER
# ==========================================
ASSET_CACHE = {}


def get_asset(filename, scale_modifier=IMG_SCALE_MODIFIER):
    """
    Checks the cache for an image. If not found, loads, scales, and caches it.
    scale_modifier: Multiplier of HEX_SIZE.
    """
    if not filename:
        return None

    # Cache Key includes scale so we can have the same rock at size 1.0 and 2.5
    cache_key = (filename, scale_modifier)

    if cache_key in ASSET_CACHE:
        return ASSET_CACHE[cache_key]

    path = os.path.join("assets", filename)
    if not os.path.exists(path):
        path = filename
        if not os.path.exists(path):
            print(f"Warning: Could not find asset {filename}")
            return None

    try:
        img = pygame.image.load(path).convert_alpha()

        original_width = img.get_width()

        # Calculate target width based on the SPECIFIC scale requested
        target_width = int(HEX_SIZE * scale_modifier)

        scale_factor = target_width / original_width
        new_size = (
            int(original_width * scale_factor),
            int(img.get_height() * scale_factor),
        )
        scaled_img = pygame.transform.scale(img, new_size)

        ASSET_CACHE[cache_key] = scaled_img
        return scaled_img

    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return None


# ==========================================
# 3. MAIN GAME LOOP
# ==========================================
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Isometric Hex Engine")
    clock = pygame.time.Clock()

    hex_math = HexMath(HEX_SIZE)
    db = GameDB()

    # Load Map Data
    # SELECT * will now include 'prop_scale' and 'prop_y_shift'
    raw_tiles = db.get_map()
    tiles = [dict(row) for row in raw_tiles]

    # Camera Setup
    camera_offset = [SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2]

    # PRE-CALCULATE POSITIONS
    for tile in tiles:
        tx, ty = hex_math.hex_to_pixel(tile["q"], tile["r"])
        tile["pixel_x"] = tx
        tile["pixel_y"] = ty * ISO_SQUASH

    # Sort by Y for Painter's Algorithm (Draw back-to-front)
    tiles.sort(key=lambda t: t["pixel_y"])

    running = True
    while running:
        # 1. INPUT
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    camera_offset[0] += 20
                if event.key == pygame.K_RIGHT:
                    camera_offset[0] -= 20
                if event.key == pygame.K_UP:
                    camera_offset[1] += 20
                if event.key == pygame.K_DOWN:
                    camera_offset[1] -= 20

        # 2. DRAW
        screen.fill((30, 30, 30))

        for tile in tiles:
            # Apply Camera
            draw_x = tile["pixel_x"] + camera_offset[0]
            draw_y = tile["pixel_y"] + camera_offset[1]

            # Culling (Performance optimization)
            if not (
                -100 < draw_x < SCREEN_WIDTH + 100
                and -100 < draw_y < SCREEN_HEIGHT + 100
            ):
                continue

            # Retrieve Filenames
            base_file = tile.get("texture_file")
            prop_file = tile.get("prop_texture_file") or tile.get(
                "overlay_texture_file"
            )

            # --- LAYER 1: BASE TERRAIN ---
            if base_file:
                # Base tiles typically use the global IMG_SCALE_MODIFIER
                base_img = get_asset(base_file, scale_modifier=IMG_SCALE_MODIFIER)
                if base_img:
                    ox = base_img.get_width() // 2
                    oy = (base_img.get_height() // 2) - VERTICAL_OFFSET
                    screen.blit(base_img, (draw_x - ox, draw_y - oy))
            else:
                points = hex_math.get_hex_corners(draw_x, draw_y)
                pygame.draw.polygon(screen, (50, 50, 50), points, 1)

            # --- LAYER 2: PROP / OVERLAY ---
            if prop_file:
                # 1. Get Scale from DB (Default to 1.0 if not set)
                p_scale = tile.get("prop_scale")
                if p_scale is None:
                    p_scale = 1.0

                # 2. Get Shift from DB (Default to 0)
                p_shift = tile.get("prop_y_shift")
                if p_shift is None:
                    p_shift = 0

                # 3. Load Asset with SPECIFIC Scale
                prop_img = get_asset(prop_file, scale_modifier=p_scale)

                if prop_img:
                    # Center the image on the hex
                    ox = prop_img.get_width() // 2
                    oy = prop_img.get_height() // 2

                    # Apply the DB Shift
                    # Subtracting shift moves it UP (because Y goes down in screens)
                    final_y = draw_y - oy - p_shift

                    screen.blit(prop_img, (draw_x - ox, final_y))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
