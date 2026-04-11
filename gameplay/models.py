class Tile:
    def __init__(self, data):
        self.id = data.get("id")
        self.q = data["q"]
        self.r = data["r"]
        self.type = data.get("tile_type", "grass")
        self.texture = data.get("texture_file")
        self.prop_texture = data.get("prop_texture_file")
        self.prop_scale = data.get("prop_scale", 1.0)
        self.prop_x_shift = data.get("prop_x_shift", 0)
        self.prop_shift = data.get("prop_y_shift", 0)
        self.passable = bool(data.get("is_permanently_passable", 1))
        self.discovered = bool(data.get("is_discovered", 0))
        #self.unlocked = bool(data.get("is_unlocked", 1))
        
        self.level = data.get("level", 1)

        #level 1 tiles start unlocked higher levels start locked
        raw_unlocked = data.get("is_unlocked")
        if raw_unlocked is None:
            self.unlocked = (self.level == 1)
        else:
            self.unlocked = bool(raw_unlocked)

        self.conquered = bool(data.get("is_conquered", 0))


class Entity:
    def __init__(self, q, r, texture=None):
        self.q = q
        self.r = r
        self.texture = texture

    # Hex utilities
    @staticmethod
    def hex_distance(q1: int, r1: int, q2: int, r2: int) -> int:
        """Axial hex distance."""
        dq = q2 - q1
        dr = r2 - r1
        return int((abs(dq) + abs(dq + dr) + abs(dr)) / 2)

    def neighbors(self):
        """Yield axial neighbor coordinates."""
        for dq, dr in self.HEX_DIRS:
            yield self.q + dq, self.r + dr

class CircleExplosion:
    def __init__(self, q: int, r: int, color: tuple, target_radius_hex: int):
        self.q = q
        self.r = r
        self.color = color
        
        self.max_pixel_radius = target_radius_hex * 80 + 30 
        
        self.current_radius = 5.0
        self.expand_speed = self.max_pixel_radius / 15.0 
        self.dead = False

    def update(self, *args):
        self.current_radius += self.expand_speed
        
        if self.current_radius >= self.max_pixel_radius:
            self.dead = True