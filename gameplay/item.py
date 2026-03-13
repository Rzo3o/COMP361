class Item:
    def __init__(self, data):
        self.id = data.get("id")
        self.name = data.get("name", "Unknown Item")
        self.type = data.get("item_type", "misc")  # weapon, food, artifact
        self.weight = data.get("weight", 0)
        self.damage_bonus = data.get("base_damage", 0)
        self.healing_amount = data.get("healing_amount", 0)
        self.hunger_restore = data.get("hunger_restore", 0)
        self.durability = data.get("durability", 100)
        self.max_durability = data.get("max_durability", 100)
        self.texture = data.get("texture_file")

    def use(self, player):
        """Consume food/potion: heal HP and restore hunger."""
        if self.type == "food":
            player.hp = min(player.max_hp, player.hp + self.healing_amount)
            player.hunger = min(player.max_hunger, player.hunger + self.hunger_restore)
            # item was consumed
            return True
        # not consumable
        return False

    def degrade(self, amount):
        self.durability -= amount

    def is_broken(self):
        return self.durability <= 0
