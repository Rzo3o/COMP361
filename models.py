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


class Player(Entity):
    def __init__(self, data):
        super().__init__(data["current_q"], data["current_r"], data.get("texture_file"))
        self.hp = data.get("health", 100)
        self.max_hp = data.get("max_health", 100)
        self.hunger = data.get("hunger", 100)
        self.max_hunger = data.get("max_hunger", 100)
        self.xp = data.get("experience", 0)
        self.dead = False

    def move(self, dq, dr):
        self.q += dq
        self.r += dr
        self.hunger = max(0, self.hunger + 1)
        self.hp = 100
        if self.hunger == 0:
            self.take_damage(5)

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.dead = True

    def eat(self, food_value):
        return

    def gain_experience(self, xp):
        return

    def attack(self, target, damage):
        return

    def use_item(self, item):
        return

    def rest(self):
        return

    def interact(self, entity):
        return

    def level_up(self):
        return

    def add_item_to_inventory(self, item):
        return

    def remove_item_from_inventory(self, item):
        return

    def conmplete_level(self, level):
        return

    def respawn(self):
        return

    def equip_item(self, item):
        return

    def unequip_item(self, item):
        return

    def get_combat_power(self):
        # Calculates total damage (Base Strength + Weapon Damage)
        return

    def conquer_tile(self, tile):
        return


class Monster(Entity):
    def __init__(self, data):
        super().__init__(data["current_q"], data["current_r"], data.get("texture_file"))
        self.id = data.get("id")
        self.name = data.get("name", "Unknown")
        self.hp = data.get("health", 50)
        self.damage = data.get("damage", 10)

    def move_towards_player(self, player):
        return

    def attack_player(self, player):
        return

    def take_damage(self, amount):
        return

    def drop_loot(self):
        return

    def is_alive(self):
        return

    def get_distance_to(self, entity):
        return

    def detect_player(self, player, detection_radius):
        return


class Item:
    def __init__(self, data):
        self.id = data.get("id")
        self.name = data.get("name", "Unknown Item")
        self.type = data.get("item_type", "misc")  # weapon, food, artifact
        self.weight = data.get("weight", 0)
        self.damage_bonus = data.get("base_damage", 0)
        self.healing_amount = data.get("healing_amount", 0)
        self.durability = data.get("durability", 100)
        self.max_durability = data.get("max_durability", 100)
        self.texture = data.get("texture_file")

    def use(self, target):
        """Logic for consuming food or using potions."""
        return

    def degrade(self, amount):
        """Reduces durability. Returns True if destroyed."""
        return

    def is_broken(self):
        return
