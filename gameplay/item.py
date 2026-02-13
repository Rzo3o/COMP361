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
        pass

    def degrade(self, amount):
        """Reduces durability. Returns True if destroyed."""
        pass

    def is_broken(self):
        return self.durability <= 0
