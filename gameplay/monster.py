from gameplay.models import Entity

class Monster(Entity):
    def __init__(self, data):
        super().__init__(data["current_q"], data["current_r"], data.get("texture_file"))
        self.id = data.get("id")
        self.name = data.get("name", "Unknown")
        self.hp = data.get("health", 50)
        self.damage = data.get("damage", 10)

    def move_towards_player(self, player):
        pass

    def attack_player(self, player):
        pass

    def take_damage(self, amount):
        pass

    def is_alive(self):
        return self.hp > 0
