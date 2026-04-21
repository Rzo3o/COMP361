from pathlib import Path

from database.db_manager import DatabaseManager
from gameplay.resource_lock import (
    ResourceState,
    ground_resource_id,
    inventory_resource_id,
)


def _make_db(tmp_path, monkeypatch):
    # create a temporary database file and set up the test environment
    project_root = Path(__file__).parent.parent
    monkeypatch.chdir(project_root)
    db = DatabaseManager(db_file=str(tmp_path / "test_inventory_lock.db"))
    sid = db.create_session(1)
    return db, sid


def _insert_item(
    db,
    name="Bread",
    item_type="food",
    slot=None,
    base_damage=0,
    defense=0,
    healing=20,
    hunger=15,
    durability=0,
    max_durability=0,
):
    db.cursor.execute(
        """INSERT INTO items (name, item_type, slot, base_damage, defense,
           healing_amount, hunger_restore, durability, max_durability)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            name,
            item_type,
            slot,
            base_damage,
            defense,
            healing,
            hunger,
            durability,
            max_durability,
        ),
    )
    db.conn.commit()
    return db.cursor.lastrowid


def _insert_spawn_tile(db):
    # Set a tile as spawn point for player to ensure inventory can be loaded without errors
    db.cursor.execute("UPDATE map_tiles SET is_spawn = 1 WHERE q = 0 AND r = 0")
    db.conn.commit()


def _place_item_on_ground(db, item_id, q=0, r=0):
    db.cursor.execute("SELECT id FROM map_tiles WHERE q=? AND r=?", (q, r))
    tile = db.cursor.fetchone()
    if tile is None:
        db.cursor.execute(
            "INSERT INTO map_tiles (q, r, tile_type, is_spawn) VALUES (?, ?, 'grass', 0)",
            (q, r),
        )
        tile_id = db.cursor.lastrowid
    else:
        tile_id = tile["id"]
    db.cursor.execute("UPDATE items SET tile=? WHERE id=?", (tile_id, item_id))
    db.conn.commit()


# Test that inventory items have correct resource IDs for locking
def test_player_inventory_items_use_inventory_entry_resource_ids(tmp_path, monkeypatch):
    db, sid = _make_db(tmp_path, monkeypatch)
    item_id = _insert_item(db)
    db.add_item(sid, item_id, quantity=2)

    from gameplay.world import World

    world = World(db, sid)
    world.player.load_inventory(db, sid)

    item = world.player.inventory[0]
    assert item.inventory_entry_id is not None
    assert item.resource_id == inventory_resource_id(item.inventory_entry_id)
    db.close()

# Test that using 1 item out of 2
def test_engine_use_food_releases_lock_for_remaining_stack(tmp_path, monkeypatch):
    db, sid = _make_db(tmp_path, monkeypatch)
    _insert_spawn_tile(db)

    item_id = _insert_item(db, healing=25, hunger=20, durability=1, max_durability=1)
    db.add_item(sid, item_id, quantity=2)

    from gameplay.engine import GameEngine

    engine = GameEngine(db, sid)
    player = engine.world.player
    resource_id = player.inventory[0].resource_id

    assert engine.world.resource_locks.get_state(resource_id) == ResourceState.AVAILABLE

    player.hp = 50
    player.hunger = 30
    engine.handle_input("INVENTORY")
    engine.handle_input("INTERACT")

    assert player.hp == 75 # 50 + 25 healing
    assert player.hunger == 50 # 30 + 20 hunger restore
    assert player.inventory[0].quantity == 1 # One item should be used, one should remain
    assert engine.world.resource_locks.get_state(resource_id) == ResourceState.AVAILABLE
    db.close()


# Test that using the last item
def test_engine_use_food_consumes_lock_when_stack_empties(tmp_path, monkeypatch):
    db, sid = _make_db(tmp_path, monkeypatch)
    _insert_spawn_tile(db)

    item_id = _insert_item(db, healing=25, hunger=20, durability=1, max_durability=1)
    db.add_item(sid, item_id)

    from gameplay.engine import GameEngine

    engine = GameEngine(db, sid)
    player = engine.world.player
    resource_id = player.inventory[0].resource_id

    # Player must be missing HP or hunger for food to be usable
    player.hp = max(1, player.hp - 30)

    engine.handle_input("INVENTORY")
    engine.handle_input("INTERACT")

    # After using the last item in the stack, the inventory should be empty and the resource lock should be consumed
    assert player.inventory == []
    assert engine.world.resource_locks.get_state(resource_id) == ResourceState.CONSUMED
    db.close()


def test_ground_items_use_ground_resource_ids(tmp_path, monkeypatch):
    db, sid = _make_db(tmp_path, monkeypatch)
    _insert_spawn_tile(db)

    item_id = _insert_item(db, name="Bread")
    _place_item_on_ground(db, item_id, q=0, r=0)

    from gameplay.world import World

    world = World(db, sid)

    item = world.ground_items[0]
    assert item.resource_id == ground_resource_id(item_id)
    db.close()


def test_engine_pickup_consumes_ground_lock(tmp_path, monkeypatch):
    db, sid = _make_db(tmp_path, monkeypatch)
    _insert_spawn_tile(db)

    item_id = _insert_item(db, name="Bread")
    _place_item_on_ground(db, item_id, q=0, r=0)

    from gameplay.engine import GameEngine

    engine = GameEngine(db, sid)
    resource_id = engine.world.ground_items[0].resource_id

    assert engine.world.resource_locks.get_state(resource_id) == ResourceState.AVAILABLE

    result = engine.handle_input("INTERACT")

    assert result == "TURN_TAKEN"
    assert engine.world.resource_locks.get_state(resource_id) == ResourceState.CONSUMED
    assert engine.world.ground_items == []
    db.close()
