import sqlite3
import os
import json


class DatabaseManager:
    def __init__(self, db_file="game_data.db"):
        self.db_file = db_file
        self.conn = sqlite3.connect(db_file)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._check_schema()

    def _check_schema(self):
        """Ensures the database has the required tables."""
        self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='game_sessions'"
        )
        if not self.cursor.fetchone():
            print("Database tables missing. Initializing from database.sql...")
            if os.path.exists("database.sql"):
                with open("database.sql", "r") as f:
                    sql_script = f.read()
                try:
                    self.cursor.executescript(sql_script)
                    self.conn.commit()
                    print("Database initialized successfully.")
                except sqlite3.Error as e:
                    print(f"Error initializing database: {e}")
            else:
                print("Error: database.sql not found. Cannot initialize database.")

    def close(self):
        self.conn.close()

    # =========================
    # Session Management
    # =========================

    def get_session(self, slot_id):
        self.cursor.execute(
            "SELECT * FROM game_sessions WHERE slot_number = ?", (slot_id,)
        )
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def create_session(self, slot_id, char_type="warrior"):
        """Creates or resets a game session at the given slot."""
        existing = self.get_session(slot_id)

        if existing:
            sid = existing["id"]
            # Clear old session data
            self.cursor.execute(
                "DELETE FROM session_world_state WHERE session_id=?", (sid,)
            )
            self.cursor.execute("DELETE FROM player_state WHERE session_id=?", (sid,))
            self.cursor.execute("DELETE FROM inventory WHERE session_id=?", (sid,))
            self.cursor.execute(
                "UPDATE game_sessions SET character_type=?, created_at=CURRENT_TIMESTAMP WHERE id=?",
                (char_type, sid),
            )
            session_id = sid
        else:
            self.cursor.execute(
                "INSERT INTO game_sessions (slot_number, character_type) VALUES (?, ?)",
                (slot_id, char_type),
            )
            session_id = self.cursor.lastrowid

        # Initialize Player State
        # We need a default texture.
        # Ideally, this should be handled by Gameplay logic, but for now we follow the old pattern
        # to ensure compatibility, or we just insert defaults and let the Player class handle loading.
        # I'll keep it simple: just insert defaults.

        default_texture = None
        player_def_dir = "assets/definitions/player"
        if os.path.exists(player_def_dir):
            for f in os.listdir(player_def_dir):
                if f.endswith(".json"):
                    try:
                        with open(os.path.join(player_def_dir, f), "r") as jf:
                            data = json.load(jf)
                            if "animations" in data and "idle" in data["animations"]:
                                default_texture = data["animations"]["idle"].get(
                                    "texture"
                                )
                            if not default_texture:
                                default_texture = data.get("texture_file")

                            if default_texture:
                                break  # Found a valid definition
                    except Exception as e:
                        print(f"Error reading player def {f}: {e}")

        self.cursor.execute(
            """INSERT INTO player_state (session_id, current_q, current_r, health, max_health, texture_file) 
               VALUES (?, 0, 0, 100, 100, ?)""",
            (session_id, default_texture),
        )

        self.conn.commit()
        return session_id

    # =========================
    # World State
    # =========================

    def load_world_state(self, session_id):
        """Returns all tiles with discovery status for the session."""
        query = """
        SELECT m.*, s.is_discovered, s.is_unlocked, s.is_conquered
        FROM map_tiles m
        LEFT JOIN session_world_state s ON m.id = s.tile_id AND s.session_id = ?
        """
        self.cursor.execute(query, (session_id,))
        return [dict(row) for row in self.cursor.fetchall()]

    def update_discovery(self, session_id, tile_id):
        self.cursor.execute(
            """
            INSERT INTO session_world_state (session_id, tile_id, is_discovered)
            VALUES (?, ?, 1)
            ON CONFLICT(session_id, tile_id) DO UPDATE SET is_discovered=1
            """,
            (session_id, tile_id),
        )
        self.conn.commit()

    # =========================
    # Player State
    # =========================

    def save_player(self, session_id, player_data):
        """
        player_data expected to be a dict or object with:
        q, r, hp, hunger, xp
        """
        # If it's an object, convert to dict-like access or usage
        q = getattr(player_data, "q", 0)
        r = getattr(player_data, "r", 0)
        hp = getattr(player_data, "hp", 100)
        hunger = getattr(player_data, "hunger", 100)
        xp = getattr(player_data, "xp", 0)

        self.cursor.execute(
            """
            UPDATE player_state 
            SET current_q=?, current_r=?, health=?, hunger=?, experience=?
            WHERE session_id=?
            """,
            (q, r, hp, hunger, xp, session_id),
        )
        self.conn.commit()

    def get_player_state(self, session_id):
        self.cursor.execute(
            "SELECT * FROM player_state WHERE session_id=?", (session_id,)
        )
        row = self.cursor.fetchone()
        return dict(row) if row else None

    """
    Inventory
    """

    def load_inventory(self, session_id):
        """Returns all items in the player's inventory for this session."""
        query = """
        SELECT i.*, inv.quantity, inv.is_equipped
        FROM inventory inv
        JOIN items i ON inv.item_id = i.id
        WHERE inv.session_id = ?
        """
        self.cursor.execute(query, (session_id,))
        return [dict(row) for row in self.cursor.fetchall()]

    def add_item(self, session_id, item_id, quantity=1):
        """Adds an item to inventory. Stacks if already owned."""
        self.cursor.execute(
            "SELECT id, quantity FROM inventory WHERE session_id=? AND item_id=?",
            (session_id, item_id),
        )
        existing = self.cursor.fetchone()
        if existing:
            self.cursor.execute(
                "UPDATE inventory SET quantity=? WHERE id=?",
                (existing["quantity"] + quantity, existing["id"]),
            )
        else:
            self.cursor.execute(
                "INSERT INTO inventory (session_id, item_id, quantity) VALUES (?, ?, ?)",
                (session_id, item_id, quantity),
            )
        self.conn.commit()

    def remove_item(self, session_id, item_id, quantity=1):
        """Removes quantity of an item. Deletes row if quantity hits 0."""
        self.cursor.execute(
            "SELECT id, quantity FROM inventory WHERE session_id=? AND item_id=?",
            (session_id, item_id),
        )
        existing = self.cursor.fetchone()
        if not existing:
            return
        new_qty = existing["quantity"] - quantity
        if new_qty <= 0:
            self.cursor.execute("DELETE FROM inventory WHERE id=?", (existing["id"],))
        else:
            self.cursor.execute(
                "UPDATE inventory SET quantity=? WHERE id=?",
                (new_qty, existing["id"]),
            )
        self.conn.commit()

    def toggle_equip(self, session_id, item_id):
        """Toggles is_equipped for an equippable item.
        When equipping, unequips any other item in the same slot first."""
        self.cursor.execute(
            "SELECT inv.id, inv.is_equipped, i.slot FROM inventory inv "
            "JOIN items i ON inv.item_id = i.id "
            "WHERE inv.session_id=? AND inv.item_id=?",
            (session_id, item_id),
        )
        row = self.cursor.fetchone()
        if not row:
            return

        if row["is_equipped"]:
            # Unequip
            self.cursor.execute(
                "UPDATE inventory SET is_equipped=0 WHERE id=?", (row["id"],)
            )
        else:
            # Unequip any other item in the same slot first
            slot = row["slot"]
            if slot:
                self.cursor.execute(
                    "UPDATE inventory SET is_equipped=0 "
                    "WHERE session_id=? AND is_equipped=1 AND item_id IN "
                    "(SELECT id FROM items WHERE slot=?)",
                    (session_id, slot),
                )
            # Equip this item
            self.cursor.execute(
                "UPDATE inventory SET is_equipped=1 WHERE id=?", (row["id"],)
            )
        self.conn.commit()

    def get_equipped_items(self, session_id):
        """Returns all currently equipped items for the session."""
        query = """
        SELECT i.*, inv.is_equipped
        FROM inventory inv
        JOIN items i ON inv.item_id = i.id
        WHERE inv.session_id = ? AND inv.is_equipped = 1
        """
        self.cursor.execute(query, (session_id,))
        return [dict(row) for row in self.cursor.fetchall()]

    # =========================
    # Editor / Map Management
    # =========================

    def get_tile(self, q, r):
        self.cursor.execute("SELECT * FROM map_tiles WHERE q=? AND r=?", (q, r))
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def get_all_tiles(self):
        self.cursor.execute("SELECT * FROM map_tiles")
        return [dict(row) for row in self.cursor.fetchall()]

    def save_tile(self, data):
        """
        data: dict containing tile attributes
        """
        if data.get("is_spawn"):
            self.cursor.execute("UPDATE map_tiles SET is_spawn = 0")

        self.cursor.execute(
            """
            INSERT INTO map_tiles (q, r, tile_type, texture_file, prop_texture_file, prop_scale, prop_y_shift, is_spawn)
            VALUES (:q, :r, :tile_type, :texture_file, :prop_texture_file, :prop_scale, :prop_y_shift, :is_spawn)
            ON CONFLICT(q,r) DO UPDATE SET
                tile_type=excluded.tile_type, texture_file=excluded.texture_file,
                prop_texture_file=excluded.prop_texture_file, 
                prop_scale=excluded.prop_scale, prop_y_shift=excluded.prop_y_shift,
                is_spawn=excluded.is_spawn
            """,
            data,
        )
        self.conn.commit()

    def delete_tile(self, q, r):
        self.cursor.execute("DELETE FROM map_tiles WHERE q=? AND r=?", (q, r))
        self.conn.commit()
