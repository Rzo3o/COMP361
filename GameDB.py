import sqlite3
import os


class GameDB:
    def __init__(self, db_path="game_data.db"):
        self.db_path = db_path
        # Check if we need to initialize the DB before connecting
        db_exists = os.path.exists(db_path)

        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

        if not db_exists:
            self._initialize_schema()

    def _initialize_schema(self):
        """Reads the SQL file and creates the tables."""
        if os.path.exists("database.sql"):
            with open("database.sql", "r") as f:
                sql_script = f.read()
            self.conn.executescript(sql_script)
            self.conn.commit()
            print("Database initialized successfully.")
        else:
            print("Warning: database.sql not found. Tables were not created.")

    def get_map(self):
        cursor = self.conn.cursor()
        # Join tiles with state for a specific session (e.g., Session 1)
        query = """
            SELECT t.*, s.is_discovered, s.is_conquered 
            FROM map_tiles t
            LEFT JOIN session_world_state s ON t.id = s.tile_id
            WHERE s.session_id = 1 OR s.session_id IS NULL
        """
        cursor.execute(query)
        return cursor.fetchall()

    def update_player_pos(self, session_id, q, r):
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE player_state SET current_q = ?, current_r = ? WHERE session_id = ?",
            (q, r, session_id),
        )
        self.conn.commit()
