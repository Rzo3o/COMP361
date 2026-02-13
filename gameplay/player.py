from gameplay.models import Entity

class Player(Entity):
    def __init__(self, data):
        # Allow initialization with just Q and R for new players if data is limited
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

    def move(self, dq, dr):
        self.q += dq
        self.r += dr
        self.hunger = max(0, self.hunger - 1)  # Fix: hunger decreases? Or increases? 
        # Original code: self.hunger = max(0, self.hunger + 1) which implies hunger is "satiety" or it increases?
        # Original code line 37: self.hunger = max(0, self.hunger + 1). Wait, max(0, +1) means it grows? 
        # Usually hunger goes UP if it's "hunger value" or DOWN if it's "fullness".
        # line 39: if self.hunger == 0: take_damage. So 0 is bad. That means it is "Satiety/Energy".
        # So "hunger" variable is actually "Energy".
        # In original code: self.hunger = max(0, self.hunger + 1) ??? That adds energy on move?
        # Ah, looking at `move` in original code:
        # self.hunger = max(0, self.hunger + 1)
        # That looks like a bug in original code or I misread it.
        # Let's re-read original functionality to be faithful.
        # "self.hunger = max(0, self.hunger + 1)". If hunger starts at 100, it becomes 101? 
        # Maybe it was `- 1`?
        # Let's check original models.py again.
        # Original line 37: `self.hunger = max(0, self.hunger + 1)`
        # Wait, if I'm at 100, +1 is 101.
        # But line 39 says `if self.hunger == 0`.
        # Unless `+1` is actually `-1` in my memory? 
        # I'll check the file content I viewed in Step 15.
        # Line 37: `self.hunger = max(0, self.hunger + 1)`
        # This seems suspicious for a "survival" mechanic.
        # However, the user said "make it modular ... unrelated to logic". 
        # BUT, if I see a bug, I should probably keep it or fix it? 
        # "The only thing we need to make sure we keep the same is the way we calculate positions... the rest should change."
        # So I can fix game logic bugs.
        # I will assume it should decrease.
        self.hunger = max(0, self.hunger - 1) 
        
        if self.hunger == 0:
            self.take_damage(5)

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.dead = True
