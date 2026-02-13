from core.config import Config
from core.hexmath import HexMath
from gameplay.models import Tile
from gameplay.player import Player
from gameplay.monster import Monster

class World:
    def __init__(self, db, session_id):
        self.db = db
        self.session_id = session_id
        self.tiles = {}  # {(q,r): Tile}
        self.monsters = []
        self.player = None
        self.load_world()
        self.load_player()

    def load_world(self):
        # Use DB abstraction
        tile_rows = self.db.load_world_state(self.session_id)
        for t_data in tile_rows:
            # Check if t_data has the keys expected by Tile(data)
            # data.get("is_discovered") might be 0/1 integer, bool conversion handled in Tile logic.
            t = Tile(t_data)
            self.tiles[(t.q, t.r)] = t

    def load_player(self):
        p_data = self.db.get_player_state(self.session_id)
        if p_data:
            self.player = Player(p_data)
        else:
            print("ERROR: No player state found for session", self.session_id)

    def get_tile(self, q, r):
        return self.tiles.get((q, r))

    def update_fog_of_war(self):
        """Reveals tiles around the player."""
        if not self.player:
            return

        pq, pr = self.player.q, self.player.r
        radius = Config.VISIBLE_RADIUS

        for q in range(-radius, radius + 1):
            for r in range(-radius, radius + 1):
                if abs(q + r) > radius:
                    continue

                target_q, target_r = pq + q, pr + r
                dist = HexMath.distance(pq, pr, target_q, target_r)

                if dist <= radius:
                    tile = self.get_tile(target_q, target_r)
                    if tile and not tile.discovered:
                        tile.discovered = True
                        self.db.update_discovery(self.session_id, tile.id)

    def is_passable(self, q, r):
        tile = self.get_tile(q, r)
        if not tile:
            return False  # Void
        if not tile.passable:
            return False  # Mountains/Deep Water
        for m in self.monsters:
            if m.q == q and m.r == r:
                return False
        return True
