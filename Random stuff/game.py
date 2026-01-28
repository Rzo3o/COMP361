import warnings


warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API")

import pygame
import sys
import os
import math
from GameDB import GameDB
from hexmath import HexMath


SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800
GAME_SCALE = 3
BASE_HEX_RADIUS = 16


CALIB_ROTATION_Z = -22.0  # Degrees
CALIB_TILT_X = 0.54  # Y-Axis Squash (Perspective)
CALIB_WIDTH_MOD = 1.4  # Grid Spacing Width Multiplier
CALIB_HEIGHT_MOD = 1.4  # Grid Spacing Height Multiplier
CALIB_OFFSET_Y = -22  # Sprite Vertical Offset
CALIB_IMG_SCALE = 2.7  # Sprite Scale Multiplier
HEX_SIZE = BASE_HEX_RADIUS * GAME_SCALE


ASSET_CACHE = {}


def get_asset(filename, scale_modifier=CALIB_IMG_SCALE):
    """
    Checks the cache for an image. If not found, loads, scales, and caches it.
    scale_modifier: Multiplier of HEX_SIZE.
    """
    if not filename:
        return None

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


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Isometric Hex Engine")
    clock = pygame.time.Clock()

    hex_math = HexMath(HEX_SIZE)
    db = GameDB()

    raw_tiles = db.get_map()
    tiles = [dict(row) for row in raw_tiles]

    camera_offset = [SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2]

    rad_z = math.radians(CALIB_ROTATION_Z)
    cos_z = math.cos(rad_z)
    sin_z = math.sin(rad_z)

    for tile in tiles:

        q = tile["q"]
        r = tile["r"]

        raw_x = HEX_SIZE * (1.5 * q)
        raw_y = HEX_SIZE * (math.sqrt(3) / 2 * q + math.sqrt(3) * r)

        mod_x = raw_x * CALIB_WIDTH_MOD
        mod_y = raw_y * CALIB_HEIGHT_MOD

        rot_x = mod_x * cos_z - mod_y * sin_z
        rot_y = mod_x * sin_z + mod_y * cos_z

        final_x = rot_x
        final_y = rot_y * CALIB_TILT_X

        tile["pixel_x"] = final_x
        tile["pixel_y"] = final_y

    tiles.sort(key=lambda t: t["pixel_y"])

    running = True
    while running:

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

        screen.fill((30, 30, 30))

        for tile in tiles:

            draw_x = tile["pixel_x"] + camera_offset[0]
            draw_y = tile["pixel_y"] + camera_offset[1]

            if not (
                -150 < draw_x < SCREEN_WIDTH + 150
                and -150 < draw_y < SCREEN_HEIGHT + 150
            ):
                continue

            base_file = tile.get("texture_file")
            prop_file = tile.get("prop_texture_file") or tile.get(
                "overlay_texture_file"
            )

            if base_file:

                base_img = get_asset(base_file, scale_modifier=CALIB_IMG_SCALE)
                if base_img:
                    ox = base_img.get_width() // 2

                    half_h = base_img.get_height() // 2

                    total_y = draw_y - CALIB_OFFSET_Y - half_h

                    screen.blit(base_img, (draw_x - ox, total_y))
            else:

                pygame.draw.circle(screen, (50, 50, 50), (int(draw_x), int(draw_y)), 5)

            if prop_file:

                db_prop_scale = tile.get("prop_scale")
                if db_prop_scale is None:
                    db_prop_scale = 1.0

                final_prop_scale = CALIB_IMG_SCALE * db_prop_scale

                db_prop_shift = tile.get("prop_y_shift")
                if db_prop_shift is None:
                    db_prop_shift = 0

                prop_img = get_asset(prop_file, scale_modifier=final_prop_scale)

                if prop_img:
                    ox = prop_img.get_width() // 2
                    oy = prop_img.get_height() // 2

                    total_y = draw_y - oy - CALIB_OFFSET_Y - db_prop_shift

                    screen.blit(prop_img, (draw_x - ox, total_y))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
