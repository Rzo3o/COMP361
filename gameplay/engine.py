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

    def load_inventory(self):
        """Load inventory from DB into Item objects."""
        rows = self.db.load_inventory(self.session_id)
        self.inventory = []
        for row in rows:
            item = Item(row)
            item.quantity = row.get("quantity", 1)
            item.equipped = bool(row.get("is_equipped", 0))
            self.inventory.append(item)

    def handle_input(self, action):
        if self.world.player.dead:
            return "GAME_OVER"

        # --- Inventory screen controls ---
        if self.show_inventory:
            if action == "INVENTORY":
                self.show_inventory = False
                return "NO_ACTION"
            if action == "MOVE_NORTH" and self.selected_index > 0:
                self.selected_index -= 1
            elif (
                action == "MOVE_SOUTH" and self.selected_index < len(self.inventory) - 1
            ):
                self.selected_index += 1
            elif action == "INTERACT":
                self.use_selected_item()
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
        # Check if the action is a movement
        if action in move_map:
            dq, dr = move_map[action]
            self.attempt_move(dq, dr)
            return "TURN_TAKEN"

        if action == "INVENTORY":
            self.show_inventory = True
            self.selected_index = 0
            self.load_inventory()  # refresh from DB
            return "NO_ACTION"

        return "NO_ACTION"

    def use_selected_item(self):
        """Use or equip the currently selected inventory item."""
        if not self.inventory or self.selected_index >= len(self.inventory):
            return
        item = self.inventory[self.selected_index]
        player = self.world.player

        if item.type == "food":
            if item.use(player):
                self.db.remove_item(self.session_id, item.id)
                self.db.save_player(self.session_id, player)
                self.load_inventory()
                # Adjust cursor if list got shorter
                if self.selected_index >= len(self.inventory):
                    self.selected_index = max(0, len(self.inventory) - 1)
        elif item.type == "weapon":
            self.db.toggle_equip(self.session_id, item.id)
            self.load_inventory()

    def attempt_move(self, dq, dr):
        """
        Try to move the player by (dq, dr).
        Returns True if movement succeeds, otherwise False.
        """
        player = self.world.player
        target_q = player.q + dq
        target_r = player.r + dr

        if not self.world.is_passable(target_q, target_r):
            return False

        player.move(dq, dr)
        self.world.update_fog_of_war()
        self.db.save_player(self.session_id, player)
        return True

    def update(self):
        player = self.world.player

        if player.dead:
            return "GAME_OVER"

        if player.hunger > 0:
            player.hunger -= 1

        if player.hunger <= 0:
            player.hunger = 0
            if player.health > 0:
                player.health -= 1

        if player.health <= 0:
            player.health = 0
            player.dead = True

            if hasattr(player, "death_count"):
                player.death_count += 1

            self.db.save_player(self.session_id, player)
            return "GAME_OVER"

        self.db.save_player(self.session_id, player)
        return "UPDATED"
