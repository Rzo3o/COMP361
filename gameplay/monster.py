from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Tuple, Any
import random
import os
import json

from gameplay.models import Entity
from gameplay.item import Item


@dataclass
class MonsterAIConfig:

    """Tunable AI parameters for a monster."""
    vision_range: int = 4         # How far the monster can "see" the player (hex distance)
    aggro_persist: int = 1        # How many turns to stay aggro after losing sight
    attack_range: int = 1         # Typically 1 for melee
    move_per_turn: int = 1        # Keep 1 for now (turn-based grid)
    attack_cooldown_turns: int = 2  # Minimum turns between attacks
    wander_chance: float = 0.60   # Chance to wander when idle (0~1)


class Monster(Entity):
    """
    Minimal backend monster for a hex-tile game.

    Assumptions based on your code:
    - Coordinates are axial (q, r)
    - World.is_passable(q, r) exists and blocks tiles + monsters
    - Player has q/r and take_damage(amount)
    - GameEngine takes turns; monsters act after player turn (recommended)
    """

    # Axial neighbor directions
    HEX_DIRS = (
        (1, 0),
        (1, -1),
        (0, -1),
        (-1, 0),
        (-1, 1),
        (0, 1),
    )

    def __init__(self, data: dict, ai: Optional[MonsterAIConfig] = None):
        super().__init__(data["current_q"], data["current_r"])
        self.id = data.get("id")
        self.name = data.get("name", "Unknown")
        self.data = data

        # Combat stats (base values, before equipment)
        self.max_hp = data.get("max_health", data.get("health", 50))
        self.hp = data.get("health", self.max_hp)
        self.base_damage = data.get("damage", 5)
        self.base_defense = 0

        # Equipment slots (same system as Player)
        self.equipment = {
            "weapon": None,
            "head": None,
            "chest": None,
            "legs": None,
        }

        # AI configuration
        self.ai = ai or MonsterAIConfig(
            vision_range=data.get("vision_range", 4),
            aggro_persist=data.get("aggro_persist", 1),
            attack_range=data.get("attack_range", 1),
            move_per_turn=data.get("move_per_turn", 1),
            attack_cooldown_turns=data.get("attack_cooldown_turns", 2),
            wander_chance=data.get("wander_chance", 0.60),
        )

        # Inventory for drops and unequipped items
        self.inventory = []
        for drop_name in data.get("drops", []):
            try:
                item_path = os.path.join("assets", "definitions", "items", f"{drop_name}.json")
                if os.path.exists(item_path):
                    with open(item_path, "r") as f:
                        item_data = json.load(f)
                        self.inventory.append(Item(item_data))
                else:
                    print(f"Warning: Drop item {drop_name}.json not found at {item_path}")
            except Exception as e:
                print(f"Error loading drop item {drop_name}: {e}")

        # State
        self.dead = False
        self.aggro = False
        self._aggro_memory = 0               # turns remaining to stay aggro when losing sight
        self._attack_cd_remaining = 0        # turns remaining before next attack

        # Animation
        animations = data.get("animations", {})

        self.anim_state = "idle"
        self.anim_tick = 0
        self.texture = animations.get("idle", {}).get("texture")

        print("Monster init:", self.name)
        print("animations:", animations)
        print("idle texture from json:", animations.get("idle", {}).get("texture"))
        print("legacy texture_file:", data.get("texture_file"))

        # Animation runtime state
        self.pending_attack_target = None
        self.pending_attack_damage = 0
        self.attack_damage_applied = False
        self.attack_hit_frame = 6

        # Hurt animation settings
        self.hurt_interrupts_attack = True
        self.queued_attack_target = None
        self.queued_attack_damage = 0

        # Death lifecycle
        self.death_finished = False
        self.remove_after_death = False
        self.death_loot_dropped = False

        # Move animation runtime state
        self.is_moving = False
        self.move_from_q = self.q
        self.move_from_r = self.r
        self.move_to_q = self.q
        self.move_to_r = self.r
        self.move_progress = 1.0
        self.move_speed = 0.25 

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

    # Equipment helpers

    @property
    def damage(self):
        """Base damage + weapon bonus."""
        bonus = 0
        weapon = self.equipment.get("weapon")
        if weapon and not weapon.is_broken():
            bonus = weapon.damage_bonus
        return self.base_damage + bonus

    @property
    def total_defense(self):
        """Sum of defense from all equipped armor."""
        total = self.base_defense
        for _, item in self.equipment.items():
            if item and not item.is_broken():
                total += item.defense
        return total

    def equip(self, item):
        """Equip an item. Returns the previously equipped item or None."""
        if not item.is_equippable:
            return None
        old = self.equipment.get(item.slot)
        self.equipment[item.slot] = item
        return old

    def unequip(self, slot):
        """Remove item from slot. Returns the removed item or None."""
        old = self.equipment.get(slot)
        if old:
            self.equipment[slot] = None
        return old

    def get_loot_drops(self):
        """Returns list of equipped items (to drop on death)."""
        drops = []
        drops.extend(self.inventory)
        for slot in list(self.equipment):
            item = self.equipment[slot]
            if item:
                drops.append(item)
                self.equipment[slot] = None
        return drops

    # Core Behaviors
    def is_alive(self) -> bool:
        return (not self.dead) and self.hp > 0

    def take_damage(self, amount, player):
        reduced = max(1, amount - self.total_defense)
        if reduced <= 0 or not self.is_alive():
            return 0

        self.hp -= reduced

        # Fatal hit: enter death animation
        if self.hp <= 0:
            self.hp = 0
            self.dead = True

            self.pending_attack_target = None
            self.pending_attack_damage = 0
            self.attack_damage_applied = False
            self.queued_attack_target = None
            self.queued_attack_damage = 0

            if not self.death_loot_dropped:
                player.add_items(*self.on_death())
                self.death_loot_dropped = True

            self.set_anim_state("die", reset_frame=True)
            return reduced

        # Non-fatal hit: switch to hurt animation.
        if self.anim_state != "die":
            if self.anim_state != "attack" or self.hurt_interrupts_attack:
                self.set_anim_state("hit", reset_frame=True)

        return reduced

    def on_death(self) -> list:
        """Drop all equipped items on death. Returns list of dropped Items."""
        drops = self.get_loot_drops()
        self.inventory = []
        return drops

    def can_attack(self) -> bool:
        return self._attack_cd_remaining <= 0
    
    def attack_player(self, player: Any) -> bool:
        """
        Deal damage if player is in range and cooldown allows.
        Returns True if an attack happened.
        """
        if not self.is_alive():
            return False

        dist = self.hex_distance(self.q, self.r, player.q, player.r)
        if dist > self.ai.attack_range:
            return False

        if not self.can_attack():
            return False

        dmg = self.damage
        self._attack_cd_remaining = self.ai.attack_cooldown_turns

        if self.anim_state == "hit":
            self.queued_attack_target = player
            self.queued_attack_damage = dmg
            return True
        
        self.set_anim_state("attack", reset_frame=True)

        # switch to attack animation
        self.pending_attack_target = player
        self.pending_attack_damage = dmg
        self.attack_damage_applied = False

        return True
    
    def start_move(self, to_q, to_r):
        self.move_from_q = self.q
        self.move_from_r = self.r
        self.move_to_q = to_q
        self.move_to_r = to_r

        self.q = to_q
        self.r = to_r

        self.move_progress = 0.0
        self.is_moving = True
        self.set_anim_state("move", reset_frame=True)

    def move_towards_player(
        self,
        player: Any,
        is_passable: Callable[[int, int], bool],
    ) -> bool:
        """
        Greedy 1-step move: choose neighbor that minimizes distance to player.
        Returns True if moved.
        """
        if not self.is_alive():
            return False
        
        current_dist = self.hex_distance(self.q, self.r, player.q, player.r)
        if current_dist <= 1:
            return False

        candidates = []

        for nq, nr in self.neighbors():
            if not is_passable(nq, nr):
                continue
            d = self.hex_distance(nq, nr, player.q, player.r)
            candidates.append((d, nq, nr))

        if not candidates:
            return False

        candidates.sort(key=lambda x: x[0])

        best_dist, best_q, best_r = candidates[0]

        if best_dist < current_dist:
            self.start_move(best_q, best_r)
            return True

        side_options = [(d, q, r) for (d, q, r) in candidates if d == current_dist]
        if side_options:
            _, sq, sr = random.choice(side_options)
            self.q, self.r = sq, sr
            return True

        return False
    
    def wander(self, is_passable) -> bool:
        """
        So far Minimal wandering: randomly move to a walkable neighbor.
        Returns True if moved
        Later may only wander within a restricted area
        """
        candidates = [(nq, nr) for (nq, nr) in self.neighbors() if is_passable(nq, nr)]
        if not candidates:
            return False

        nq, nr = random.choice(candidates)
        self.start_move(nq, nr)
        return True

    # AI decision
    def decide_and_act(self, world: Any, player: Any) -> dict:
        """
        One monster turn: decide action and execute.
        Returns a small log dict for debugging/UI.

        world must provide:
        - is_passable(q, r) -> bool
        """
        if not self.is_alive():
            return {"id": self.id, "action": "dead"}

        # Tick cooldowns
        if self._attack_cd_remaining > 0:
            self._attack_cd_remaining -= 1

        # Detect player
        dist = self.hex_distance(self.q, self.r, player.q, player.r)
        seen = dist <= self.ai.vision_range

        if seen:
            self.aggro = True
            self._aggro_memory = self.ai.aggro_persist
        else:
            if self._aggro_memory > 0:
                self._aggro_memory -= 1
            else:
                self.aggro = False

        # If aggro: attack if in range, else move closer
        if self.aggro:
            if dist <= self.ai.attack_range and self.can_attack():
                did = self.attack_player(player)
                return {"id": self.id, "action": "attack", "did": did, "dist": dist}

            moved = self.move_towards_player(player, world.is_passable)
            if moved:
                return {"id": self.id, "action": "chase_move", "dist": dist}

            return {"id": self.id, "action": "chase_stuck", "dist": dist}

        # If not aggro: optionally wander
        if random.random() < self.ai.wander_chance:
            moved = self.wander(world.is_passable)
            return {"id": self.id, "action": "wander" if moved else "idle_blocked", "dist": dist}

        return {"id": self.id, "action": "idle", "dist": dist}
    
    def update_animation(self, asset_manager):
        """
        Update the current animation state.

        States handled:
        - idle: loops
        - move: interpolates from one tile to another, then returns to idle
        - attack: applies damage at hit frame, then returns to idle
        - hit: plays once, then optionally chains into queued attack
        - die: plays once, then stays on last frame and marks monster removable
        """
        animations = self.data.get("animations", {})
        anim_cfg = animations.get(self.anim_state) or animations.get("idle")

        if not anim_cfg:
            return

        # Get the texture file for this animation state
        texture = anim_cfg.get("texture")
        if not texture:
            return

        # Get metadata such as frame count from the asset manager
        meta = asset_manager.anim_metadata.get(texture)
        if not meta:
            return

        frame_count = meta.get("count", 1)

        # move animation: advance interpolation + animate frames
        if self.anim_state == "move":
            # advance tile-to-tile interpolation
            if getattr(self, "is_moving", False):
                self.move_progress += self.move_speed

                if self.move_progress >= 1.0:
                    self.move_progress = 1.0
                    self.is_moving = False

            # animate move frames
            self.anim_tick += 1

            # loop move frames while moving
            if self.anim_tick >= frame_count:
                self.anim_tick = 0

            # once movement finishes, return to idle
            if not getattr(self, "is_moving", False):
                self.set_anim_state("idle", reset_frame=True)

            return

        # Apply attack damage when the animation reaches the hit frame
        if self.anim_state == "attack":
            if (
                not self.attack_damage_applied
                and self.pending_attack_target is not None
                and self.anim_tick >= self.attack_hit_frame
            ):
                if self.pending_attack_target.is_alive():
                    self.pending_attack_target.take_damage(self.pending_attack_damage)
                self.attack_damage_applied = True

        self.anim_tick += 1

        # Handle state change after the animation finishes
        if self.anim_tick >= frame_count:
            if self.anim_state in ("attack"):
                # Return to idle after attack or hurt animation
                self.pending_attack_target = None
                self.pending_attack_damage = 0
                self.attack_damage_applied = False
                self.set_anim_state("idle", reset_frame=True)
            elif self.anim_state == "hit":
                if self.queued_attack_target is not None and self.queued_attack_target.is_alive():
                    self.set_anim_state("attack", reset_frame=True)
                    self.pending_attack_target = self.queued_attack_target
                    self.pending_attack_damage = self.queued_attack_damage
                    self.attack_damage_applied = False
                else:
                    self.set_anim_state("idle", reset_frame=True)

                self.queued_attack_target = None
                self.queued_attack_damage = 0

            elif self.anim_state == "die":
                # Keep the last frame for death animation
                self.anim_tick = frame_count - 1
                self.death_finished = True
                self.remove_after_death = True
            else:
                self.anim_tick = 0

    def get_animation_config(self):
        # Get the animation config for the current state
        animations = self.data.get("animations", {}) if hasattr(self, "data") else {}
        return animations.get(self.anim_state) or animations.get("idle") or {}
    
    def get_texture_for_state(self, state):
        # Try to get the texture for the requested state
        animations = self.data.get("animations", {})
        state_anim = animations.get(state, {})
        if state_anim.get("texture"):
            return state_anim["texture"]
        
        # Fallback to idle texture if the state texture does not exist
        idle_anim = animations.get("idle", {})
        if idle_anim.get("texture"):
            return idle_anim["texture"]
        
        return self.texture
    
    def set_anim_state(self, new_state, reset_frame=True):
        # Do nothing if the state is unchanged and reset is not needed
        if self.anim_state == new_state and not reset_frame:
            return

        # Change animation state and update the texture
        self.anim_state = new_state
        self.texture = self.get_texture_for_state(new_state)

        if reset_frame:
            self.anim_tick = 0



