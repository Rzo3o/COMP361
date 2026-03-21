from gameplay.world import World
from gameplay.item import Item


class GameEngine:
    def __init__(self, db, session_id):
        self.db = db
        self.session_id = session_id
        self.world = World(db, session_id)
        self.world.update_fog_of_war()
        self.inventory = []  # list of Item objects
        self.show_inventory = False  # toggle flag
        self.selected_index = 0  # cursor position in inventory
        self.load_inventory()
        self._apply_equipment()

    def load_inventory(self):
        """Load inventory from DB into Item objects."""
        rows = self.db.load_inventory(self.session_id)
        self.inventory = []
        for row in rows:
            item = Item(row)
            item.quantity = row.get("quantity", 1)
            item.equipped = bool(row.get("is_equipped", 0))
            self.inventory.append(item)

    def _apply_equipment(self):
        """Sync equipped items from inventory into player equipment slots."""
        player = self.world.player
        if not player:
            return
        # Clear all slots first
        for slot in player.equipment:
            player.equipment[slot] = None
        # Apply equipped items
        for item in self.inventory:
            if item.equipped and item.is_equippable:
                player.equipment[item.slot] = item

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
                return "NO_ACTION"
            if action == "MOVE_NORTH" and self.selected_index > 0:
                self.selected_index -= 1
            elif (
                action == "MOVE_SOUTH"
                and self.selected_index < len(self.inventory) - 1
            ):
                self.selected_index += 1
            elif action == "INTERACT":
                self.use_selected_item()
            elif action == "MOVE_WEST":
                self.drop_selected_item()
            return "NO_ACTION"

        # --- Normal gameplay controls ---
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

                if hasattr(self.db, "save_monster"):
                    self.db.save_monster(monster)
                self.db.save_player(self.session_id, player)

                print(f"Player attacked {monster.name} for {damage} damage")
                return "TURN_TAKEN"
            
            # if no monster, then try to move
            moved = self.attempt_move(dq, dr)
            return "TURN_TAKEN" if moved else "NO_ACTION"

        if action == "INVENTORY":
            self.show_inventory = True
            self.selected_index = 0
            self.load_inventory()
            return "NO_ACTION"

        return "NO_ACTION"

    def use_selected_item(self):
        """Use or equip/unequip the currently selected inventory item."""
        if not self.inventory or self.selected_index >= len(self.inventory):
            return
        item = self.inventory[self.selected_index]
        player = self.world.player

        if item.type == "food":
            if item.use(player):
                self.db.remove_item(self.session_id, item.id)
                self.db.save_player(self.session_id, player)
                self.load_inventory()
                self._apply_equipment()
                if self.selected_index >= len(self.inventory):
                    self.selected_index = max(0, len(self.inventory) - 1)

        elif item.is_equippable:
            self.db.toggle_equip(self.session_id, item.id)
            self.load_inventory()
            self._apply_equipment()

    def drop_selected_item(self):
        """Drop one of the selected item from inventory."""
        if not self.inventory or self.selected_index >= len(self.inventory):
            return
        item = self.inventory[self.selected_index]
        self.db.remove_item(self.session_id, item.id, quantity=1)
        self.load_inventory()
        self._apply_equipment()
        if self.selected_index >= len(self.inventory):
            self.selected_index = max(0, len(self.inventory) - 1)

    def _safe_save_player(self, player):
        try:
            self.db.save_player(self.session_id, player)
            return True
        except Exception:
            return False

    def attempt_move(self, dq, dr):
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
                player.hp -= 1

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

        self.process_monster_turns()

        game_state = self.update()
        if game_state == "GAME_OVER":
            return "GAME_OVER"

        return "TURN_DONE"
        
        