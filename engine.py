from world import World


class GameEngine:
    def __init__(self, db, session_id):
        self.db = db
        self.session_id = session_id
        self.world = World(db, session_id)
        self.world.update_fog_of_war()

    def handle_input(self, key):
        if self.world.player.dead:
            return "GAME_OVER"

        dq, dr = 0, 0
        if key == "Up":
            dq, dr = 0, -1
        elif key == "Down":
            dq, dr = 0, 1
        elif key == "Left":
            dq, dr = -1, 0
        elif key == "Right":
            dq, dr = 1, 0
        move_map = {
            "w": (0, -1),  # N
            "s": (0, 1),  # S
            "a": (-1, 0),  # NW
            "d": (1, 0),  # SE
            "q": (-1, 1),  # SW
            "e": (1, -1),  # NE
        }

        if key.lower() in move_map:
            dq, dr = move_map[key.lower()]
            self.attempt_move(dq, dr)
            return "TURN_TAKEN"

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
