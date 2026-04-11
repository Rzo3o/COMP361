# tests/conftest.py
import sqlite3
import pytest
from database.db_manager import DatabaseManager

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS game_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_number INTEGER UNIQUE,
    character_type TEXT DEFAULT 'warrior'
);

CREATE TABLE IF NOT EXISTS map_tiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    q INTEGER NOT NULL,
    r INTEGER NOT NULL,
    tile_type TEXT DEFAULT 'grass',
    level INTEGER DEFAULT 1,
    texture_file TEXT,
    prop_texture_file TEXT,
    prop_scale REAL DEFAULT 1.0,
    prop_x_shift INTEGER DEFAULT 0,
    prop_y_shift INTEGER DEFAULT 0,
    is_spawn BOOLEAN DEFAULT 0,
    is_permanently_passable BOOLEAN DEFAULT 1,
    UNIQUE(q, r)
);

CREATE TABLE IF NOT EXISTS session_world_state (
    session_id INTEGER,
    tile_id INTEGER,
    is_discovered BOOLEAN DEFAULT 0,
    is_unlocked BOOLEAN DEFAULT 1,
    is_conquered BOOLEAN DEFAULT 0,
    PRIMARY KEY (session_id, tile_id)
);

CREATE TABLE IF NOT EXISTS player_state (
    session_id INTEGER PRIMARY KEY,
    current_q INTEGER NOT NULL,
    current_r INTEGER NOT NULL,
    health INTEGER DEFAULT 100,
    max_health INTEGER DEFAULT 100,
    hunger INTEGER DEFAULT 100,
    max_hunger INTEGER DEFAULT 100,
    experience INTEGER DEFAULT 0,
    death_count INTEGER DEFAULT 0,
    texture_file TEXT
);

CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    tile INTEGER REFERENCES map_tiles(id) ON DELETE SET NULL, 
    item_type TEXT NOT NULL, 
    slot TEXT DEFAULT NULL, 
    weight INTEGER DEFAULT 1,
    base_damage INTEGER DEFAULT 0,
    defense INTEGER DEFAULT 0, 
    max_durability INTEGER DEFAULT 0,
    durability INTEGER DEFAULT 0,
    healing_amount INTEGER DEFAULT 0,
    hunger_restore INTEGER DEFAULT 0,
    texture_file TEXT,
    power_bonus INTEGER DEFAULT 0 
);

CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    item_id INTEGER,
    quantity INTEGER DEFAULT 1,
    is_equipped BOOLEAN DEFAULT 0
);

CREATE TABLE IF NOT EXISTS monsters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    current_q INTEGER NOT NULL,
    current_r INTEGER NOT NULL,
    level INTEGER DEFAULT 1,
    health INTEGER DEFAULT 50,
    damage INTEGER DEFAULT 10,
    is_defeated BOOLEAN DEFAULT 0,
    texture_file TEXT,
    weapon_item_id INTEGER,
    head_item_id INTEGER,
    chest_item_id INTEGER,
    legs_item_id INTEGER
);
"""

def seed_basic_world(conn: sqlite3.Connection):
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO game_sessions (id, slot_number, character_type) VALUES (1, 1, 'warrior')"
    )

    cur.execute("""
        INSERT INTO map_tiles
        (id, q, r, tile_type, level, is_permanently_passable, texture_file)
        VALUES (1, 0, 0, 'grass', 1, 1, 'grass.png')
    """)
    cur.execute("""
        INSERT INTO map_tiles
        (id, q, r, tile_type, level, is_permanently_passable, texture_file)
        VALUES (2, 1, 0, 'grass', 1, 1, 'grass.png')
    """)
    cur.execute("""
        INSERT INTO map_tiles
        (id, q, r, tile_type, level, is_permanently_passable, texture_file)
        VALUES (3, 2, 0, 'grass', 2, 1, 'grass.png')
    """)
    cur.execute("""
        INSERT INTO map_tiles
        (id, q, r, tile_type, level, is_permanently_passable, texture_file)
        VALUES (4, 3, 0, 'grass', 2, 1, 'grass.png')
    """)

    cur.execute("""
        INSERT INTO player_state
        (session_id, current_q, current_r, health, max_health, hunger, max_hunger, experience, death_count, texture_file)
        VALUES (1, 0, 0, 100, 100, 100, 100, 0, 0, NULL)
    """)

    conn.commit()

@pytest.fixture
def db(tmp_path):
    db_path = tmp_path / "test_game.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA_SQL)
    seed_basic_world(conn)
    conn.close()

    dbm = DatabaseManager(str(db_path))
    yield dbm
    dbm.close()

def initialize_level_unlocks_for_test(db: DatabaseManager, session_id: int):
    db.cursor.execute(
        """
        INSERT OR IGNORE INTO session_world_state
        (session_id, tile_id, is_unlocked, is_discovered, is_conquered)
        SELECT ?, id,
               CASE WHEN level = 1 THEN 1 ELSE 0 END,
               0,
               0
        FROM map_tiles
        """,
        (session_id,),
    )
    db.conn.commit()