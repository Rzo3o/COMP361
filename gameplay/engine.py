import time
from gameplay.world import World
from gameplay.item import Item



class GameEngine:
    def __init__(self, db, session_id):
        self.db = db
        self.session_id = session_id
        self.world = World(db, session_id)
        self.world.update_fog_of_war()
        self.show_inventory = False  # toggle flag
        self.selected_index = 0  # cursor position in inventory
        if self.world.player:
            self.world.player.load_inventory(self.db, self.session_id)
            self.world.sync_inventory_resource_locks() # Sync resource locks after loading inventory
        self.start_time = time.time()
        self.monsters_need_turn = False  # Animation lock: A mark waiting for the monster to act

    def handle_input(self, action):
        player = self.world.player

        if player is None:
            return "NO_PLAYER"
        if player.dead:
            return "GAME_OVER"

        # --- Inventory screen controls ---
        if self.show_inventory:
            if action == "INVENTORY":
                self.show_inventory = False
                player.set_anim_state("idle", reset_frame=True)
                return "NO_ACTION"
            if action == "MOVE_NORTH" and self.selected_index > 0:
                self.selected_index -= 1
            elif (
                action == "MOVE_SOUTH"
                and self.selected_index < len(player.inventory) - 1
            ):
                self.selected_index += 1
            elif action == "INTERACT":
                self.use_selected_item()
            elif action == "MOVE_WEST":
                self.drop_selected_item()
            return "NO_ACTION"

        # --- Normal gameplay controls ---
        if action == "INTERACT":
            # pick up items take a turn
            picked_up = self.pick_up_ground_items()
            return "TURN_TAKEN" if picked_up else "NO_ACTION"

        move_map = {
            "MOVE_NORTH": (0, -1),
            "MOVE_SOUTH": (0, 1),
            "MOVE_WEST": (-1, 0),
            "MOVE_EAST": (1, 0),
            "MOVE_SW": (-1, 1),
            "MOVE_NE": (1, -1),
        }
        if action in move_map:
            dq, dr = move_map[action]
            player = self.world.player
            
            if player is None:
                return "NO_PLAYER"

            target_q = player.q + dq
            target_r = player.r + dr

            # if target hex has a monster, then player attacks
            monster = self.world.get_monster_at(target_q, target_r)
            if monster is not None:
                damage = player.attack_monster(monster)

                if not self._safe_save_monster(monster):
                    return "SAVE_ERROR"

                if not self._safe_save_player(player):
                    return "SAVE_ERROR"

                if not monster.is_alive():
                    self.drop_monster_loot(monster)

                print(f"Player attacked {monster.name} for {damage} damage")
                return "TURN_TAKEN"
            
            # if no monster, then try to move
            moved = self.attempt_move(dq, dr)
            return "TURN_TAKEN" if moved else "NO_ACTION"

        if action == "INVENTORY":
            self.show_inventory = True
            self.selected_index = 0
            if player:
                player.load_inventory(self.db, self.session_id)
                self.world.sync_inventory_resource_locks() # Sync resource locks when opening inventory
            return "NO_ACTION"

        return "NO_ACTION"

    def use_selected_item(self):
        """Use or equip/unequip the currently selected inventory item."""
        # get the player and check if selected index is valid
        player = self.world.player
        if not player or self.selected_index >= len(player.inventory):
            return False

        # get the item and its resource lock if it has one
        item = player.inventory[self.selected_index]
        resource_id = item.resource_id
        if resource_id is not None:
            # ensure the resource lock exists before trying to acquire it
            self.world.resource_locks.add_resource(resource_id)
            # try to acquire the lock
            if not self.world.resource_locks.acquire(resource_id):
                return False
 
        used = player.use_item(self.selected_index, self.db, self.session_id)
        if resource_id is not None:
            if used and item.type == "food":
                self.world.resource_locks.consume(resource_id)
            else:
                self.world.resource_locks.release(resource_id)

        if used:
            # Sync resource locks after using item\
            self.world.sync_inventory_resource_locks()

        # If the item was consumed or equipped, we may need to adjust the selected index if it goes out of bounds
        if self.selected_index >= len(player.inventory):
            self.selected_index = max(0, len(player.inventory) - 1)
        return used

    def drop_selected_item(self):
        """Drop one of the selected item from inventory."""
        player = self.world.player
        if not player:
            return
        player.drop_item(self.selected_index, self.db, self.session_id)
        if self.selected_index >= len(player.inventory):
            self.selected_index = max(0, len(player.inventory) - 1)

    def pick_up_ground_items(self):
        """Pick up all ground items on the player's current tile."""
        player = self.world.player
        if not player:
            return False

        ground_items = list(self.world.get_ground_items_at(player.q, player.r))
        if not ground_items:
            return False

        picked_up_any = False
        # if any item is successfully picked up add to inventory and remove from ground.
        for item in ground_items:
            resource_id = item.resource_id
            if resource_id is None:
                continue

            # ensure the resource lock exists before trying to acquire it
            self.world.resource_locks.add_resource(resource_id)
            if not self.world.resource_locks.acquire(resource_id):
                continue

            try:
                self.db.add_item(self.session_id, item.id)
                self.db.remove_ground_item(item.id)
                self.world.resource_locks.consume(resource_id)
                picked_up_any = True
            except Exception:
                self.world.resource_locks.release(resource_id)

        # fail if we couldn't pick up any items
        if not picked_up_any:
            return False

        # reload inventory and sync resource locks
        player.load_inventory(self.db, self.session_id)
        self.world.load_ground_items()
        self.world.sync_inventory_resource_locks()
        return True

    def _safe_save_player(self, player):
        try:
            self.db.save_player(self.session_id, player)
            return True
        except Exception:
            return False
        
    def _safe_save_monster(self, monster):
        try:
            if hasattr(self.db, "save_monster"):
                self.db.save_monster(monster)
            return True
        except Exception:
            return False

    def attempt_move(self, dq, dr):
        """Try to move the player by (dq, dr). Returns True if move succeeded, False if blocked."""
        player = self.world.player
        target_q = player.q + dq
        target_r = player.r + dr

        if not self.world.is_passable(target_q, target_r):
            return False

        old_q, old_r = player.q, player.r

        player.move(dq, dr)
        self.world.update_fog_of_war()

        if not self._safe_save_player(player):
            player.q = old_q
            player.r = old_r
            self.world.update_fog_of_war()
            return False

        return True

    def drop_monster_loot(self, monster):
        if not monster.is_alive():
            if not getattr(monster, 'death_loot_dropped', False):
                drops = monster.on_death()
                print("Dropped: ", [item.name for item in drops])
                for item in drops:
                    if getattr(item, 'id', None) is None and hasattr(item, '_def_name'):
                        item.id = self.db.get_or_create_item(item._def_name)
                    if getattr(item, 'id', None) is not None:
                        self.db.add_item(self.session_id, item.id)
                self.world.player.load_inventory(self.db, self.session_id)
                monster.death_loot_dropped = True

            alive_count = sum(
                1 for m in self.world.monsters
                if m.is_alive() and m.level == self.world.current_level)

            print(f"{monster.name} died! {alive_count} monsters left in this level.")

    def update(self):
        player = self.world.player

        if player is None:
            return "NO_PLAYER"
        
        if player.dead:
            return "GAME_OVER"

        if player.hunger > 0:
            player.hunger -= 1

        if player.hunger <= 0:
            player.hunger = 0
            if player.hp > 0:
                player.take_damage(5)

        if player.hp <= 0:
            player.hp = 0
            player.dead = True

            if hasattr(player, "death_count"):
                player.death_count += 1

            if not self._safe_save_player(player):
                return "SAVE_ERROR"

            return "GAME_OVER"

        if not self._safe_save_player(player):
            return "SAVE_ERROR"

        return "UPDATED"

    def process_monster_turns(self):
        """
        Run one monster turn for all alive monsters after the player takes a turn.
        """
        player = self.world.player
        if not player or player.dead:
            return []

        logs = []

        for monster in self.world.monsters:
            if not monster.is_alive():
                continue
            
            if monster.level != self.world.current_level:
                continue

            tile = self.world.get_tile(monster.q, monster.r)
            if not tile or not tile.unlocked:
                continue

            result = monster.decide_and_act(self.world, player)
            logs.append(result)

            # Save each monster after it acts
            if hasattr(self.db, "save_monster"):
                self.db.save_monster(monster)

            # Stop early if player died during monster actions
            if player.dead:
                break

        # Save player state too, because monsters may have damaged the player
        self.db.save_player(self.session_id, player)
        return logs
    
    def run_turn(self, action):
        result = self.handle_input(action)

        if result == "GAME_OVER":
            return "GAME_OVER"

        if result != "TURN_TAKEN":
            return "NO_ACTION"

        self.monsters_need_turn = True 

        game_state = self.update()
        if game_state == "GAME_OVER":
            return "GAME_OVER"
        
        if self.check_level_completed():
            unlocked = self.world.unlock_next_level()
            #print("current level:", self.world.current_level, "max level:", self.world.get_max_level())
            if unlocked:
                self.start_time = time.time()

        return "TURN_DONE"
    
    def check_level_completed(self):
        current_level_monsters = [
            m for m in self.world.monsters
            if m.level == self.world.current_level and m.is_alive()
            ]
        return len(current_level_monsters) == 0
    
        #return (time.time() - self.start_time > 10 and self.world.current_level < self.world.get_max_level())
        
