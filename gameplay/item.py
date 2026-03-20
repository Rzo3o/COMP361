class Item:
    # Valid equipment slots
    EQUIPMENT_SLOTS = ("weapon", "head", "chest", "legs")

    def __init__(self, data):
        self.id = data.get("id")
        self.name = data.get("name", "Unknown Item")
        self.description = data.get("description", "")
        self.type = data.get("item_type", "misc")  # weapon, armor, food, artifact
        self.slot = data.get("slot")  # weapon, head, chest, legs
        self.weight = data.get("weight", 0)
        self.damage_bonus = data.get("base_damage", 0)
        self.defense = data.get("defense", 0)
        self.healing_amount = data.get("healing_amount", 0)
        self.hunger_restore = data.get("hunger_restore", 0)
        self.durability = data.get("durability", 100)
        self.max_durability = data.get("max_durability", 100)
        self.power_bonus = data.get("power_bonus", 0)
        self.texture = data.get("texture_file")

    @property
    def is_equippable(self):
        """Returns True if this item can be equipped."""
        return self.slot in self.EQUIPMENT_SLOTS

    def use(self, player):
        """Consume food/potion: heal HP and restore hunger."""
        if self.type == "food":
            player.hp = min(player.max_hp, player.hp + self.healing_amount)
            player.hunger = min(player.max_hunger, player.hunger + self.hunger_restore)
            return True
        return False

    def degrade(self, amount=1):
        """Reduce durability by amount. Called after attacks or when taking hits."""
        self.durability = max(0, self.durability - amount)

    def is_broken(self):
        return self.durability <= 0