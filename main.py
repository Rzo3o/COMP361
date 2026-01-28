import tkinter as tk
from tkinter import messagebox, Canvas
import os
import json
from PIL import Image, ImageTk

from hexmath import Config, HexMath
from GameDB import GameDB
from engine import GameEngine


class AssetManager:
    """Asset manager that syncs with Editor JSON definitions"""

    def __init__(self):
        self.cache = {}
        self.layouts = {}  # Map: texture_filename -> (scale, y_shift)
        self.anim_metadata = {}  # Map: texture_filename -> {fw, fh, count}
        self._load_layouts()

    def _load_layouts(self):
        """Scans definition files to ensure Game renders exactly like Editor."""
        search_dirs = [
            "assets/definitions/tiles",
            "assets/definitions/props",
            "assets/definitions/monsters",
            "assets/definitions/player",
        ]

        for d in search_dirs:
            if not os.path.exists(d):
                continue

            for f in os.listdir(d):
                if f.endswith(".json"):
                    try:
                        with open(os.path.join(d, f), "r") as jf:
                            data = json.load(jf)
                            if "animations" in data:
                                for anim_name, anim_data in data["animations"].items():
                                    tex = anim_data.get("texture")
                                    if tex:
                                        self.anim_metadata[tex] = {
                                            "fw": anim_data.get("fw", 32),
                                            "fh": anim_data.get("fh", 32),
                                            "count": anim_data.get("count", 1),
                                            "scale": data.get("scale", 1.0),
                                            "y_shift": data.get("y_shift", 0),
                                        }
                                        self.layouts[tex] = (
                                            float(data.get("scale", 1.0)),
                                            int(data.get("y_shift", 0)),
                                        )
                            tex = data.get("texture_file")
                            if not tex and "animations" in data:
                                tex = data["animations"].get("idle", {}).get("texture")

                            if tex:
                                s = data.get("prop_scale") or data.get("scale", 1.0)
                                y = data.get("prop_y_shift") or data.get("y_shift", 0)
                                self.layouts[tex] = (float(s), int(y))
                    except Exception as e:
                        print(f"Error loading layout {f}: {e}")

    def get_layout(self, filename):
        """Returns (scale, y_shift) for a given texture file."""
        return self.layouts.get(filename, (1.0, 0))

    def get_anim_frame(self, filename, frame_index=0):
        """Extracts and scales a specific frame from a sprite sheet."""
        if not filename or filename not in self.anim_metadata:
            return self.get_image(filename)  # Fallback to static

        meta = self.anim_metadata[filename]
        path = os.path.join("assets", filename)
        key = (filename, frame_index, "anim")
        if key in self.cache:
            return self.cache[key]

        if not os.path.exists(path):
            return None

        try:
            pil = Image.open(path)
            fw = meta["fw"]
            fh = meta["fh"]
            count = meta["count"]
            scale = meta["scale"]
            safe_idx = frame_index % max(1, count)
            x = safe_idx * fw
            y = 0
            if x + fw > pil.width:
                x = 0
            crop = pil.crop((x, y, x + fw, y + fh))
            target_w = int(fw * scale)
            target_h = int(fh * scale)
            crop = crop.resize((target_w, target_h), Image.Resampling.NEAREST)

            tk_img = ImageTk.PhotoImage(crop)
            self.cache[key] = tk_img
            return tk_img
        except Exception as e:
            print(f"Anim Error {filename}: {e}")
            return None

    def get_image(self, filename, scale=1.0):
        if not filename:
            return None
        if filename in self.anim_metadata:
            return self.get_anim_frame(filename, 0)

        path = os.path.join("assets", filename)
        key = (filename, scale)
        if key in self.cache:
            return self.cache[key]

        if not os.path.exists(path):
            return None

        try:
            pil = Image.open(path)
            target_w = max(1, int(Config.HEX_SIZE * scale))

            w, h = pil.size
            ratio = target_w / w
            target_h = int(h * ratio)

            pil = pil.resize((target_w, target_h), Image.Resampling.NEAREST)
            tk_img = ImageTk.PhotoImage(pil)
            self.cache[key] = tk_img
            return tk_img
        except Exception as e:
            print(f"Failed to load {filename}: {e}")
            return None


