from world import World


class GameEngine:
    def __init__(self, db, session_id):
        self.db = db
        self.session_id = session_id
        self.world = World(db, session_id)
        self.world.update_fog_of_war()

    def handle_input(self, action):
        if self.world.player.dead:
            return "GAME_OVER"

        # Update the keys to match main.py Action Names
        move_map = {
            "MOVE_NORTH": (0, -1),
            "MOVE_SOUTH": (0, 1),
            "MOVE_WEST": (-1, 0),
            "MOVE_EAST": (1, 0),
            "MOVE_SW": (-1, 1),
            "MOVE_NE": (1, -1),
        }

        # Check if the action is a movement
        if action in move_map:
            dq, dr = move_map[action]
            self.attempt_move(dq, dr)
            return "TURN_TAKEN"

        # Handle new actions easily
        if action == "INVENTORY":
            print("Opening Inventory...")  # Placeholder
            return "NO_ACTION"

        return "NO_ACTION"

    def attempt_move(self, dq, dr):
        target_q = self.world.player.q + dq
        target_r = self.world.player.r + dr

        if self.world.is_passable(target_q, target_r):
            self.world.player.move(dq, dr)
            self.world.update_fog_of_war()
            self.db.save_player(self.session_id, self.world.player)
        else:
            pass

    def update(self):
        pass
