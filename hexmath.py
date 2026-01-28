import math


class Config:
    GAME_SCALE = 3
    BASE_HEX_RADIUS = 16
    HEX_SIZE = BASE_HEX_RADIUS * GAME_SCALE  # 48 pixels
    HEX_ASPECT_RATIO = 0.87
    CALIB_OFFSET_Y = 16 * GAME_SCALE
    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 800
    CENTER_X = WINDOW_WIDTH // 2
    CENTER_Y = WINDOW_HEIGHT // 2
    VISIBLE_RADIUS = 4  # Fog of War radius


class HexMath:
    @staticmethod
    def hex_to_pixel(q, r, cx=0, cy=0):
        size = Config.HEX_SIZE
        x = size * (3 / 2 * q)
        y = size * math.sqrt(3) * (r + q / 2)
        return (x + cx), (y * Config.HEX_ASPECT_RATIO + cy)

    @staticmethod
    def pixel_to_hex(px, py, cx=0, cy=0):
        x = px - cx
        y = (py - cy) / Config.HEX_ASPECT_RATIO
        size = Config.HEX_SIZE
        q = (2.0 / 3 * x) / size
        r = (-1.0 / 3 * x + math.sqrt(3) / 3 * y) / size
        return HexMath.cube_round(q, r, -q - r)

    @staticmethod
    def cube_round(frac_q, frac_r, frac_s):
        q, r, s = round(frac_q), round(frac_r), round(frac_s)
        q_diff, r_diff, s_diff = abs(q - frac_q), abs(r - frac_r), abs(s - frac_s)
        if q_diff > r_diff and q_diff > s_diff:
            q = -r - s
        elif r_diff > s_diff:
            r = -q - s
        else:
            s = -q - r
        return int(q), int(r)

    @staticmethod
    def get_hex_polygon(cx, cy):
        points = []
        for i in range(6):
            angle_rad = math.radians(60 * i)
            vx = Config.HEX_SIZE * math.cos(angle_rad)
            vy = Config.HEX_SIZE * math.sin(angle_rad)
            points.append(cx + vx)
            points.append(cy + (vy * Config.HEX_ASPECT_RATIO))
        return points

    @staticmethod
    def distance(q1, r1, q2, r2):
        return (abs(q1 - q2) + abs(q1 + r1 - q2 - r2) + abs(r1 - r2)) / 2
