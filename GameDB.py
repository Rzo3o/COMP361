import sqlite3
import os
import json


class GameDB:
    def __init__(self, db_file="game_data.db"):
        self.conn = sqlite3.connect(db_file)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._check_schema()

    def _check_schema(self):
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

    def get_session(self, slot_id):
        self.cursor.execute(
            "SELECT * FROM game_sessions WHERE slot_number = ?", (slot_id,)
        )
        return self.cursor.fetchone()

    def create_session(self, slot_id, char_type="warrior"):
        existing = self.get_session(slot_id)

        if existing:
            sid = existing["id"]
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

    def load_world_state(self, session_id):
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

    def save_player(self, session_id, player_obj):
        self.cursor.execute(
            """
            UPDATE player_state 
            SET current_q=?, current_r=?, health=?, hunger=?, experience=?
            WHERE session_id=?
        """,
            (
                player_obj.q,
                player_obj.r,
                player_obj.hp,
                player_obj.hunger,
                player_obj.xp,
                session_id,
            ),
        )
        self.conn.commit()

    def get_player_state(self, session_id):
        self.cursor.execute(
            "SELECT * FROM player_state WHERE session_id=?", (session_id,)
        )
        row = self.cursor.fetchone()
        return dict(row) if row else None
