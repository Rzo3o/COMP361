from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Tuple, Any
import random

from gameplay.models import Entity


@dataclass
class MonsterAIConfig:

    """Tunable AI parameters for a monster."""
    vision_range: int = 6         # How far the monster can "see" the player (hex distance)
    aggro_persist: int = 2        # How many turns to stay aggro after losing sight
    attack_range: int = 1         # Typically 1 for melee
    move_per_turn: int = 1        # Keep 1 for now (turn-based grid)
    attack_cooldown_turns: int = 1  # Minimum turns between attacks
    wander_chance: float = 0.20   # Chance to wander when idle (0~1)


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
        super().__init__(data["current_q"], data["current_r"], data.get("texture_file"))
        self.id = data.get("id")
        self.name = data.get("name", "Unknown")

        # Combat stats (base values, before equipment)
        self.max_hp = data.get("max_health", data.get("health", 50))
        self.hp = data.get("health", self.max_hp)
        self.base_damage = data.get("damage", 10)
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
            vision_range=data.get("vision_range", 6),
            attack_range=data.get("attack_range", 1),
            move_per_turn=data.get("move_per_turn", 1),
            attack_cooldown_turns=data.get("attack_cooldown_turns", 1),
        )

        # State
        self.dead = False
        self.aggro = False
        self._aggro_memory = 0               # turns remaining to stay aggro when losing sight
        self._attack_cd_remaining = 0        # turns remaining before next attack

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
        for slot in list(self.equipment):
            item = self.equipment[slot]
            if item:
                drops.append(item)
                self.equipment[slot] = None
        return drops

    # Core Behaviors
    def is_alive(self) -> bool:
        return (not self.dead) and self.hp > 0

    def take_damage(self, amount):
        reduced = max(1, amount - self.total_defense)
        if reduced <= 0 or not self.is_alive():
            return

        self.hp -= reduced

        # TODO (animation/modeling): play hurt animation / flash / sound
        # self.anim_state = "hurt"

        if self.hp <= 0:
            self.hp = 0
            self.dead = True
            self.on_death()

    def on_death(self) -> list:
        """Drop all equipped items on death. Returns list of dropped Items."""
        return self.get_loot_drops()

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

        # TODO (animation/modeling): trigger attack animation (windup) then apply damage
        # self.anim_state = "attack"

        if hasattr(player, "take_damage"):
            player.take_damage(self.damage)
        else:
            # Fallback if Player doesn't have take_damage yet
            player.hp = max(0, player.hp - self.damage)

        self._attack_cd_remaining = self.ai.attack_cooldown_turns
        return True
    
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

        best = (self.q, self.r)
        best_dist = current_dist

        # Evaluate all walkable neighbors; pick the one that gets closer
        for nq, nr in self.neighbors():
            if not is_passable(nq, nr):
                continue
            d = self.hex_distance(nq, nr, player.q, player.r)
            if d < best_dist:
                best_dist = d
                best = (nq, nr)

        if best != (self.q, self.r):
            # TODO (animation/modeling): trigger move animation / interpolate pixels
            # self.anim_state = "move"
            self.q, self.r = best
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

        self.q, self.r = random.choice(candidates)
        # TODO (animation/modeling): idle->move animation
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
            return {"id": self.id, "action": "chase_move" if moved else "chase_stuck", "dist": dist}

        # If not aggro: optionally wander
        if random.random() < self.ai.wander_chance:
            moved = self.wander(world.is_passable)
            return {"id": self.id, "action": "wander" if moved else "idle_blocked", "dist": dist}

        return {"id": self.id, "action": "idle", "dist": dist}


