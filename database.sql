-- ==========================================
-- 1. CORE SESSION MANAGEMENT (3 SAVE SLOTS)
-- ==========================================
CREATE TABLE game_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_number INTEGER UNIQUE CHECK (slot_number BETWEEN 1 AND 3),
    save_name TEXT DEFAULT 'New Game',
    difficulty TEXT DEFAULT 'medium' CHECK (difficulty IN ('easy', 'medium', 'hard')),
    hunger_drain_rate REAL DEFAULT 1.0,
    enemy_damage_mult REAL DEFAULT 1.0,
    character_type TEXT DEFAULT 'warrior' CHECK (character_type IN ('warrior', 'archer', 'mage')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_saved DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- 2. MASTER MAP DATA (THE PREMADE WORLD)
-- ==========================================
CREATE TABLE map_tiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    q INTEGER NOT NULL, -- Axial Column
    r INTEGER NOT NULL, -- Axial Row
    tile_type TEXT DEFAULT 'grass', -- 'forest', 'mountain', 'water', 'castle', 'village'
    location_name TEXT, -- 'Oakvale', 'Stonehold Castle', etc.
    level INTEGER DEFAULT 1, -- What level for when 
    texture_file TEXT,
    prop_texture_file TEXT,
    prop_type TEXT, -- 'tree', 'rock', 'building', etc.
    prop_scale REAL DEFAULT 1.0,
    prop_y_shift INTEGER DEFAULT 0,
    is_permanently_passable BOOLEAN DEFAULT 1, -- 0 for deep water/impassable peaks
    UNIQUE(q, r)
);

-- ==========================================
-- 3. SESSION STATE (PROGRESS PER SAVE SLOT)
-- ==========================================
-- This table tracks what is conquered or unlocked in a specific save slot.
CREATE TABLE session_world_state (
    session_id INTEGER REFERENCES game_sessions(id) ON DELETE CASCADE,
    tile_id INTEGER REFERENCES map_tiles(id) ON DELETE CASCADE,
    is_discovered BOOLEAN DEFAULT 0, -- Fog of war logic
    is_unlocked BOOLEAN DEFAULT 1,   -- 0 if blocked by a quest/event
    is_conquered BOOLEAN DEFAULT 0,  -- 1 if player owns the village/castle
    conquered_at DATETIME,
    PRIMARY KEY (session_id, tile_id)
);

-- ==========================================
-- 4. PLAYER STATUS
-- ==========================================
CREATE TABLE player_state (
    session_id INTEGER PRIMARY KEY REFERENCES game_sessions(id) ON DELETE CASCADE,
    current_q INTEGER NOT NULL,
    current_r INTEGER NOT NULL,
    health INTEGER DEFAULT 100,
    max_health INTEGER DEFAULT 100,
    hunger INTEGER DEFAULT 100,
    max_hunger INTEGER DEFAULT 100,
    experience INTEGER DEFAULT 0,
    power_level INTEGER DEFAULT 1, -- Your conquest rank/strength
    death_count INTEGER DEFAULT 0,
    texture_file TEXT,
    FOREIGN KEY (current_q, current_r) REFERENCES map_tiles(q, r)
);

CREATE TABLE monsters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    tile_id INTEGER REFERENCES map_tiles(id) ON DELETE SET NULL,
    health INTEGER DEFAULT 50,
    damage INTEGER DEFAULT 10,
    is_defeated BOOLEAN DEFAULT 0,
    texture_file TEXT
);

-- ==========================================
-- 5. ITEMS & INVENTORY
-- ==========================================
CREATE TABLE items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    tile INTEGER REFERENCES map_tiles(id) ON DELETE SET NULL, -- Where to find it in the world
    item_type TEXT NOT NULL, -- 'weapon', 'food', 'tribute', 'artifact'
    weight INTEGER DEFAULT 1,
    base_damage INTEGER DEFAULT 0,
    max_durability INTEGER DEFAULT 0,
    durability INTEGER DEFAULT 0,
    healing_amount INTEGER DEFAULT 0,
    hunger_restore INTEGER DEFAULT 0,
    texture_file TEXT,
    power_bonus INTEGER DEFAULT 0 -- For artifacts that boost conquest stats
);

CREATE TABLE inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER REFERENCES game_sessions(id) ON DELETE CASCADE,
    item_id INTEGER REFERENCES items(id) ON DELETE CASCADE,
    quantity INTEGER DEFAULT 1,
    is_equipped BOOLEAN DEFAULT 0
);

-- ==========================================
-- 6. AUTOMATION (TRIGGERS)
-- ==========================================
-- Automatically updates the 'last_saved' timestamp when player state changes
CREATE TRIGGER update_save_time
AFTER UPDATE ON player_state
BEGIN
    UPDATE game_sessions 
    SET last_saved = CURRENT_TIMESTAMP 
    WHERE id = NEW.session_id;
END;