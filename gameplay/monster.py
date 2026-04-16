from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Tuple, Any
import random
import os
import json
import math

from gameplay.models import Entity
from gameplay.item import Item
from gameplay.models import CircleExplosion


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

    Assumptions:
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
        self.level = data.get("level", 1)

        # Combat stats (base values, before equipment)
        self.max_hp = data.get("max_health", data.get("health", 50))
        self.hp = data.get("health", self.max_hp)
        self.base_damage = data.get("damage", 5)
        self.base_defense = 0

        # Equipment slots (same system as Player)
        self.equipment = {
            "weapon": None,
            "armor": None,
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
                base_drop = drop_name[:-5] if drop_name.endswith(".json") else drop_name
                item_path = os.path.join("assets", "definitions", "items", f"{base_drop}.json")
                if os.path.exists(item_path):
                    with open(item_path, "r") as f:
                        item_data = json.load(f)
                        new_item = Item(item_data)
                        new_item._def_name = base_drop
                        self.inventory.append(new_item)
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

        # Float progress timer and speed config for animations
        self.anim_progress = 0.0  
        self.anim_speeds = {
            "idle": 0.2,
            "move": 0.3,
            "attack": 0.7,  
            "hit": 0.5,     
            "die": 0.5      
        }

        print("Monster init:", self.name)
        print("animations:", animations)
        print("idle texture from json:", animations.get("idle", {}).get("texture"))
        print("legacy texture_file:", data.get("texture_file"))

        # Animation runtime state
        self.pending_attack_target = None
        self.pending_attack_damage = 0
        self.attack_damage_applied = False
        self.attack_hit_frame = data.get("attack_hit_frame", 6)

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

        self.flip_x = False

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
        chance = .8
        dropItem = True
        equipment = list(self.equipment.values())
        inventory = list(self.inventory)
        while len(inventory) > 0 or len(equipment) > 0:
            if dropItem and random.random() <= chance and len(inventory) > 0:
                item = inventory.pop(0)
                if not item:
                    continue
                drops.append(item)
                chance *= 0.5
            elif not dropItem and random.random() <= chance and len(equipment) > 0:
                item = equipment.pop(0)
                if not item:
                    continue
                drops.append(item)
                chance *= 0.5
            dropItem = not dropItem
        return drops

    # Core Behaviors
    def is_alive(self) -> bool:
        return (not self.dead) and self.hp > 0

    def take_damage(self, amount):
        reduced = max(1, amount - self.total_defense)
        if reduced <= 0 or not self.is_alive():
            return 0

        self.hp -= reduced

        # Interept is_moving state once take damage
        if getattr(self, "is_moving", False):
            self.is_moving = False
            self.move_progress = 1.0 

        # Fatal hit: enter death animation
        if self.hp <= 0:
            self.hp = 0
            self.dead = True

            self.pending_attack_target = None
            self.pending_attack_damage = 0
            self.attack_damage_applied = False
            self.queued_attack_target = None
            self.queued_attack_damage = 0

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

        dist = super().hex_distance(self.q, self.r, player.q, player.r)
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
        
        current_dist = super().hex_distance(self.q, self.r, player.q, player.r)
        if current_dist <= 1:
            return False

        candidates = []

        for nq, nr in self.neighbors():
            if not is_passable(nq, nr):
                continue
            d = super().hex_distance(nq, nr, player.q, player.r)
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
            self.start_move(sq, sr)
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
        dist = super().hex_distance(self.q, self.r, player.q, player.r)
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

        # Calculate current animation speed based on state
        current_anim_speed = 1.0
        for base_state, speed in getattr(self, "anim_speeds", {}).items():
            if self.anim_state.endswith(base_state):
                current_anim_speed = speed
                break

        # move animation: advance interpolation + animate frames
        if self.anim_state == "move":
            # advance tile-to-tile interpolation
            if getattr(self, "is_moving", False):
                self.move_progress += self.move_speed

                if self.move_progress >= 1.0:
                    self.move_progress = 1.0
                    self.is_moving = False

            # animate move frames
            self.anim_progress += current_anim_speed
            self.anim_tick = int(self.anim_progress)

            # loop move frames while moving
            if self.anim_tick >= frame_count:
                self.anim_tick = 0
                self.anim_progress = 0.0

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

        self.anim_progress += current_anim_speed
        self.anim_tick = int(self.anim_progress)

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
                self.anim_progress = float(frame_count - 1)
                self.death_finished = True
                self.remove_after_death = True
            else:
                self.anim_tick = 0
                self.anim_progress = 0.0

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
            self.anim_progress = 0.0

class DashMonster(Monster):
    """
    Extended Monster class for entities with Dash and Stun mechanics 
    (e.g., flying_monster, mushroom_monster).
    """
    def __init__(self, data: dict, ai: Optional[MonsterAIConfig] = None):
        super().__init__(data, ai)
        
        # Dash and stun properties
        self.dash_cd_remaining = 0
        self.dash_cooldown_turns = 8
        
        self.is_dashing = False
        self.dash_dir = (0, 0)
        self.dash_steps = 0
        
        self.is_stunned = False
        self.is_charging = False
        
        # Cached references for dynamic collision checks during animation
        self._cached_world = None
        self._cached_player = None

        # animation speeds
        self.anim_speeds["stun"] = 0.25
        self.anim_speeds["charge"] = 0.3

        self.dash_recovery_turns = 1
        self.dash_recovery_remaining = 0

    # Overwrite
    def decide_and_act(self, world: Any, player: Any) -> dict:
        if not self.is_alive():
            return super().decide_and_act(world, player)

        self._cached_world = world
        self._cached_player = player

        # Intercept if stunned
        if self.is_stunned:
            return {"id": self.id, "action": "stunned"}

        # Recovery timer after dashing
        if self.dash_recovery_remaining > 0:
            self.dash_recovery_remaining -= 1
            return {"id": self.id, "action": "recovering"}
    
        # Intercept if charging
        if self.is_charging:
            return {"id": self.id, "action": "charging"}
        
        # Intercept if already moving or actively dashing
        if getattr(self, "is_moving", False) or self.is_dashing:
            return {"id": self.id, "action": "busy"}

        if self.dash_cd_remaining > 0:
            self.dash_cd_remaining -= 1

        dist = super().hex_distance(self.q, self.r, player.q, player.r)
        
        # Check for dash opportunity
        if (dist <= self.ai.vision_range or self.aggro) and self.dash_cd_remaining <= 0 and 2 <= dist <= 6:
            dash_dir = self._get_dash_axis(player)
            
            if dash_dir:
                # Raycast to ensure the initial path is clear of walls
                path_clear = True
                for step in range(1, dist):
                    cq = self.q + dash_dir[0] * step
                    cr = self.r + dash_dir[1] * step
                    if not world.is_passable(cq, cr):
                        path_clear = False
                        break
                
                if path_clear:
                    self.dash_dir = dash_dir
                    self.dash_steps = 0
                    self.flip_x = (dash_dir[0] > 0) 
                    
                    # Enter charge state before dashing
                    self.is_charging = True
                    self.set_anim_state("charge", reset_frame=True)

                    return {"id": self.id, "action": "charge_start", "dist": dist}

        # Fallback to standard AI behavior
        return super().decide_and_act(world, player)

    # Overwrite 
    def update_animation(self, asset_manager):
        # Handle Stun Animation
        if self.is_stunned and self.anim_state == "stun":
            current_anim_speed = getattr(self, "anim_speeds", {}).get("stun", 0.25)
            self.anim_progress += current_anim_speed
            self.anim_tick = int(self.anim_progress)
            
            meta = asset_manager.anim_metadata.get(self.texture)
            frame_count = meta.get("count", 1) if meta else 1

            if self.anim_tick >= frame_count:
                self.is_stunned = False                    
                self.set_anim_state("idle", reset_frame=True) 
            return 

        # Handle Charge Animation
        if self.is_charging and self.anim_state == "charge":
            current_anim_speed = getattr(self, "anim_speeds", {}).get("charge", 0.15)
            self.anim_progress += current_anim_speed
            self.anim_tick = int(self.anim_progress)
            
            meta = asset_manager.anim_metadata.get(self.texture)
            frame_count = meta.get("count", 1) if meta else 1

            # Launch the dash exactly when the charge animation finishes
            if self.anim_tick >= frame_count:
                self.is_charging = False
                self.is_dashing = True
                
                
                self._continue_dash() 
            return 
        
        # Handle High-Speed Dash Movement
        if self.anim_state == "move" and self.is_dashing:
            self.move_progress += self.move_speed * 2.0

            if self.move_progress >= 1.0:
                self.move_progress = 1.0
                self.is_moving = False
                self._continue_dash() # Check collision for the next tile

            current_anim_speed = self.anim_speeds.get("move", 1.0)
            self.anim_progress += current_anim_speed
            self.anim_tick = int(self.anim_progress)
            
            meta = asset_manager.anim_metadata.get(self.texture)
            if meta and self.anim_tick >= meta.get("count", 1):
                self.anim_tick = 0
                self.anim_progress = 0.0
                
            return 

        super().update_animation(asset_manager)

    def _get_dash_axis(self, player) -> Optional[Tuple[int, int]]:
        """Check if player aligns with hex axes (with 1-tile fuzzy tolerance)"""
        dq = player.q - self.q
        dr = player.r - self.r
        ds = (-player.q - player.r) - (-self.q - self.r)

        min_dist = min(abs(dq), abs(dr), abs(ds))
        
        if min_dist <= 1:
            # Snap to the closest axis
            if abs(dq) == min_dist:
                return (0, 1 if dr > 0 else -1)  
            elif abs(dr) == min_dist:
                return (1 if dq > 0 else -1, 0) 
            else:
                return (1 if dq > 0 else -1, -1 if dq > 0 else 1)
        
        return None

    def _continue_dash(self):
        """Dynamic per-hex collision check during active dash"""
        world = self._cached_world
        player = self._cached_player
        
        if not world or not player or self.dash_steps >= 6:
            self._stop_dash()
            return

        next_q = self.q + self.dash_dir[0]
        next_r = self.r + self.dash_dir[1]

        # Hit player
        if next_q == player.q and next_r == player.r:
            player.take_damage(self.damage * 2) # Double the damage
            self._stop_dash()
            return

        # Hit wall or another monster
        if not world.is_passable(next_q, next_r):
            target_monster = None
            if hasattr(world, "monsters"):
                for m in world.monsters:
                    if m.q == next_q and m.r == next_r and m.is_alive():
                        target_monster = m
                        break
            
            # Damage the blocking monster
            if target_monster and target_monster != self:
                target_monster.take_damage(self.damage)
            
            # Stun self
            self._stop_dash()
            self.is_stunned = True
            self.set_anim_state("stun", reset_frame=True)
            return

        # Path clear, move to next hex
        self.dash_steps += 1
        self.start_move(next_q, next_r)

    # Overwrite
    def take_damage(self, amount):
        self.is_dashing = False
        self.is_charging = False

        # Wake slap
        if self.is_stunned or getattr(self, "anim_state", "").endswith("stun"):
            self.is_stunned = False
            
        return super().take_damage(amount)
    
    def _stop_dash(self):
        """Halt dash and trigger cooldown"""
        self.is_dashing = False
        self.dash_cd_remaining = self.dash_cooldown_turns
        if not self.is_stunned:
            self.dash_recovery_remaining = self.dash_recovery_turns
            self.set_anim_state("idle", reset_frame=True)


class SlimeMonster(Monster):
    """
    Slime monster variant that explodes upon death.
    Green: 1-hex radius damage.
    Orange: 2-hex radius massive damage.
    Blue: 1-hex radius damage + applies poison to player.
    """
    def __init__(self, data: dict, ai: Optional[MonsterAIConfig] = None):
        super().__init__(data, ai)
        self.has_exploded = False
        self._cached_world = None
        self._cached_player = None

    def decide_and_act(self, world: Any, player: Any) -> dict:
        # Cache world and player to use during the death explosion
        self._cached_world = world
        self._cached_player = player
        return super().decide_and_act(world, player)

    def update_animation(self, asset_manager):
        # Store death status before updating
        was_dead = getattr(self, "death_finished", False)
        
        # Call base animation logic
        super().update_animation(asset_manager)
        
        # Trigger explosion when the death animation finishes
        if self.anim_state == "die" and self.death_finished and not was_dead:
            if not self.has_exploded:
                self._explode()
                self.has_exploded = True

    def _explode(self):
        world = self._cached_world
        player = self._cached_player

        if not world or not player:
            return

        dist = super().hex_distance(self.q, self.r, player.q, player.r)
        
        # Determine explosion properties based on slime name
        radius = 1
        is_poisonous = False
        color = (255, 255, 255)  # default white color
        slime_name = self.name.lower()
        
        if "orange" in slime_name:
            radius = 2
            color = (255, 100, 0)
        elif "blue" in slime_name:
            radius = 1
            is_poisonous = True
            color = (180, 50, 255)
        elif "green" in slime_name:
            radius = 1
            color = (50, 255, 50)

        # Add explosion effect in the world
        if hasattr(world, "effects"):
            effect = CircleExplosion(self.q, self.r, color, radius)
            world.effects.append(effect) 

        # Explosion deals 1.5x base damage
        explosion_damage = int(self.damage * 1.5)
        
        # Check if player is caught in the blast radius
        if dist <= radius:
            player.take_damage(explosion_damage)
            
            if is_poisonous:
                # Apply poison effect (3 turns, 2 damage per turn)
                if hasattr(player, "apply_poison"):
                    player.apply_poison(turns=5, damage_per_turn=3)
        if hasattr(world, "monsters"):
            for m in world.monsters:
                if m != self and m.is_alive():
                    dist_to_monster = super().hex_distance(self.q, self.r, m.q, m.r)
                    
                    if dist_to_monster <= radius:
                        m.take_damage(explosion_damage)


class BushMonster(Monster):
    """
    Bush monster variant that applies poison to the player on a attack hit.
    """
    def update_animation(self, asset_manager):
        damage_was_applied = getattr(self, "attack_damage_applied", False)
        target = self.pending_attack_target

        super().update_animation(asset_manager)

        if self.anim_state == "attack" and not damage_was_applied and self.attack_damage_applied:
            if target and target.is_alive() and hasattr(target, "apply_poison"):
                target.apply_poison(turns=3, damage_per_turn=2)
                print(f"[Combat] {self.name} applied poison to the player!")


class MonsterFactory:
    _registry = {
        "flying_monster": DashMonster,
        "mushroom_monster": DashMonster,
        "green_slime": SlimeMonster,
        "orange_slime": SlimeMonster,
        "blue_slime": SlimeMonster,
        "bush_monster": BushMonster,
    }

    @classmethod
    def create_monster(cls, data: dict, ai_config: Optional[Any] = None):
        monster_name = data.get("name", "Unknown")

        # Strip .json suffix if present
        if monster_name.endswith(".json"):
            monster_name = monster_name[:-5]

        # Fetch specific class or fallback to base Monster
        MonsterClass = cls._registry.get(monster_name, Monster)

        return MonsterClass(data, ai_config)



