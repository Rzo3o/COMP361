from gameplay.models import Entity
from gameplay.item import Item


class Player(Entity):
    def __init__(self, data):
        q = data.get("current_q", 0)
        r = data.get("current_r", 0)
        super().__init__(q, r)

        self.data = data
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

        animations = self.data.get("animations", {})

        # Animation runtime state
        self.anim_state = "idle"
        self.anim_tick = 0

        self.texture = animations.get("idle", {}).get("texture")
        if not self.texture:
            print("[Player init WARNING] no idle texture found in animations!")
            self.texture = None

        # move interpolation runtime
        self.is_moving = False
        self.move_from_q = self.q
        self.move_from_r = self.r
        self.move_to_q = self.q
        self.move_to_r = self.r
        self.move_progress = 1.0
        self.move_speed = 0.25
        self.pending_q = self.q
        self.pending_r = self.r

        self.is_attacking = False

        # Hit frame attack variables
        self.pending_attack_target = None
        self.pending_attack_damage = 0
        self.attack_damage_applied = False
        self.attack_hit_frame = 4 

        # Damage flash timer
        self.damage_flash_timer = 0

        # debug
        print("[Player init] data keys:", data.keys())
        print("[Player init] texture_file:", data.get("texture_file"))
        print("[Player init] animations:", data.get("animations"))

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
        # Apply equipped items
        for item in self.inventory:
            if item.equipped and item.is_equippable and self.equipment.get(item.slot) is None:
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
        print([item.name for item in items])
        self.inventory.extend(items)
        #self.apply_equipment()
        #print([item.name for item in self.equipment.values()])

    def start_move(self, dq, dr):
        """Start a tile-to-tile move animation"""
        if self.is_moving or self.is_attacking:
            return

        new_q = self.q + dq
        new_r = self.r + dr

        self.move_from_q = self.q
        self.move_from_r = self.r
        self.move_to_q = new_q
        self.move_to_r = new_r

        # update logical position immediately
        self.q = new_q
        self.r = new_r

        self.move_progress = 0.0
        self.is_moving = True
        self.set_anim_state("move", reset_frame=True)

        self.hunger = max(0, self.hunger - 1)
        if self.hunger == 0:
            self.take_damage(5)

    def move(self, dq, dr):
        self.start_move(dq, dr)

    def take_damage(self, amount):
        """Apply damage reduced by total defense. Minimum 1 damage."""
        reduced = max(1, amount - self.total_defense)
        self.hp -= reduced

        self.damage_flash_timer = 3
        if self.hp <= 0:
            self.hp = 0
            self.dead = True
        return reduced

    def attack_monster(self, monster):
        """
        Player attacks a monster.
        Returns the damage dealt
        """
        self.is_attacking = True
        self.set_anim_state("attack", reset_frame=True)

        damage = self.total_damage

        # Save the target to apply damage later in update_animation
        self.pending_attack_target = monster
        self.pending_attack_damage = damage
        self.attack_damage_applied = False

        return damage
        
    def get_texture_for_state(self, state):
        animations = self.data.get("animations", {})
        state_anim = animations.get(state, {})
        if state_anim.get("texture"):
            return state_anim["texture"]

        idle_anim = animations.get("idle", {})
        if idle_anim.get("texture"):
            return idle_anim["texture"]

        return self.texture
    
    def set_anim_state(self, state, reset_frame=True):
        """Change animation state"""
        if self.anim_state == state and not reset_frame:
            return

        self.anim_state = state
        self.texture = self.get_texture_for_state(state)

        if reset_frame:
            self.anim_tick = 0

    def is_alive(self) -> bool:
        return (not self.dead) and self.hp > 0
    
    def update_animation(self, asset_manager):
        """
        Update player animation state.

        States handled:
        - idle: loops
        - move: interpolates from one tile to another, then returns to idle
        - attack: plays once, then returns to idle
        """
        animations = getattr(self, "data", {}).get("animations", {}) if hasattr(self, "data") else {}
        anim_cfg = animations.get(self.anim_state) or animations.get("idle")

        if not anim_cfg:
            return

        texture = anim_cfg.get("texture")
        if not texture:
            return

        meta = asset_manager.anim_metadata.get(texture)
        if not meta:
            return

        frame_count = meta.get("count", 1)

        # MOVE animation
        if self.anim_state == "move":
            if self.is_moving:
                self.move_progress += self.move_speed
                if self.move_progress >= 1.0:
                    self.move_progress = 1.0
                    self.is_moving = False

            self.anim_tick += 1
            if self.anim_tick >= frame_count:
                self.anim_tick = 0

            if not self.is_moving:
                self.set_anim_state("idle", reset_frame=True)

            return

        # Apply damage at specific hit frame
        if self.anim_state == "attack":
            if (not self.attack_damage_applied 
                and self.pending_attack_target is not None 
                and self.anim_tick >= self.attack_hit_frame):
                
                # Apply the saved damage to the monster
                if hasattr(self.pending_attack_target, "take_damage"):
                    self.pending_attack_target.take_damage(self.pending_attack_damage)
                else:
                    self.pending_attack_target.hp -= self.pending_attack_damage
                    if self.pending_attack_target.hp <= 0:
                        self.pending_attack_target.hp = 0
                        
                # Mark as applied so it doesn't hit multiple times
                self.attack_damage_applied = True

        # ATTACK animation
        self.anim_tick += 1

        if self.anim_tick >= frame_count:
            if self.anim_state == "attack":
                
                self.is_attacking = False
                # Reset attack variables when animation ends
                self.pending_attack_target = None
                self.pending_attack_damage = 0
                self.attack_damage_applied = False
                self.set_anim_state("idle", reset_frame=True)
            else:
                self.anim_tick = 0

        # decrement the timer
        if getattr(self, "damage_flash_timer", 0) > 0:
            self.damage_flash_timer -= 1