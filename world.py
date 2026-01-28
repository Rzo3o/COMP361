from hexmath import HexMath, Config
from models import Tile, Player, Monster


class World:
    def __init__(self, db, session_id):
        self.db = db
        self.session_id = session_id
        self.tiles = {}  # {(q,r): Tile}
        self.monsters = []
        self.load_world()
        self.load_player()

    def load_world(self):
        query = """
        SELECT 
            m.id, m.q, m.r, m.tile_type, m.texture_file, 
            m.prop_texture_file, m.prop_scale, m.prop_y_shift, m.is_permanently_passable,
            s.is_discovered, s.is_unlocked, s.is_conquered
        FROM map_tiles m
        LEFT JOIN session_world_state s 
            ON m.id = s.tile_id 
            AND s.session_id = ?
        """
        self.db.cursor.execute(query, (self.session_id,))

        raw_tiles = self.db.cursor.fetchall()
        for t_data in raw_tiles:
            t = Tile(dict(t_data))

            if t_data["is_discovered"] is None:
                t.discovered = False
            else:
                t.discovered = bool(t_data["is_discovered"])

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
