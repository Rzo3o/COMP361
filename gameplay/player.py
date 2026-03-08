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
        self.hunger = max(0, self.hunger - 1)
        self.hunger = max(0, self.hunger - 1) 
        
        if self.hunger == 0:
            self.take_damage(5)

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.dead = True
