class Tile:
    def __init__(self, data):
        self.id = data.get("id")
        self.q = data["q"]
        self.r = data["r"]
        self.type = data.get("tile_type", "grass")
        self.texture = data.get("texture_file")
        self.prop_texture = data.get("prop_texture_file")
        self.prop_scale = data.get("prop_scale", 1.0)
        self.prop_shift = data.get("prop_y_shift", 0)
        self.passable = bool(data.get("is_permanently_passable", 1))
        self.discovered = bool(data.get("is_discovered", 0))
        self.unlocked = bool(data.get("is_unlocked", 1))
        self.conquered = bool(data.get("is_conquered", 0))


class Entity:
    def __init__(self, q, r, texture=None):
        self.q = q
        self.r = r
        self.texture = texture
