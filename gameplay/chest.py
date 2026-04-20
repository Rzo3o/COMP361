"""Chest entity for the loot system.

A Chest is a world object that sits on a tile, blocks movement for both
players and monsters, animates an idle sparkle loop until opened, then
plays a one-shot opening animation and despawns.

Design patterns in this file:
  - Flyweight: chest JSON definitions are loaded once per type and shared
    across every Chest instance of that type via the class-level
    `_definitions` cache.
  - Data-driven entity: all timings, frame counts, and sprite rows come
    from the JSON definition, never hard-coded in the class.
"""

import os
import json

from core.config import Config


class Chest:
    """A chest placed on a tile.

    Lifecycle:
        1. Spawned (by spawn_demo_chest or engine.drop_monster_loot).
        2. Animates its 'idle' row on a loop.
        3. Player presses INTERACT adjacent to it -> open_chest() is
           called, which transitions the state to 'opening'.
        4. Opening animation plays once, holds on the last frame.
        5. After `despawn_delay_ticks` idle ticks post-completion, the
           `remove_after_open` flag flips True and the game window loop
           removes the chest from world.chests.

    Items held in `self.items` are transferred to the player's inventory
    by GameEngine._award_chest_items when the chest is opened. Awarded
    items are drained from the chest so they can never be awarded twice.
    """

    # Flyweight cache: chest_type -> definition dict. Loaded lazily on
    # first request and reused by every Chest instance of that type.
    _definitions = {}

    def __init__(self, q, r, chest_type="brown_chest", items=None):
        """Create a chest at axial coordinates (q, r)."""
        self.q = q
        self.r = r
        self.chest_type = chest_type
        self.items = list(items) if items else []

        data = Chest._load_definition(chest_type)
        self.data = data
        self.animations = data.get("animations", {})

        self.anim_state = "idle"
        self.texture = self.animations.get("idle", {}).get("texture")
        self.anim_row = self.animations.get("idle", {}).get("row", 0)
        self.anim_tick = 0
        self.anim_progress = 0.0
        self.anim_speed = 0.15  # fractional frames advanced per tick

        # Opening lifecycle flags.
        self.opened = False
        self.open_complete = False
        # The main loop calls update_animation every ~50ms, so 7 ticks
        # is roughly a third of a second of chest sits open
        self.despawn_delay_ticks = 7
        self._despawn_counter = 0
        self.remove_after_open = False

    @classmethod
    def _load_definition(cls, chest_type):
        """Load (or return cached) JSON definition for a chest type.

        Uses a class-level flyweight cache so each chest type is parsed
        from disk at most once per game session.

        If the definition file is missing or malformed, logs a warning
        and returns a minimal stub so the game keeps running instead of
        crashing. The stub produces a chest with no animation (texture
        is None) but is safe to animate and open.
        """
        if chest_type in cls._definitions:
            return cls._definitions[chest_type]

        path = os.path.join(Config.DIRS["chest"], f"{chest_type}.json")
        try:
            with open(path, "r") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
            # Graceful degradation: log once and cache an empty stub so
            # subsequent loads don't keep hitting the filesystem.
            print(f"[Chest] Could not load definition '{chest_type}': {e}")
            data = {"animations": {}, "scale": 1.0}

        cls._definitions[chest_type] = data
        return data

    def open_chest(self):
        """Returns True the first time the chest transitions from closed to
        opening (so the engine can award loot exactly once). Subsequent
        calls on an already-opened chest return False.

        """
        if self.opened:
            return False
        self.opened = True
        self.anim_state = "opening"
        self.anim_row = self.animations.get("opening", {}).get("row", 1)
        self.anim_tick = 0
        self.anim_progress = 0.0
        return True

    def update_animation(self, _asset_manager=None):
        """Advance the animation by one tick.

        Called once per animation frame from GameWindow.update.
        """
        anim_cfg = self.animations.get(self.anim_state)
        if not anim_cfg:
            return
        count = anim_cfg.get("count", 1)

        self.anim_progress += self.anim_speed
        self.anim_tick = int(self.anim_progress)

        if self.anim_state == "idle":
            # Loop the idle animation forever.
            if self.anim_tick >= count:
                self.anim_tick = 0
                self.anim_progress = 0.0
            return

        if self.anim_state == "opening":
            # Play once, then hold the last frame.
            if self.anim_tick >= count:
                self.anim_tick = count - 1
                self.anim_progress = float(count - 1)
                self.open_complete = True

            # Once opening has finished, count down toward despawn.
            if self.open_complete and not self.remove_after_open:
                self._despawn_counter += 1
                if self._despawn_counter >= self.despawn_delay_ticks:
                    self.remove_after_open = True
