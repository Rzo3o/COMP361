import pytest
import sqlite3
import time


from database.db_manager import DatabaseManager
from gameplay.models import Tile
from gameplay.world import World
from gameplay.engine import GameEngine


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
    name TEXT,
    item_type TEXT,
    slot TEXT,
    base_damage INTEGER DEFAULT 0,
    defense INTEGER DEFAULT 0,
    durability INTEGER DEFAULT 0,
    max_durability INTEGER DEFAULT 0
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

    # one session
    cur.execute(
        "INSERT INTO game_sessions (id, slot_number, character_type) VALUES (1, 1, 'warrior')"
    )

    # level 1 tiles
    cur.execute(
        """
        INSERT INTO map_tiles
        (id, q, r, tile_type, level, is_permanently_passable, texture_file)
        VALUES (1, 0, 0, 'grass', 1, 1, 'grass.png')
        """
    )
    cur.execute(
        """
        INSERT INTO map_tiles
        (id, q, r, tile_type, level, is_permanently_passable, texture_file)
        VALUES (2, 1, 0, 'grass', 1, 1, 'grass.png')
        """
    )

    # level 2 tiles
    cur.execute(
        """
        INSERT INTO map_tiles
        (id, q, r, tile_type, level, is_permanently_passable, texture_file)
        VALUES (3, 2, 0, 'grass', 2, 1, 'grass.png')
        """
    )
    cur.execute(
        """
        INSERT INTO map_tiles
        (id, q, r, tile_type, level, is_permanently_passable, texture_file)
        VALUES (4, 3, 0, 'grass', 2, 1, 'grass.png')
        """
    )

    # player on level 1
    cur.execute(
        """
        INSERT INTO player_state
        (session_id, current_q, current_r, health, max_health, hunger, max_hunger, experience, death_count, texture_file)
        VALUES (1, 0, 0, 100, 100, 100, 100, 0, 0, NULL)
        """
    )

    conn.commit()


@pytest.fixture
def db(tmp_path):
    db_path = tmp_path / "test_levels.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA_SQL)
    seed_basic_world(conn)
    conn.close()

    dbm = DatabaseManager(str(db_path))
    yield dbm
    dbm.close()


def initialize_level_unlocks_for_test(db: DatabaseManager, session_id: int):
    # Use the SQLite-compatible form
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


def test_initialize_level_unlocks_only_level1_is_open(db):
    initialize_level_unlocks_for_test(db, 1)

    rows = db.cursor.execute(
        """
        SELECT m.level, s.is_unlocked
        FROM session_world_state s
        JOIN map_tiles m ON m.id = s.tile_id
        WHERE s.session_id = 1
        ORDER BY m.id
        """
    ).fetchall()

    assert len(rows) == 4
    for row in rows:
        if row["level"] == 1:
            assert row["is_unlocked"] == 1
        else:
            assert row["is_unlocked"] == 0


def test_tile_safe_default_unlock_logic():
    level1_tile = Tile(
        {
            "id": 1,
            "q": 0,
            "r": 0,
            "level": 1,
            "tile_type": "grass",
            "is_permanently_passable": 1,
        }
    )
    level2_tile = Tile(
        {
            "id": 2,
            "q": 1,
            "r": 0,
            "level": 2,
            "tile_type": "grass",
            "is_permanently_passable": 1,
        }
    )

    assert level1_tile.unlocked is True
    assert level2_tile.unlocked is False


def test_world_get_max_level(db):
    initialize_level_unlocks_for_test(db, 1)
    world = World(db, 1)

    assert world.get_max_level() == 2


def test_world_unlock_next_level_updates_memory_and_db(db):
    initialize_level_unlocks_for_test(db, 1)
    world = World(db, 1)

    level2_tiles_before = [t for t in world.tiles.values() if t.level == 2]
    assert level2_tiles_before
    assert all(t.unlocked is False for t in level2_tiles_before)

    unlocked = world.unlock_next_level()

    assert unlocked is True
    assert world.current_level == 2

    level2_tiles_after = [t for t in world.tiles.values() if t.level == 2]
    assert all(t.unlocked is True for t in level2_tiles_after)

    db_rows = db.cursor.execute(
        """
        SELECT s.is_unlocked
        FROM session_world_state s
        JOIN map_tiles m ON m.id = s.tile_id
        WHERE s.session_id = 1 AND m.level = 2
        """
    ).fetchall()

    assert db_rows
    assert all(row["is_unlocked"] == 1 for row in db_rows)


def test_world_unlock_next_level_stops_at_max_level(db):
    initialize_level_unlocks_for_test(db, 1)
    world = World(db, 1)

    assert world.unlock_next_level() is True
    assert world.current_level == 2

    # no level 3 exists
    assert world.unlock_next_level() is False
    assert world.current_level == 2


def test_engine_check_level_completed_timer(monkeypatch, db):
    initialize_level_unlocks_for_test(db, 1)

    # make engine init lighter and independent from inventory/equipment details
    monkeypatch.setattr(GameEngine, "load_inventory", lambda self: None)
    monkeypatch.setattr(GameEngine, "_apply_equipment", lambda self: None)

    engine = GameEngine(db, 1)

    # before timer
    monkeypatch.setattr(time, "time", lambda: engine.start_time + 5)
    assert engine.check_level_completed() is False

    # after timer, still below max level
    monkeypatch.setattr(time, "time", lambda: engine.start_time + 11)
    assert engine.check_level_completed() is True

    # at max level -> should stop
    engine.world.current_level = engine.world.get_max_level()
    assert engine.check_level_completed() is False


class FakeMonster:
    def __init__(self, name, level, q, r, alive=True):
        self.name = name
        self.level = level
        self.q = q
        self.r = r
        self._alive = alive
        self.acted = False

    def is_alive(self):
        return self._alive

    def decide_and_act(self, world, player):
        self.acted = True
        return {"name": self.name, "action": "acted"}


def test_process_monster_turns_only_current_level_monsters_act(monkeypatch, db):
    initialize_level_unlocks_for_test(db, 1)

    monkeypatch.setattr(GameEngine, "load_inventory", lambda self: None)
    monkeypatch.setattr(GameEngine, "_apply_equipment", lambda self: None)

    engine = GameEngine(db, 1)
    engine.world.current_level = 1

    # prevent DB save logic from caring about fake monster shape
    monkeypatch.setattr(engine.db, "save_monster", lambda monster: None)
    monkeypatch.setattr(engine.db, "save_player", lambda session_id, player: None)

    m1 = FakeMonster("L1-alive", level=1, q=0, r=0, alive=True)
    m2 = FakeMonster("L2-alive", level=2, q=2, r=0, alive=True)
    m3 = FakeMonster("L1-dead", level=1, q=1, r=0, alive=False)

    engine.world.monsters = [m1, m2, m3]

    logs = engine.process_monster_turns()

    assert m1.acted is True
    assert m2.acted is False
    assert m3.acted is False
    assert len(logs) == 1
    assert logs[0]["name"] == "L1-alive"