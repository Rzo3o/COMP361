import os
import json
import random
from core.hexmath import HexMath
from gameplay import world
from gameplay.models import HealEffect
from gameplay.monster import Monster

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from gameplay.world import World

class Assistant(Monster):
    def __init__(self, data, ai=None):
        # Attempt to load the dedicated JSON file
        name = data.get("name", "warrior_assistant")
        base_name = name[:-5] if name.endswith(".json") else name
        json_path = os.path.join("assets", "definitions", "monsters", f"{base_name}.json")
        
        base_data = {}
        if os.path.exists(json_path):
            with open(json_path, "r") as f:
                base_data = json.load(f)
        else:
            print(f"[Warning] Assistant JSON not found at: {json_path}")

        # Merge dynamic DB data into the JSON template
        base_data.update(data)

        super().__init__(base_data, ai)
        
        self.vision_range = 4
        if "archer" in base_name:
            self.attack_range = 3
        else:
            self.attack_range = 1 
        self.is_friendly = True
        self.damage_flash_timer = 0
        self.poison_flash_timer = 0
        self.poison_turns_remaining = 0 
        self.poison_damage_per_turn = 0
        self.attack_hit_frame = base_data.get("attack_hit_frame", 3)

        self.ai_state = "FOLLOW"  # State：FOLLOW, RETURN, COMBAT
        
        self.leash_limit = 6    # Max distance before forced return
        self.teleport_limit = 10  # Max distance before instant teleport
        self.comfort_zone = 3    # Distance to resume normal follow   

        self.wander_cd_timer = 0
        self.wander_interval = (10,20)  
        
    def apply_poison(self, turns, damage_per_turn):
        self.poison_turns_remaining = turns
        self.poison_damage_per_turn = damage_per_turn
        self.poison_flash_timer = 3

    def take_damage(self, amount):
        actual_dmg = super().take_damage(amount)
        
        if actual_dmg > 0:
            self.damage_flash_timer = 5

            if self.anim_state == "hit":
                self.set_anim_state("idle", reset_frame=False)
                
        return actual_dmg
    
    def get_closest_monster(self, monsters):
        """Find the nearest enemy target."""
        best_target = None
        min_dist = 9999
        
        for m in monsters:
            if m.is_alive() and not getattr(m, "is_friendly", False):
                dist = HexMath.distance(self.q, self.r, m.q, m.r)
                if dist < min_dist:
                    min_dist = dist
                    best_target = m
                    
        return best_target

    def decide_and_act(self, world, player):
        if not self.is_alive() or getattr(self, "is_moving", False) or self.anim_state in ("attack", "hit"):
            return

        # Take poison damage first
        if self.poison_turns_remaining > 0:
            self.take_damage(self.poison_damage_per_turn)
            self.poison_flash_timer = 3
            self.poison_turns_remaining -= 1
            if not self.is_alive(): return

        dist_to_player = HexMath.distance(self.q, self.r, player.q, player.r)

        # If the player is way too far, instantly teleport to their side
        if dist_to_player > self.teleport_limit:
            self._teleport_to_player(world, player)
            return
        
        # State Transitions (Decision Making)
        # Too far from player
        if dist_to_player > self.leash_limit:
            self.ai_state = "RETURN"

        # Back in safe zone
        if self.ai_state == "RETURN" and dist_to_player <= self.comfort_zone:
            self.ai_state = "FOLLOW"

        # Enemy scan (Only if not returning to player)
        if self.ai_state != "RETURN":
            target_monster = self.get_closest_monster(world.monsters)
        
            if target_monster and HexMath.distance(self.q, self.r, target_monster.q, target_monster.r) <= self.vision_range:
                self.ai_state = "COMBAT"
            else:
                self.ai_state = "FOLLOW"

        # State Execution
        if self.ai_state == "RETURN":
            # Ignore combat, run back to player
            self.flip_x = (player.q < self.q)
            self.move_towards_player(player, world.is_passable)
            return  

        if self.ai_state == "COMBAT":
            if target_monster: 
                dist_to_m = HexMath.distance(self.q, self.r, target_monster.q, target_monster.r)
                if dist_to_m <= self.attack_range:
                    # In range: Attack!
                    self.flip_x = (target_monster.q < self.q)
                    self.attack(target_monster)
                else:
                    # Out of range: Chase enemy!
                    next_step = self._find_path_next_step(target_monster.q, target_monster.r, world.is_passable)
                    if next_step and next_step != (self.q, self.r):
                        self.flip_x = (next_step[0] < self.q)
                        self.start_move(next_step[0], next_step[1])
            else:
                self.ai_state = "FOLLOW" 
            return

        if self.ai_state == "FOLLOW":
            if dist_to_player > 2:
                # Catch up to player
                self.flip_x = (player.q < self.q)
                self.move_towards_player(player, world.is_passable)
            else:
                if self.wander_cd_timer > 0:
                    self.wander_cd_timer -= 1

                # Close enough, just wait (Idle) or Wander
                if self.anim_state not in ("attack", "hit", "move"):
                    if self.wander_cd_timer <= 0:
                        self.wander(world.is_passable) 
                        self.wander_cd_timer = random.randint(*self.wander_interval)
                    else:
                        self.set_anim_state("idle", reset_frame=False)

    def _pathfind_to(self, tq, tr, world):
        next_step = self._find_path_next_step(tq, tr, world.is_passable)
        if next_step and next_step != (self.q, self.r):
            # Don't step on the player
            if next_step == (world.player.q, world.player.r):
                return
            nq, nr = next_step
            self.flip_x = (nq < self.q)
            self.start_move(nq, nr)
    
    def _teleport_to_player(self, world, player):
        """
        Instantly snaps the assistant to a valid hex adjacent to the player.
        """
        # Hex directional neighbors
        directions = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]
        
        for dq, dr in directions:
            nq, nr = player.q + dq, player.r + dr
            
            # Find the first empty, passable tile next to the player
            if world.is_passable(nq, nr):
                # 1. Update logical coordinates
                self.q = nq
                self.r = nr
                
                # Reset rendering interpolation variables! 
                # This prevents the renderer from drawing a long "slide" across the screen.
                self.move_from_q = nq
                self.move_from_r = nr
                self.move_to_q = nq
                self.move_to_r = nr
                self.is_moving = False
                self.move_progress = 1.0
                
                # Reset state and animation
                self.set_anim_state("idle", reset_frame=True)
                self.ai_state = "FOLLOW"
                
                return
            
    def attack(self, target):
        """Trigger attack animation and queue damage."""
        self.set_anim_state("attack", reset_frame=True)
        self.pending_attack_target = target
        self.pending_attack_damage = getattr(self, "damage", 10) 
        self.attack_damage_applied = False


