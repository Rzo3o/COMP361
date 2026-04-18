import random
from core.hexmath import HexMath
from gameplay.monster import Monster

class Assistant(Monster):
    def __init__(self, data, ai=None):
        super().__init__(data, ai)
        
        self.leash_range = 5    
        self.aggro_range = 3    
        self.attack_range = 1  
        self.follow_dist = 1    
        self.is_friendly = True
        self.damage_flash_timer = 0
        self.poison_flash_timer = 0
        self.poison_turns_remaining = 0 
        self.poison_damage_per_turn = 0
        self.attack_hit_frame = data.get("attack_hit_frame", 3)

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
        if not self.is_alive(): return
        
        if self.poison_turns_remaining > 0:
            self.take_damage(self.poison_damage_per_turn)
            
            self.poison_flash_timer = 8
            
            self.poison_turns_remaining -= 1

        dist_to_player = HexMath.distance(self.q, self.r, player.q, player.r)

        if dist_to_player > self.leash_range:
            self._smart_move_towards(player.q, player.r, world)
            return

        target_monster = self.get_closest_monster(world.monsters)
        
        if target_monster and target_monster.is_alive():
            dist_to_monster = HexMath.distance(self.q, self.r, target_monster.q, target_monster.r)
            print(f"[Assistant AI] Found enemy {target_monster.name} at dist {dist_to_monster}")

            if dist_to_monster <= self.attack_range:
                print(f"[Assistant AI] {self.name} is attacking {target_monster.name}!")
                self.attack(target_monster) 
                return
            elif dist_to_monster <= self.aggro_range:
                self._smart_move_towards(target_monster.q, target_monster.r, world)
                return

        # 3. 没事干，跟随玩家
        if dist_to_player > self.follow_dist:
            self._smart_move_towards(player.q, player.r, world)

    def _smart_move_towards(self, tq, tr, world):
        """调用基类的 BFS 寻路，比简单的邻居查找聪明得多"""
        if getattr(self, "is_moving", False):
            return

        # 直接调用 Monster 基类里的寻路算法
        next_step = self._find_path_next_step(tq, tr, world.is_passable)
        
        if next_step and next_step != (tq, tr):
            nq, nr = next_step
            self.flip_x = (nq > self.q)
            self.start_move(nq - self.q, nr - self.r)
    

    def attack(self, target):
        """触发攻击逻辑（如果 Monster 基类已经写好了，这里甚至可以删除）"""
        self.set_anim_state("attack", reset_frame=True)
        self.pending_attack_target = target
        # 使用 JSON 里配置的伤害，如果没有默认 10
        self.pending_attack_damage = getattr(self, "damage", 10) 
        self.attack_damage_applied = False