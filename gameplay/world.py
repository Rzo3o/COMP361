from numpy import tile

from core.config import Config
from core.hexmath import HexMath
from gameplay.models import Tile
from gameplay.player import Player
from gameplay.monster import MonsterFactory
from gameplay.item import Item
from gameplay.resource_lock import (
    ResourceLockManager,
    ground_resource_id,
    inventory_resource_id,
)

class World:
    def __init__(self, db, session_id):
        self.db = db
        self.session_id = session_id
        self.tiles = {}  # {(q,r): Tile}
        self.monsters = []
        self.ground_items = []
        self.player = None
        self.current_level = 1
        self.resource_locks = ResourceLockManager()

        self.load_world()
        self.load_player()
        self.load_monsters()
        self.load_ground_items()

    def load_world(self):
        # Use DB abstraction
        tile_rows = self.db.load_world_state(self.session_id)
        #tile_rows = self.db.load_world_level(self.session_id, self.current_level)

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

    def load_monsters(self):
        """Load all alive monsters from DB and equip their saved gear."""
        self.monsters = []
        rows = self.db.load_monsters()
        for data in rows:
            monster = MonsterFactory.create_monster(data)
            # Equip saved items for each slot
            for slot_name in ("weapon", "armor"):
                item_data = data.get(f"{slot_name}_item")
                if item_data:
                    item = Item(item_data)
                    monster.equip(item)
            self.monsters.append(monster)

    def load_ground_items(self):
        """Load all items placed on the ground."""
        self.ground_items = []
        rows = self.db.load_ground_items(self.session_id)
        for data in rows:
            item = Item(data)
            item.q = data.get("q")
            item.r = data.get("r")
            self.ground_items.append(item)
            if item.id is not None:
                self.resource_locks.add_resource(ground_resource_id(item.id))

    def sync_inventory_resource_locks(self):
        """Register current inventory entries as lockable resources."""
        if not self.player:
            return

        for item in self.player.inventory:
            if item.inventory_entry_id is not None:
                self.resource_locks.add_resource(
                    inventory_resource_id(item.inventory_entry_id)
                )

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

    def get_max_level(self):
        if not self.tiles:
            return 1
        return max(tile.level for tile in self.tiles.values())
    # def expand_to_next_level(self):
    #     self.current_level += 1

    #     new_tiles = self.db.load_world_level(self.session_id, self.current_level)

    #     if not new_tiles:
    #         print("No more levels")
    #         return

    #     for t_data in new_tiles:
    #         t = Tile(t_data)
    #         self.tiles[(t.q, t.r)] = t

    #     print(f"Loaded level {self.current_level}")

    def unlock_next_level(self):
        next_level = self.current_level + 1
        max_level = self.get_max_level()

        if next_level > max_level:
            return False
        
        next_level_tiles = [tile for tile in self.tiles.values() if tile.level == next_level]
        if not next_level_tiles:
            print(f"No tiles found for level {next_level}")
            return False

        self.db.unlock_level(self.session_id, next_level)

        for tile in next_level_tiles:
            tile.unlocked = True

        self.current_level = next_level
        print(f"Unlocked level {self.current_level}")
        return True

    def is_passable(self, q, r):
        tile = self.get_tile(q, r)
        if not tile or not tile.unlocked or not tile.passable:
            return False

        # check if there is a player in the tile
        if self.player and not self.player.dead:
            if self.player.q == q and self.player.r == r:
                return False
            
        # check if there is a monster in the tile
        for m in self.monsters:
            if m.is_alive() and m.q == q and m.r == r:
                return False
        return True
    
    def get_monster_at(self, q, r):
        for monster in self.monsters:
            if monster.is_alive() and monster.q == q and monster.r == r:
                return monster
        return None
    
    # helper for clouds
    def is_tile_locked(self, q, r):
        tile = self.get_tile(q, r)
        if not tile:
            return True
        return tile.level > self.current_level
    
