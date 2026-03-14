"""
One-time script to seed test items into game_data_1.db for manual testing.
Run: python seed_test_items.py
Then: python main.py  (select slot 1)
"""
import sqlite3
import os

DB_FILE = "game_data_1.db"

if not os.path.exists(DB_FILE):
    print(f"{DB_FILE} not found! Start the game once first to create it.")
    exit(1)

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# Add slot and defense columns if missing (for existing DBs)
try:
    c.execute("ALTER TABLE items ADD COLUMN slot TEXT DEFAULT NULL")
except sqlite3.OperationalError:
    pass
try:
    c.execute("ALTER TABLE items ADD COLUMN defense INTEGER DEFAULT 0")
except sqlite3.OperationalError:
    pass

# Insert sample items
c.execute("""INSERT OR IGNORE INTO items
    (id, name, description, item_type, slot, weight, base_damage, defense,
     max_durability, durability, healing_amount, hunger_restore)
    VALUES (1, 'Iron Sword', 'A sturdy iron blade.', 'weapon', 'weapon',
            3, 15, 0, 100, 100, 0, 0)""")

c.execute("""INSERT OR IGNORE INTO items
    (id, name, description, item_type, slot, weight, base_damage, defense,
     max_durability, durability, healing_amount, hunger_restore)
    VALUES (2, 'Bread', 'Restores hunger and a little health.', 'food', NULL,
            1, 0, 0, 0, 0, 25, 20)""")

c.execute("""INSERT OR IGNORE INTO items
    (id, name, description, item_type, slot, weight, base_damage, defense,
     max_durability, durability, healing_amount, hunger_restore)
    VALUES (3, 'Health Potion', 'A glowing red vial.', 'food', NULL,
            1, 0, 0, 0, 0, 50, 0)""")

c.execute("""INSERT OR IGNORE INTO items
    (id, name, description, item_type, slot, weight, base_damage, defense,
     max_durability, durability, healing_amount, hunger_restore)
    VALUES (4, 'Iron Helmet', 'Protects your head.', 'armor', 'head',
            2, 0, 5, 80, 80, 0, 0)""")

c.execute("""INSERT OR IGNORE INTO items
    (id, name, description, item_type, slot, weight, base_damage, defense,
     max_durability, durability, healing_amount, hunger_restore)
    VALUES (5, 'Chain Chestplate', 'Solid chest protection.', 'armor', 'chest',
            5, 0, 8, 120, 120, 0, 0)""")

c.execute("""INSERT OR IGNORE INTO items
    (id, name, description, item_type, slot, weight, base_damage, defense,
     max_durability, durability, healing_amount, hunger_restore)
    VALUES (6, 'Leather Leggings', 'Light leg armor.', 'armor', 'legs',
            2, 0, 3, 60, 60, 0, 0)""")

# Give them to session 1's inventory
c.execute("INSERT OR IGNORE INTO inventory (session_id, item_id, quantity) VALUES (1, 1, 1)")
c.execute("INSERT OR IGNORE INTO inventory (session_id, item_id, quantity) VALUES (1, 2, 3)")
c.execute("INSERT OR IGNORE INTO inventory (session_id, item_id, quantity) VALUES (1, 3, 2)")
c.execute("INSERT OR IGNORE INTO inventory (session_id, item_id, quantity) VALUES (1, 4, 1)")
c.execute("INSERT OR IGNORE INTO inventory (session_id, item_id, quantity) VALUES (1, 5, 1)")
c.execute("INSERT OR IGNORE INTO inventory (session_id, item_id, quantity) VALUES (1, 6, 1)")

conn.commit()
conn.close()
print("Test items seeded into game_data_1.db!")
print("  - Iron Sword x1     (weapon, +15 ATK)")
print("  - Bread x3          (food, +25 HP, +20 hunger)")
print("  - Health Potion x2  (food, +50 HP)")
print("  - Iron Helmet x1    (head armor, +5 DEF)")
print("  - Chain Chestplate x1 (chest armor, +8 DEF)")
print("  - Leather Leggings x1 (leg armor, +3 DEF)")
print()
print("Now run: python main.py")
