from gameplay.models import Entity


class Player(Entity):
    def __init__(self, data):
        q = data.get("current_q", 0)
        r = data.get("current_r", 0)
        texture = data.get("texture_file")
        super().__init__(q, r, texture)

        self.hp = data.get("health", 100)
        self.max_hp = data.get("max_health", 100)
        self.hunger = data.get("hunger", 100)
        self.max_hunger = data.get("max_hunger", 100)
        self.xp = data.get("experience", 0)
        self.dead = False

        # Base stats (without equipment)
        self.base_damage = 5
        self.base_defense = 0

        # Equipment slots: slot_name -> Item or None
        self.equipment = {
            "weapon": None,
            "head": None,
            "chest": None,
            "legs": None,
        }

    @property
    def total_damage(self):
        """Base damage + weapon bonus."""
        bonus = 0
        weapon = self.equipment.get("weapon")
        if weapon and not weapon.is_broken():
            bonus = weapon.damage_bonus
        return self.base_damage + bonus

    @property
    def total_defense(self):
        """Sum of defense from all equipped armor pieces."""
        total = self.base_defense
        for slot, item in self.equipment.items():
            if item and not item.is_broken():
                total += item.defense
        return total

    def equip(self, item):
        """Equip an item into its slot. Returns the previously equipped item or None."""
        if not item.is_equippable:
            return None
        old = self.equipment.get(item.slot)
        self.equipment[item.slot] = item
        return old

    def unequip(self, slot):
        """Remove item from a slot. Returns the removed item or None."""
        old = self.equipment.get(slot)
        if old:
            self.equipment[slot] = None
        return old

    def move(self, dq, dr):
        self.q += dq
        self.r += dr
        self.hunger = max(0, self.hunger - 1)

        if self.hunger == 0:
            self.take_damage(5)

    def take_damage(self, amount):
        """Apply damage reduced by total defense. Minimum 1 damage."""
        reduced = max(1, amount - self.total_defense)
        self.hp -= reduced
        if self.hp <= 0:
            self.hp = 0
            self.dead = True
        return reduced