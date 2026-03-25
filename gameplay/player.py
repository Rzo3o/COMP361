from gameplay.models import Entity
from gameplay.item import Item


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
        self.base_damage = 10
        self.base_defense = 100

        # Equipment slots: slot_name -> Item or None
        self.equipment = {
            "weapon": None,
            "head": None,
            "chest": None,
            "legs": None,
        }

        # Inventory for consumable items
        self.inventory = []

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

    def load_inventory(self, db, session_id):
        """Load inventory from DB into Item objects."""
        rows = db.load_inventory(session_id)
        self.inventory = []
        for row in rows:
            item = Item(row)
            item.quantity = row.get("quantity", 1)
            item.equipped = bool(row.get("is_equipped", 0))
            self.inventory.append(item)
        self.apply_equipment()

    def apply_equipment(self):
        """Sync equipped items from inventory into player equipment slots."""
        # Clear all slots first
        for slot in self.equipment:
            self.equipment[slot] = None
        # Apply equipped items
        for item in self.inventory:
            if item.equipped and item.is_equippable:
                self.equipment[item.slot] = item

    def use_item(self, index, db, session_id):
        if not self.inventory or index >= len(self.inventory):
            return False
        item = self.inventory[index]

        if item.type == "food":
            if item.use(self):
                db.remove_item(session_id, item.id)
                db.save_player(session_id, self)
                self.load_inventory(db, session_id)
                return True

        elif item.is_equippable:
            db.toggle_equip(session_id, item.id)
            self.load_inventory(db, session_id)
            return True
        return False

    def drop_item(self, index, db, session_id):
        if not self.inventory or index >= len(self.inventory):
            return False
        item = self.inventory[index]
        db.remove_item(session_id, item.id, quantity=1)
        self.load_inventory(db, session_id)
        return True

    def add_items(self, *items):
        self.inventory.extend(items)
        self.apply_equipment()

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

    def attack_monster(self, monster):
        """
        Player attacks a monster.
        Returns the damage dealt
        """
        damage = self.total_damage

        if hasattr(monster, "take_damage"):
            return monster.take_damage(damage)
        else:
            monster.hp -= damage
            if monster.hp <= 0:
                monster.hp = 0
            return damage
        
    def is_alive(self) -> bool:
        return (not self.dead) and self.hp > 0