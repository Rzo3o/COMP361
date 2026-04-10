import os
import json

from core.config import Config


class Chest:
    """A chest placed on a tile. Blocks movement, animates idle until opened,
    then plays opening animation once. Loot is resolved by the engine.
    """

    # Class-level cache of loaded chest definitions {name: data}
    _definitions = {}

    def __init__(self, q, r, chest_type="brown_chest"):
        self.q = q
        self.r = r
        self.chest_type = chest_type

        data = Chest._load_definition(chest_type)
        self.data = data
        self.animations = data.get("animations", {})

        self.anim_state = "idle"
        self.texture = self.animations.get("idle", {}).get("texture")
        self.anim_row = self.animations.get("idle", {}).get("row", 0)
        self.anim_tick = 0
        self.anim_progress = 0.0
        self.anim_speed = 0.15  # frames per update tick

        self.opened = False
        self.open_complete = False  # True once opening animation finished
        # How many anim ticks to wait after the opening animation ends
        # before the chest should be removed from the world.
        # The main loop calls update_animation every ~50ms, so 20 ticks ~= 1s.
        self.despawn_delay_ticks = 7
        self._despawn_counter = 0
        # engine deciding if the chest should be removed after opening
        self.remove_after_open = False

    @classmethod
    def _load_definition(cls, chest_type):
        if chest_type in cls._definitions:
            return cls._definitions[chest_type]
        path = os.path.join(Config.DIRS["chest"], f"{chest_type}.json")
        with open(path, "r") as f:
            data = json.load(f)
        cls._definitions[chest_type] = data
        return data

    def open(self):
        """Start the opening animation. Returns True if the chest actually
        transitioned from closed to opening (so the engine can award loot)."""
        if self.opened:
            return False
        self.opened = True
        self.anim_state = "opening"
        self.anim_row = self.animations.get("opening", {}).get("row", 1)
        self.anim_tick = 0
        self.anim_progress = 0.0
        return True

    def update_animation(self, asset_manager):
        anim_cfg = self.animations.get(self.anim_state)
        if not anim_cfg:
            return
        count = anim_cfg.get("count", 1)

        self.anim_progress += self.anim_speed
        self.anim_tick = int(self.anim_progress)

        if self.anim_state == "idle":
            # loop forever
            if self.anim_tick >= count:
                self.anim_tick = 0
                self.anim_progress = 0.0
        elif self.anim_state == "opening":
            # play once, then hold the last frame
            if self.anim_tick >= count:
                self.anim_tick = count - 1
                self.anim_progress = float(count - 1)
                self.open_complete = True

            # Once the opening animation has finished, count down and
            # flag the chest for removal.
            if self.open_complete and not self.remove_after_open:
                self._despawn_counter += 1
                if self._despawn_counter >= self.despawn_delay_ticks:
                    self.remove_after_open = True
