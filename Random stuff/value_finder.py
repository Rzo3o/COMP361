import pygame
import sqlite3
import os
import math

SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 900

GAME_SCALE = 3
BASE_HEX_RADIUS = 16
HEX_SIZE = BASE_HEX_RADIUS * GAME_SCALE
cal_values = {
    "ROTATION_Z": 0.0,  # Spin (0 for flat top, 30 for pointy)
    "ROTATION_X": 1.0,  # Tilt (1.0 = flat 2D, <1.0 = tilted back)
    "SQUASH_X": 1.00,  # Width modifier
    "SQUASH_Y": 1.00,  # Height modifier
    "IMG_SCALE_MODIFIER": 3.0,
    "VERTICAL_OFFSET": 0,
}
ASSET_CACHE = {}


def get_db_connection():
    if not os.path.exists("game_data.db"):
        return None
    conn = sqlite3.connect("game_data.db")
    conn.row_factory = sqlite3.Row
    return conn


def load_map_data(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM map_tiles")
        return [dict(row) for row in cursor.fetchall()]
    except:
        return []


def get_asset(filename, scale_mod):
    if not filename:
        return None
    key = (filename, scale_mod)
    if key in ASSET_CACHE:
        return ASSET_CACHE[key]

    paths = [
        os.path.join("assets", filename),
        os.path.join("assets/definitions/tiles", filename),
        os.path.join("assets/definitions/props", filename),
        filename,
    ]

    for p in paths:
        if os.path.exists(p):
            try:
                img = pygame.image.load(p).convert_alpha()
                target_width = int(HEX_SIZE * scale_mod)
                orig_w = img.get_width()
                scale_ratio = target_width / orig_w
                new_size = (
                    int(orig_w * scale_ratio),
                    int(img.get_height() * scale_ratio),
                )
                scaled_img = pygame.transform.scale(img, new_size)
                ASSET_CACHE[key] = scaled_img
                return scaled_img
            except:
                pass
    return None


def rotate_point(x, y, degrees):
    rad = math.radians(degrees)
    c, s = math.cos(rad), math.sin(rad)
    return x * c - y * s, x * s + y * c


def project_hex(q, r, sq_x, sq_y, rot_z, tilt_x):
    x = HEX_SIZE * (3 / 2 * q)
    y = HEX_SIZE * math.sqrt(3) * (r + q / 2)
    x *= sq_x
    y *= sq_y
    x, y = rotate_point(x, y, rot_z)
    y *= tilt_x

    return x, y


def get_corners(cx, cy, sq_x, sq_y, rot_z, tilt_x):
    points = []
    for i in range(6):
        angle_deg = 60 * i
        angle_rad = math.radians(angle_deg)
        lx = HEX_SIZE * math.cos(angle_rad)
        ly = HEX_SIZE * math.sin(angle_rad)
        lx *= sq_x
        ly *= sq_y
        rx, ry = rotate_point(lx, ly, rot_z)
        ry *= tilt_x

        points.append((cx + rx, cy + ry))
    return points


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Surface Alignment Tool")
    font = pygame.font.SysFont("Consolas", 14, bold=True)
    clock = pygame.time.Clock()

    conn = get_db_connection()
    tiles = load_map_data(conn) if conn else []
    if conn:
        conn.close()
    if not tiles:
        tiles = [{"q": 0, "r": 0, "texture_file": "default.png"}]

    cam_x = SCREEN_WIDTH // 2
    cam_y = SCREEN_HEIGHT // 2
    show_wireframe = True

    running = True
    while running:
        keys = pygame.key.get_pressed()
        shift = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

        fine = 0.001 if shift else 0.01
        rot_spd = 0.1 if shift else 1.0
        mov_spd = 0.1 if shift else 0.5
        cam_spd = 5 if shift else 10

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                show_wireframe = not show_wireframe
        if keys[pygame.K_q]:
            cal_values["ROTATION_Z"] += rot_spd
        if keys[pygame.K_a]:
            cal_values["ROTATION_Z"] -= rot_spd
        if keys[pygame.K_w]:
            cal_values["ROTATION_X"] += fine
        if keys[pygame.K_s]:
            cal_values["ROTATION_X"] -= fine
        if keys[pygame.K_e]:
            cal_values["SQUASH_X"] += fine
        if keys[pygame.K_d]:
            cal_values["SQUASH_X"] -= fine
        if keys[pygame.K_r]:
            cal_values["SQUASH_Y"] += fine
        if keys[pygame.K_f]:
            cal_values["SQUASH_Y"] -= fine
        if keys[pygame.K_t]:
            cal_values["IMG_SCALE_MODIFIER"] += fine
        if keys[pygame.K_g]:
            cal_values["IMG_SCALE_MODIFIER"] -= fine
        if keys[pygame.K_y]:
            cal_values["VERTICAL_OFFSET"] += mov_spd
        if keys[pygame.K_h]:
            cal_values["VERTICAL_OFFSET"] -= mov_spd
        if keys[pygame.K_UP]:
            cam_y += cam_spd
        if keys[pygame.K_DOWN]:
            cam_y -= cam_spd
        if keys[pygame.K_LEFT]:
            cam_x += cam_spd
        if keys[pygame.K_RIGHT]:
            cam_x -= cam_spd

        if keys[pygame.K_t] or keys[pygame.K_g]:
            ASSET_CACHE.clear()
        screen.fill((40, 40, 45))

        display_tiles = []
        for t in tiles:
            tx, ty = project_hex(
                t["q"],
                t["r"],
                cal_values["SQUASH_X"],
                cal_values["SQUASH_Y"],
                cal_values["ROTATION_Z"],
                cal_values["ROTATION_X"],
            )
            display_tiles.append(
                {
                    "data": t,
                    "x": int(tx + cam_x),
                    "y": int(ty + cam_y),
                    "z_index": ty,  # Simple Z-sort
                }
            )

        display_tiles.sort(key=lambda x: x["z_index"])

        for item in display_tiles:
            x, y = item["x"], item["y"]
            t = item["data"]
            tex = t.get("texture_file") or "default.png"
            img = get_asset(tex, cal_values["IMG_SCALE_MODIFIER"])
            if img:
                ix = x - (img.get_width() // 2)
                iy = y - (img.get_height() // 2) - cal_values["VERTICAL_OFFSET"]
                screen.blit(img, (ix, iy))
            if show_wireframe:
                corners = get_corners(
                    x,
                    y,
                    cal_values["SQUASH_X"],
                    cal_values["SQUASH_Y"],
                    cal_values["ROTATION_Z"],
                    cal_values["ROTATION_X"],
                )
                pygame.draw.polygon(screen, (255, 50, 50), corners, 2)
                pygame.draw.circle(screen, (255, 255, 0), (x, y), 2)
        ui_y = 10
        texts = [
            ("GRID SURFACE ALIGNMENT", (255, 255, 255)),
            ("----------------------", (150, 150, 150)),
            (
                f"[Q/A] ROTATION (Z): {cal_values['ROTATION_Z']:.1f}° (Spin)",
                (255, 255, 0),
            ),
            (
                f"[W/S] TILT (X):     {cal_values['ROTATION_X']:.3f} (View Angle)",
                (0, 255, 0),
            ),
            (f"[E/D] WIDTH:        {cal_values['SQUASH_X']:.3f}", (0, 255, 255)),
            (f"[R/F] HEIGHT:       {cal_values['SQUASH_Y']:.3f}", (255, 100, 100)),
            ("----------------------", (150, 150, 150)),
            (
                f"[Y/H] OFFSET:       {cal_values['VERTICAL_OFFSET']:.1f} (Shift Image)",
                (200, 200, 200),
            ),
            (
                f"[T/G] SCALE:        {cal_values['IMG_SCALE_MODIFIER']:.3f}",
                (100, 100, 255),
            ),
        ]

        pygame.draw.rect(screen, (20, 20, 20), (5, 5, 350, 200))
        for txt, col in texts:
            screen.blit(font.render(txt, True, col), (15, ui_y))
            ui_y += 20

        pygame.draw.line(screen, (100, 100, 100), (cam_x, 0), (cam_x, SCREEN_HEIGHT))
        pygame.draw.line(screen, (100, 100, 100), (0, cam_y), (SCREEN_WIDTH, cam_y))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
