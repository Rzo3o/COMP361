# seed_ground_items.py
import sqlite3

conn = sqlite3.connect("game_data_1.db")
c = conn.cursor()
# Item definition for bread
c.execute(
    "INSERT OR IGNORE INTO items (id, name, item_type, healing_amount, hunger_restore, durability, max_durability) VALUES (100, 'Bread', 'food', 20, 15, 1, 1)"
)
# Place it on the spawn tile
c.execute("SELECT id FROM map_tiles WHERE is_spawn=1 LIMIT 1")
tile_id = c.fetchone()[0]
c.execute("UPDATE items SET tile=? WHERE id=100", (tile_id,))
conn.commit()
print(f"Bread placed on tile {tile_id}")
