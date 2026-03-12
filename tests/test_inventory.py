from pathlib import Path
from database.db_manager import DatabaseManager
from gameplay.item import Item
from gameplay.player import Player


# Helper functions to create a DB with a session + test item


def _make_db(tmp_path, monkeypatch):
    """Returns (db, session_id) with schema initialized."""
    project_root = Path(__file__).parent.parent
    monkeypatch.chdir(project_root)
    db = DatabaseManager(db_file=str(tmp_path / "test_inv.db"))
    sid = db.create_session(1)
    return db, sid


def _insert_item(
    db,
    name="Bread",
    item_type="food",
    base_damage=0,
    healing=20,
    hunger=15,
    durability=0,
    max_durability=0,
):
    """Insert a row into the items table and return its id."""
    db.cursor.execute(
        """INSERT INTO items (name, item_type, base_damage, healing_amount,
           hunger_restore, durability, max_durability)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (name, item_type, base_damage, healing, hunger, durability, max_durability),
    )
    db.conn.commit()
    return db.cursor.lastrowid


# Database tests


def test_add_item_to_inventory(tmp_path, monkeypatch):
    db, sid = _make_db(tmp_path, monkeypatch)
    item_id = _insert_item(db)
    db.add_item(sid, item_id)

    inv = db.load_inventory(sid)
    assert len(inv) == 1
    assert inv[0]["name"] == "Bread"
    assert inv[0]["item_type"] == "food"
    assert inv[0]["quantity"] == 1
    db.close()


def test_add_item_stacks(tmp_path, monkeypatch):
    db, sid = _make_db(tmp_path, monkeypatch)
    item_id = _insert_item(db)
    db.add_item(sid, item_id)
    db.add_item(sid, item_id)

    inv = db.load_inventory(sid)
    assert len(inv) == 1  # one row, not two
    assert inv[0]["quantity"] == 2
    db.close()


def test_remove_item_decrements(tmp_path, monkeypatch):
    db, sid = _make_db(tmp_path, monkeypatch)
    item_id = _insert_item(db)
    db.add_item(sid, item_id, quantity=3)
    db.remove_item(sid, item_id, quantity=1)

    inv = db.load_inventory(sid)
    assert len(inv) == 1
    assert inv[0]["quantity"] == 2
    db.close()


def test_remove_item_deletes_at_zero(tmp_path, monkeypatch):
    db, sid = _make_db(tmp_path, monkeypatch)
    item_id = _insert_item(db)
    db.add_item(sid, item_id, quantity=1)
    db.remove_item(sid, item_id, quantity=1)

    inv = db.load_inventory(sid)
    assert len(inv) == 0
    db.close()


def test_toggle_equip(tmp_path, monkeypatch):
    db, sid = _make_db(tmp_path, monkeypatch)
    item_id = _insert_item(
        db,
        name="Iron Sword",
        item_type="weapon",
        base_damage=10,
        durability=100,
        max_durability=100,
    )
    db.add_item(sid, item_id)

    # Equip
    db.toggle_equip(sid, item_id)
    inv = db.load_inventory(sid)
    assert inv[0]["is_equipped"] == 1

    # Unequip
    db.toggle_equip(sid, item_id)
    inv = db.load_inventory(sid)
    assert inv[0]["is_equipped"] == 0
    db.close()


# B. Item.use() tests


def test_food_use_heals_and_restores_hunger():
    item = Item(
        {
            "id": 1,
            "name": "Bread",
            "item_type": "food",
            "healing_amount": 20,
            "hunger_restore": 15,
        }
    )
    player = Player(
        {
            "current_q": 0,
            "current_r": 0,
            "health": 50,
            "max_health": 100,
            "hunger": 40,
            "max_hunger": 100,
        }
    )
    result = item.use(player)
    assert result is True
    assert player.hp == 70  # 50 + 20
    assert player.hunger == 55  # 40 + 15


def test_food_use_clamps_to_max():
    item = Item(
        {
            "id": 1,
            "name": "Feast",
            "item_type": "food",
            "healing_amount": 999,
            "hunger_restore": 999,
        }
    )
    player = Player(
        {
            "current_q": 0,
            "current_r": 0,
            "health": 90,
            "max_health": 100,
            "hunger": 95,
            "max_hunger": 100,
        }
    )
    item.use(player)
    assert player.hp == 100
    assert player.hunger == 100


def test_weapon_use_returns_false():
    item = Item(
        {
            "id": 2,
            "name": "Sword",
            "item_type": "weapon",
            "base_damage": 15,
        }
    )
    player = Player(
        {
            "current_q": 0,
            "current_r": 0,
            "health": 80,
            "max_health": 100,
            "hunger": 60,
            "max_hunger": 100,
        }
    )
    result = item.use(player)
    assert result is False
    assert player.hp == 80  # unchanged
    assert player.hunger == 60  # unchanged


# Engine tests
# =============================================


def test_engine_inventory_toggle(tmp_path, monkeypatch):
    db, sid = _make_db(tmp_path, monkeypatch)
    # Engine needs tiles in the DB to build the world, so insert a spawn tile
    db.cursor.execute(
        "INSERT INTO map_tiles (q, r, tile_type, is_spawn) VALUES (0, 0, 'grass', 1)"
    )
    db.conn.commit()

    from gameplay.engine import GameEngine

    engine = GameEngine(db, sid)

    assert engine.show_inventory is False
    engine.handle_input("INVENTORY")
    assert engine.show_inventory is True
    engine.handle_input("INVENTORY")
    assert engine.show_inventory is False
    db.close()


def test_engine_use_food_removes_from_inventory(tmp_path, monkeypatch):
    db, sid = _make_db(tmp_path, monkeypatch)
    db.cursor.execute(
        "INSERT INTO map_tiles (q, r, tile_type, is_spawn) VALUES (0, 0, 'grass', 1)"
    )
    db.conn.commit()

    item_id = _insert_item(db, name="Bread", item_type="food", healing=25, hunger=20)
    db.add_item(sid, item_id, quantity=2)

    from gameplay.engine import GameEngine

    engine = GameEngine(db, sid)

    # Damage the player so healing is visible
    engine.world.player.hp = 50
    engine.world.player.hunger = 30

    # Open inventory, use first item
    engine.handle_input("INVENTORY")
    assert engine.show_inventory is True
    engine.handle_input("INTERACT")  # use selected food

    # Verify healing
    assert engine.world.player.hp == 75  # 50 + 25
    assert engine.world.player.hunger == 50  # 30 + 20

    # Verify quantity decreased
    assert len(engine.inventory) == 1
    assert engine.inventory[0].quantity == 1
    db.close()
