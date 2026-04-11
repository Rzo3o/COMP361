
import time
from gameplay.models import Tile
from gameplay.world import World
from gameplay.engine import GameEngine
from conftest import initialize_level_unlocks_for_test

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

def test_engine_check_level_completed_when_current_level_monsters_are_dead(monkeypatch, db):
    initialize_level_unlocks_for_test(db, 1)

    monkeypatch.setattr(GameEngine, "load_inventory", lambda self: None, raising=False)
    monkeypatch.setattr(GameEngine, "_apply_equipment", lambda self: None, raising=False)
    monkeypatch.setattr(World, "load_monsters", lambda self: setattr(self, "monsters", []))

    engine = GameEngine(db, 1)
    engine.world.current_level = 1

    class FakeMonster:
        def __init__(self, level, alive):
            self.level = level
            self._alive = alive

        def is_alive(self):
            return self._alive

    # one alive monster in current level -> not completed
    engine.world.monsters = [
        FakeMonster(level=1, alive=True),
        FakeMonster(level=2, alive=True),
    ]
    assert engine.check_level_completed() is False

    # current level monsters dead, other level monster alive -> completed
    engine.world.monsters = [
        FakeMonster(level=1, alive=False),
        FakeMonster(level=2, alive=True),
    ]
    assert engine.check_level_completed() is True