class MonkAssistant(Assistant):
    def __init__(self, data, ai=None):
        super().__init__(data, ai)
        
        self.attack_range = 0       # Monk does not attack
        self.heal_range = 3
        self.healing_amount = 10
        self.heal_cd_turns = 12
        self.heal_cd_remaining = 0

    def get_closest_wounded_ally(self, world, player):
        """Search for the most recent injured teammates (including players and other minions, but not yourself)"""
        allies = []
        if player.is_alive() and player.hp < player.max_hp:
            allies.append(player)
            
        for asst in getattr(world, "assistants", []):
            if asst != self and asst.is_alive() and asst.hp < asst.max_hp:
                allies.append(asst)
                
        if not allies: return None
        return min(allies, key=lambda a: HexMath.distance(self.q, self.r, a.q, a.r))

    def perform_heal(self, target, world: 'World'):
        self.set_anim_state("attack", reset_frame=True) 
        
        target.hp = min(target.max_hp, target.hp + self.healing_amount)
        target.heal_flash_timer = 5
        self.heal_cd_remaining = self.heal_cd_turns
        self.flip_x = (target.q < self.q)

        world.effects.append(HealEffect(target))
        
    def decide_and_act(self, world, player):
        if not self.is_alive() or getattr(self, "is_moving", False) or self.anim_state in ("attack", "hit"):
            return

        if self.poison_turns_remaining > 0:
            self.take_damage(self.poison_damage_per_turn)
            self.poison_flash_timer = 3
            self.poison_turns_remaining -= 1
            if not self.is_alive(): return

        dist_to_player = HexMath.distance(self.q, self.r, player.q, player.r)

        if dist_to_player > self.teleport_limit:
            self._teleport_to_player(world, player)
            return

        if self.heal_cd_remaining > 0:
            self.heal_cd_remaining -= 1

        target = self.get_closest_wounded_ally(world, player)
        
        if target and self.heal_cd_remaining <= 0:
            dist_to_target = HexMath.distance(self.q, self.r, target.q, target.r)
            if dist_to_target <= self.heal_range:
                self.perform_heal(target, world)
                return
            else:
                self.flip_x = (target.q < self.q)
                self.move_towards_player(target, world.is_passable)
                return

        if dist_to_player > 2:
            self.flip_x = (player.q < self.q)
            self.move_towards_player(player, world.is_passable)
        else:
            if self.wander_cd_timer > 0:
                self.wander_cd_timer -= 1

            if self.anim_state not in ("attack", "hit", "move"):
                if self.wander_cd_timer <= 0:
                    self.wander(world.is_passable)
                    self.wander_cd_timer = random.randint(*self.wander_interval)
                else:
                    self.set_anim_state("idle", reset_frame=False)