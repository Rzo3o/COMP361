"""
One-time script to seed test items into game_data_1.db for manual testing.
This inserts an Iron Sword, 3 Bread, and 2 Health Potions into slot 1's inventory.
Run: python seed_test_items.py
Then: python main.py  (select slot 1)
"""

import sqlite3
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB_FILE = ROOT / "game_data_1.db"

if not DB_FILE.exists():
    print(f"{DB_FILE} not found! Start the game once first to create it.")
    exit(1)

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# Insert sample items
c.execute(
    """INSERT OR IGNORE INTO items
    (id, name, item_type, weight, base_damage, max_durability, durability, healing_amount, hunger_restore)
    VALUES (1, 'Iron Sword', 'weapon', 3, 15, 100, 100, 0, 0)"""
)

c.execute(
    """INSERT OR IGNORE INTO items
    (id, name, item_type, weight, base_damage, max_durability, durability, healing_amount, hunger_restore)
    VALUES (2, 'Bread', 'food', 1, 0, 0, 0, 25, 20)"""
)

c.execute(
    """INSERT OR IGNORE INTO items
    (id, name, item_type, weight, base_damage, max_durability, durability, healing_amount, hunger_restore)
    VALUES (3, 'Health Potion', 'food', 1, 0, 0, 0, 50, 0)"""
)

# Give them to session 1's inventory
c.execute(
    "INSERT OR IGNORE INTO inventory (session_id, item_id, quantity) VALUES (1, 1, 1)"
)
c.execute(
    "INSERT OR IGNORE INTO inventory (session_id, item_id, quantity) VALUES (1, 2, 3)"
)
c.execute(
    "INSERT OR IGNORE INTO inventory (session_id, item_id, quantity) VALUES (1, 3, 2)"
)

conn.commit()
conn.close()
print(
    """Test items seeded into game_data_1.db!
    - Iron Sword x1 (weapon, 15 dmg)
    - Bread x3 (food, heals 25 HP, +20 hunger)
    - Health Potion x2 (food, heals 50 HP)
Now run: python main.py  (select slot 1)"""
)
