import os
import json
from core.hexmath import HexMath
from gameplay.monster import Monster

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
        self.attack_range = 1  
        self.is_friendly = True
        self.damage_flash_timer = 0
        self.poison_flash_timer = 0
        self.poison_turns_remaining = 0 
        self.poison_damage_per_turn = 0
        self.attack_hit_frame = data.get("attack_hit_frame", 3)

        self.ai_state = "FOLLOW"  # State：FOLLOW, RETURN, COMBAT
        
        self.leash_limit = 6    # Max distance before forced return
        self.comfort_zone = 3    # Distance to resume normal follow     
        
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

        # State Transitions (Decision Making)

        # Too far from player
        if dist_to_player > self.leash_limit:
            self.ai_state = "RETURN"

        # Back in safe zone
        if self.ai_state == "RETURN" and dist_to_player <= self.comfort_zone:
            self.ai_state = "FOLLOW"

        # Enemy scan (Only if not returning to player)
        target_monster = self.get_closest_monster(world.monsters)
        
        if target_monster and HexMath.distance(self.q, self.r, target_monster.q, target_monster.r) <= self.vision_range:
            self.ai_state = "COMBAT"
        else:
            self.ai_state = "FOLLOW"

        # State Execution
        if self.ai_state == "RETURN":
            # Ignore combat, run back to player
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
                self.move_towards_player(player, world.is_passable)
            else:
                # Close enough, just wait (Idle)
                if self.anim_state not in ("attack", "hit", "move"):
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
    
    def attack(self, target):
        """Trigger attack animation and queue damage."""
        self.set_anim_state("attack", reset_frame=True)
        self.pending_attack_target = target
        self.pending_attack_damage = getattr(self, "damage", 10) 
        self.attack_damage_applied = False