class GameWindow:
    def __init__(self, root, session_id=1):
        self.root = root
        self.db = GameDB()
        if not self.db.get_session(session_id):
            self.db.create_session(session_id)

        self.engine = GameEngine(self.db, session_id)
        self.assets = AssetManager()
        self.frame_index = 0

        self._setup_ui()
        self._bind_inputs()
        self._game_loop()

    def _setup_ui(self):
        self.root.geometry(f"{Config.WINDOW_WIDTH}x{Config.WINDOW_HEIGHT}")
        self.root.title("Hex RPG")
        self.stats_frame = tk.Frame(self.root, bg="#222", height=40)
        self.stats_frame.pack(fill="x", side="top")

        self.lbl_hp = tk.Label(
            self.stats_frame,
            text="HP: 100",
            fg="#f55",
            bg="#222",
            font=("Arial", 14, "bold"),
        )
        self.lbl_hp.pack(side="left", padx=10)

        self.lbl_hunger = tk.Label(
            self.stats_frame,
            text="Hunger: 100",
            fg="#fa5",
            bg="#222",
            font=("Arial", 14, "bold"),
        )
        self.lbl_hunger.pack(side="left", padx=10)

        self.lbl_loc = tk.Label(
            self.stats_frame, text="Q:0 R:0", fg="#fff", bg="#222", font=("Arial", 14)
        )
        self.lbl_loc.pack(side="right", padx=10)
        self.canvas = Canvas(self.root, bg="#111")
        self.canvas.pack(fill="both", expand=True)

    def _bind_inputs(self):
        self.root.bind("<w>", lambda e: self.on_input("w"))
        self.root.bind("<s>", lambda e: self.on_input("s"))
        self.root.bind("<a>", lambda e: self.on_input("a"))
        self.root.bind("<d>", lambda e: self.on_input("d"))
        self.root.bind("<q>", lambda e: self.on_input("q"))
        self.root.bind("<e>", lambda e: self.on_input("e"))

    def _game_loop(self):
        """Main Loop for animations."""
        self.frame_index += 1
        self.render()
        self.root.after(150, self._game_loop)

    def on_input(self, key):
        result = self.engine.handle_input(key)
        if result == "GAME_OVER":
            messagebox.showinfo("Dead", "You have perished.")
            self.root.destroy()
        elif result == "TURN_TAKEN":
            self.render()

    def render(self):
        self.canvas.delete("all")

        p = self.engine.world.player
        self.lbl_hp.config(text=f"HP: {p.hp}/{p.max_hp}")
        self.lbl_hunger.config(text=f"Hunger: {p.hunger}/{p.max_hunger}")
        self.lbl_loc.config(text=f"Q:{p.q} R:{p.r}")
        cx = Config.CENTER_X
        cy = Config.CENTER_Y
        render_range = 15
        terrain_layer = []
        object_layer = []

        for q in range(p.q - render_range, p.q + render_range):
            for r in range(p.r - render_range, p.r + render_range):
                tile = self.engine.world.get_tile(q, r)
                if not tile:
                    continue
                px, py = HexMath.hex_to_pixel(q, r)
                ppx, ppy = HexMath.hex_to_pixel(p.q, p.r)

                draw_x = cx + (px - ppx)
                draw_y = cy + (py - ppy)
                if (
                    -100 < draw_x < Config.WINDOW_WIDTH + 100
                    and -100 < draw_y < Config.WINDOW_HEIGHT + 100
                ):
                    terrain_layer.append((tile, draw_x, draw_y))
                    if tile.discovered and tile.prop_texture:
                        object_layer.append(
                            {
                                "depth": draw_y,  # Sort by base Y
                                "type": "prop",
                                "tile": tile,
                                "x": draw_x,
                                "y": draw_y,
                            }
                        )
        object_layer.append(
            {"depth": cy, "type": "entity", "entity": p, "x": cx, "y": cy}
        )
        terrain_layer.sort(key=lambda t: t[2])
        for tile, dx, dy in terrain_layer:
            self._draw_hex_base(tile, dx, dy)
        object_layer.sort(key=lambda obj: obj["depth"])

        for obj in object_layer:
            if obj["type"] == "prop":
                self._draw_prop(obj["tile"], obj["x"], obj["y"])
            elif obj["type"] == "entity":
                self._draw_entity(obj["entity"], obj["x"], obj["y"])

    def _draw_hex_base(self, tile, x, y):
        """Draws the flat hexagon ground only."""
        poly = HexMath.get_hex_polygon(x, y)

        if not tile.discovered:
            self.canvas.create_polygon(poly, fill="#000", outline="#111")
            return
        fill = "#2e3b28"  # grass default
        if tile.type == "water":
            fill = "#283b45"
        elif tile.type == "stone":
            fill = "#383838"

        self.canvas.create_polygon(poly, fill=fill, outline="#222")
        if tile.texture:
            base_scale, base_shift = self.assets.get_layout(tile.texture)

            img = self.assets.get_image(tile.texture, scale=base_scale)
            if img:
                self.canvas.create_image(
                    x, y - Config.CALIB_OFFSET_Y - base_shift, image=img
                )

    def _draw_prop(self, tile, x, y):
        """Draws the prop (tree, rock, etc)."""
        if tile.prop_texture:
            img = self.assets.get_image(tile.prop_texture, scale=tile.prop_scale)
            if img:
                self.canvas.create_image(
                    x, y - Config.CALIB_OFFSET_Y - tile.prop_shift, image=img
                )

    def _draw_entity(self, entity, x, y):
        """Draws dynamic entities."""
        r = 15
        self.canvas.create_oval(
            x - r, y - r - 10, x + r, y + r - 10, fill="red", outline="white", width=2
        )
        if entity.texture:
            img = self.assets.get_anim_frame(entity.texture, self.frame_index)
            scale, shift = self.assets.get_layout(entity.texture)

            if img:
                self.canvas.create_image(
                    x, y - Config.CALIB_OFFSET_Y - shift, image=img
                )


if __name__ == "__main__":
    root = tk.Tk()
    app = GameWindow(root)
    root.mainloop()
