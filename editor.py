import tkinter as tk
from tkinter import ttk, filedialog, messagebox, Canvas, simpledialog
import sqlite3
import shutil
import os
import json
import math
from PIL import Image, ImageTk


class Config:
    GAME_SCALE = 3
    BASE_HEX_RADIUS = 16
    HEX_SIZE = BASE_HEX_RADIUS * GAME_SCALE  # 48 pixels
    HEX_ASPECT_RATIO = 0.87
    CALIB_OFFSET_Y = 16 * GAME_SCALE
    GRID_RANGE = 20
    MAP_WIDTH = 1400
    MAP_HEIGHT = 900
    CENTER_X = MAP_WIDTH // 2
    CENTER_Y = MAP_HEIGHT // 2
    ASSET_DIR = "assets"
    DIRS = {
        "tile": "assets/definitions/tiles",
        "prop": "assets/definitions/props",
        "monster": "assets/definitions/monsters",
        "player": "assets/definitions/player",
    }


for d in Config.DIRS.values():
    os.makedirs(d, exist_ok=True)
if not os.path.exists(Config.ASSET_DIR):
    os.makedirs(Config.ASSET_DIR)


class HexEngine:
    @staticmethod
    def hex_to_pixel(q, r):
        size = Config.HEX_SIZE
        x = size * (3 / 2 * q)
        y = size * math.sqrt(3) * (r + q / 2)
        return x, y * Config.HEX_ASPECT_RATIO

    @staticmethod
    def pixel_to_hex(px, py):
        x = px
        y = py / Config.HEX_ASPECT_RATIO
        size = Config.HEX_SIZE
        q = (2.0 / 3 * x) / size
        r = (-1.0 / 3 * x + math.sqrt(3) / 3 * y) / size
        return HexEngine.cube_round(q, r, -q - r)

    @staticmethod
    def cube_round(frac_q, frac_r, frac_s):
        q, r, s = round(frac_q), round(frac_r), round(frac_s)
        q_diff, r_diff, s_diff = abs(q - frac_q), abs(r - frac_r), abs(s - frac_s)
        if q_diff > r_diff and q_diff > s_diff:
            q = -r - s
        elif r_diff > s_diff:
            r = -q - s
        else:
            s = -q - r
        return int(q), int(r)

    @staticmethod
    def get_hex_polygon(cx, cy):
        points = []
        for i in range(6):
            angle_rad = math.radians(60 * i)
            vx = Config.HEX_SIZE * math.cos(angle_rad)
            vy = Config.HEX_SIZE * math.sin(angle_rad)
            points.append(cx + vx)
            points.append(cy + (vy * Config.HEX_ASPECT_RATIO))
        return points


class DatabaseManager:
    def __init__(self, db_file="game_data.db"):
        self.conn = sqlite3.connect(db_file)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._init_schema()

    def _init_schema(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS map_tiles (
                q INTEGER, r INTEGER,
                tile_type TEXT, texture_file TEXT,
                prop_texture_file TEXT, prop_scale REAL DEFAULT 1.0, prop_y_shift INTEGER DEFAULT 0,
                is_spawn BOOLEAN DEFAULT 0,
                PRIMARY KEY (q, r)
            )
        """
        )
        try:
            self.cursor.execute(
                "ALTER TABLE map_tiles ADD COLUMN is_spawn BOOLEAN DEFAULT 0"
            )
        except sqlite3.OperationalError:
            pass  # Column likely exists
        self.conn.commit()

    def get_tile(self, q, r):
        self.cursor.execute("SELECT * FROM map_tiles WHERE q=? AND r=?", (q, r))
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def get_all_tiles(self):
        self.cursor.execute("SELECT * FROM map_tiles")
        return [dict(row) for row in self.cursor.fetchall()]

    def clear_spawn_points(self):
        self.cursor.execute("UPDATE map_tiles SET is_spawn = 0")
        self.conn.commit()

    def save_tile(self, data):
        if data.get("is_spawn"):
            self.clear_spawn_points()

        self.cursor.execute(
            """
            INSERT INTO map_tiles (q, r, tile_type, texture_file, prop_texture_file, prop_scale, prop_y_shift, is_spawn)
            VALUES (:q, :r, :tile_type, :texture_file, :prop_texture_file, :prop_scale, :prop_y_shift, :is_spawn)
            ON CONFLICT(q,r) DO UPDATE SET
                tile_type=excluded.tile_type, texture_file=excluded.texture_file,
                prop_texture_file=excluded.prop_texture_file, 
                prop_scale=excluded.prop_scale, prop_y_shift=excluded.prop_y_shift,
                is_spawn=excluded.is_spawn
        """,
            data,
        )
        self.conn.commit()

    def delete_tile(self, q, r):
        self.cursor.execute("DELETE FROM map_tiles WHERE q=? AND r=?", (q, r))
        self.conn.commit()


class AssetManager:
    def __init__(self):
        self.image_cache = {}
        self.texture_layout_map = {}
        self.refresh_layouts()

    def refresh_layouts(self):
        self.texture_layout_map = {}
        for category in ["tile", "prop"]:
            folder = Config.DIRS.get(category)
            if not os.path.exists(folder):
                continue
            for fname in os.listdir(folder):
                if not fname.endswith(".json"):
                    continue
                path = os.path.join(folder, fname)
                try:
                    with open(path, "r") as f:
                        data = json.load(f)
                        tex = data.get("texture_file")
                        if not tex and "animations" in data:
                            tex = data["animations"].get("idle", {}).get("texture")
                        if tex:
                            s = data.get("prop_scale") or data.get("scale", 1.0)
                            y = data.get("prop_y_shift") or data.get("y_shift", 0)
                            self.texture_layout_map[tex] = (float(s), int(y))
                except Exception as e:
                    print(f"Error reading {fname}: {e}")

    def get_asset_layout(self, texture_file):
        if not texture_file:
            return 1.0, 0
        if texture_file in self.texture_layout_map:
            return self.texture_layout_map[texture_file]
        return 1.0, 0

    def get_tk_image(self, filename, scale=1.0):
        if not filename:
            return None
        path = os.path.join(Config.ASSET_DIR, filename)
        if not os.path.exists(path):
            return None
        target_w = max(1, int(Config.HEX_SIZE * scale))
        key = (path, target_w)
        if key in self.image_cache:
            return self.image_cache[key]
        try:
            pil = Image.open(path)
            w_pct = target_w / float(pil.size[0])
            h_size = int((float(pil.size[1]) * float(w_pct)))
            pil = pil.resize((target_w, h_size), Image.Resampling.NEAREST)
            tk_img = ImageTk.PhotoImage(pil)
            self.image_cache[key] = tk_img
            return tk_img
        except Exception as e:
            return None

    def get_anim_frame(self, filename, frame_index, fw, fh, count, scale=1.0):
        """
        Extracts a specific frame from a sprite sheet.
        """
        if not filename:
            return None
        path = os.path.join(Config.ASSET_DIR, filename)
        if not os.path.exists(path):
            return None

        try:
            pil = Image.open(path)
            safe_idx = frame_index % max(1, count)
            x = safe_idx * fw
            y = 0
            if x + fw > pil.width:
                x = 0

            crop = pil.crop((x, y, x + fw, y + fh))
            target_w = int(fw * scale)
            target_h = int(fh * scale)
            crop = crop.resize((target_w, target_h), Image.Resampling.NEAREST)

            return ImageTk.PhotoImage(crop)
        except Exception as e:
            print(f"Anim Error: {e}")
            return None

    def load_json(self, category, name):
        folder = Config.DIRS.get(category)
        path = os.path.join(folder, name)
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
        return {}

    def save_json(self, category, name, data):
        folder = Config.DIRS.get(category)
        if not name.endswith(".json"):
            name += ".json"
        path = os.path.join(folder, name)
        with open(path, "w") as f:
            json.dump(data, f, indent=4)
        self.refresh_layouts()
        return path

    def list_assets(self, category):
        folder = Config.DIRS.get(category)
        if not os.path.exists(folder):
            return []
        return sorted([f for f in os.listdir(folder) if f.endswith(".json")])


class Renderer:
    def __init__(self, asset_mgr):
        self.am = asset_mgr

    def render_hex_at_pixel(self, canvas, cx, cy, tile_data, selected=False):
        poly = HexEngine.get_hex_polygon(cx, cy)
        fill = ""
        t_type = tile_data.get("tile_type")
        if t_type == "water":
            fill = "#283b45"
        elif t_type == "stone":
            fill = "#383838"
        elif t_type == "grass":
            fill = "#2e3b28"

        if fill:
            canvas.create_polygon(poly, fill=fill, outline="", tags="hex_fill")
        tex = tile_data.get("texture_file")
        if tex:
            t_scale = tile_data.get("tile_scale")
            t_shift = tile_data.get("tile_y_shift")
            if t_scale is None:
                t_scale, t_shift = self.am.get_asset_layout(tex)
            img = self.am.get_tk_image(tex, scale=t_scale)
            if img:
                canvas.create_image(
                    cx, cy - Config.CALIB_OFFSET_Y - t_shift, image=img, tags="hex_art"
                )
        p_tex = tile_data.get("prop_texture_file")
        if p_tex:
            p_scale = tile_data.get("prop_scale", 1.0)
            p_shift = tile_data.get("prop_y_shift", 0)
            img = self.am.get_tk_image(p_tex, scale=p_scale)
            if img:
                canvas.create_image(
                    cx, cy - Config.CALIB_OFFSET_Y - p_shift, image=img, tags="hex_prop"
                )
        outline = "red" if selected else "#555"
        width = 2 if selected else 1
        if tile_data.get("is_spawn"):
            canvas.create_oval(
                cx - 5, cy - 5, cx + 5, cy + 5, fill="#00FF00", outline="black"
            )
            outline = "#00FF00"
            width = 3

        canvas.create_polygon(
            poly, fill="", outline=outline, width=width, tags="hex_grid"
        )


class MapTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.selected_q = 0
        self.selected_r = 0
        self.var_paint_mode = tk.BooleanVar(value=False)

        self._setup_ui()
        self._bind_events()

    def _setup_ui(self):
        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(fill="both", expand=True)

        c_frame = ttk.Frame(self.paned)
        self.paned.add(c_frame, weight=3)

        self.canvas = Canvas(
            c_frame,
            bg="#202020",
            scrollregion=(0, 0, Config.MAP_WIDTH, Config.MAP_HEIGHT),
        )
        vbar = ttk.Scrollbar(c_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        hbar = ttk.Scrollbar(c_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=vbar.set, xscrollcommand=hbar.set)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)
        hbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill="both", expand=True)

        self.inspector = ttk.Frame(self.paned, padding=10)
        self.paned.add(self.inspector, weight=1)
        paint_frame = ttk.LabelFrame(self.inspector, text="Editor Mode", padding=5)
        paint_frame.pack(fill="x", pady=(0, 10))
        ttk.Checkbutton(
            paint_frame, text="PAINT MODE (On/Off)", variable=self.var_paint_mode
        ).pack()
        self.var_q = tk.StringVar(value="0")
        self.var_r = tk.StringVar(value="0")
        self.var_tile = tk.StringVar()
        self.var_prop = tk.StringVar()
        self.var_prop_scale = tk.DoubleVar(value=1.0)
        self.var_prop_shift = tk.IntVar(value=0)
        self.var_is_spawn = tk.BooleanVar(value=False)

        ttk.Label(self.inspector, text="Coordinates", font=("Bold", 10)).pack(
            anchor="w"
        )
        ttk.Label(self.inspector, textvariable=self.var_q).pack()
        ttk.Label(self.inspector, textvariable=self.var_r).pack()

        ttk.Separator(self.inspector).pack(fill="x", pady=10)
        ttk.Checkbutton(
            self.inspector,
            text="Is World Spawn Point?",
            variable=self.var_is_spawn,
            command=self._auto_save,
        ).pack(anchor="w", pady=5)

        ttk.Separator(self.inspector).pack(fill="x", pady=10)

        ttk.Label(self.inspector, text="Terrain (Base)", font=("Bold", 10)).pack(
            anchor="w"
        )
        self.cb_tiles = ttk.Combobox(self.inspector, state="readonly")
        self.cb_tiles.pack(fill="x")
        self.cb_tiles.bind("<<ComboboxSelected>>", self._on_tile_preset_select)
        ttk.Entry(self.inspector, textvariable=self.var_tile).pack(
            fill="x", pady=(5, 0)
        )
        ttk.Button(
            self.inspector,
            text="Browse...",
            command=lambda: self._browse(self.var_tile),
        ).pack(fill="x")

        ttk.Separator(self.inspector).pack(fill="x", pady=10)

        ttk.Label(self.inspector, text="Prop (Overlay)", font=("Bold", 10)).pack(
            anchor="w"
        )
        self.cb_props = ttk.Combobox(self.inspector, state="readonly")
        self.cb_props.pack(fill="x")
        self.cb_props.bind("<<ComboboxSelected>>", self._on_prop_preset_select)
        ttk.Entry(self.inspector, textvariable=self.var_prop).pack(
            fill="x", pady=(5, 0)
        )

        ttk.Label(self.inspector, text="Scale:").pack(anchor="w")
        ttk.Scale(
            self.inspector,
            from_=0.1,
            to=3.0,
            variable=self.var_prop_scale,
            command=lambda x: self._auto_save(),
        ).pack(fill="x")
        ttk.Label(self.inspector, text="Y-Shift:").pack(anchor="w")
        ttk.Scale(
            self.inspector,
            from_=-50,
            to=100,
            variable=self.var_prop_shift,
            command=lambda x: self._auto_save(),
        ).pack(fill="x")

        ttk.Button(self.inspector, text="Clear Prop", command=self._clear_prop).pack(
            fill="x", pady=5
        )
        ttk.Separator(self.inspector).pack(fill="x", pady=20)
        ttk.Button(self.inspector, text="DELETE TILE", command=self._delete_tile).pack(
            fill="x"
        )

    def _bind_events(self):
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_click)

    def refresh_libraries(self):
        self.cb_tiles["values"] = self.app.asset_mgr.list_assets("tile")
        self.cb_props["values"] = self.app.asset_mgr.list_assets("prop")

    def render(self):
        self.canvas.delete("all")
        db_tiles = {(t["q"], t["r"]): t for t in self.app.db.get_all_tiles()}
        cx, cy = Config.CENTER_X, Config.CENTER_Y
        r_range = Config.GRID_RANGE

        render_list = []
        for q in range(-r_range, r_range + 1):
            for r_idx in range(-r_range, r_range + 1):
                if abs(q + r_idx) > r_range:
                    continue
                px, py = HexEngine.hex_to_pixel(q, r_idx)
                draw_x, draw_y = cx + px, cy + py
                if not (
                    0 < draw_x < Config.MAP_WIDTH and 0 < draw_y < Config.MAP_HEIGHT
                ):
                    continue
                tile_data = db_tiles.get((q, r_idx), {})
                render_list.append((q, r_idx, draw_x, draw_y, tile_data))

        render_list.sort(key=lambda x: x[3])
        for q, r_idx, x, y, data in render_list:
            is_selected = q == self.selected_q and r_idx == self.selected_r
            self.app.renderer.render_hex_at_pixel(self.canvas, x, y, data, is_selected)

    def _on_click(self, event):
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        q, r = HexEngine.pixel_to_hex(cx - Config.CENTER_X, cy - Config.CENTER_Y)

        if q != self.selected_q or r != self.selected_r:
            self.selected_q = q
            self.selected_r = r
            self.var_q.set(str(q))
            self.var_r.set(str(r))

            if self.var_paint_mode.get():
                self._save_from_inspector()
            else:
                existing = self.app.db.get_tile(q, r)
                if existing:
                    self._load_into_inspector(existing)
                else:
                    self.var_is_spawn.set(False)

            self.render()

    def _load_into_inspector(self, data):
        self.var_tile.set(data.get("texture_file", ""))
        self.var_prop.set(data.get("prop_texture_file", ""))
        self.var_prop_scale.set(data.get("prop_scale", 1.0))
        self.var_prop_shift.set(data.get("prop_y_shift", 0))
        self.var_is_spawn.set(bool(data.get("is_spawn", 0)))

    def _save_from_inspector(self):
        data = {
            "q": self.selected_q,
            "r": self.selected_r,
            "tile_type": "grass",
            "texture_file": self.var_tile.get(),
            "prop_texture_file": self.var_prop.get(),
            "prop_scale": self.var_prop_scale.get(),
            "prop_y_shift": self.var_prop_shift.get(),
            "is_spawn": self.var_is_spawn.get(),
        }
        self.app.db.save_tile(data)

    def _auto_save(self):
        self._save_from_inspector()
        self.render()

    def _browse(self, var):
        f = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg")])
        if f:
            base = os.path.basename(f)
            dest = os.path.join(Config.ASSET_DIR, base)
            if not os.path.exists(dest):
                shutil.copy(f, dest)
            var.set(base)
            self._save_from_inspector()
            self.render()

    def _on_tile_preset_select(self, event):
        fname = self.cb_tiles.get()
        data = self.app.asset_mgr.load_json("tile", fname)
        self.var_tile.set(data.get("texture_file", ""))
        self._save_from_inspector()
        self.render()

    def _on_prop_preset_select(self, event):
        fname = self.cb_props.get()
        data = self.app.asset_mgr.load_json("prop", fname)
        self.var_prop.set(data.get("texture_file", ""))
        self.var_prop_scale.set(data.get("prop_scale", 1.0))
        self.var_prop_shift.set(data.get("prop_y_shift", 0))
        self._save_from_inspector()
        self.render()

    def _clear_prop(self):
        self.var_prop.set("")
        self._save_from_inspector()
        self.render()

    def _delete_tile(self):
        self.app.db.delete_tile(self.selected_q, self.selected_r)
        self.render()


class LibraryTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.anim_running = False
        self.current_frame = 0
        self.anim_timer = None
        self.anim_data = {}  # Holds the data being edited

        self._setup_ui()

    def _setup_ui(self):
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill="both", expand=True)
        self.ctrl = ttk.Frame(paned, padding=10)
        paned.add(self.ctrl, weight=1)

        ttk.Label(self.ctrl, text="Asset Management", font=("Bold", 12)).pack(pady=10)
        self.var_cat = tk.StringVar(value="prop")
        f_cat = ttk.Frame(self.ctrl)
        f_cat.pack(fill="x", pady=5)
        for c in ["tile", "prop", "monster", "player"]:
            ttk.Radiobutton(
                f_cat,
                text=c.capitalize(),
                variable=self.var_cat,
                value=c,
                command=self._on_category_change,
            ).pack(side=tk.LEFT)
        ttk.Label(self.ctrl, text="Load / Create File:", font=("Bold", 10)).pack(
            anchor="w", pady=(15, 0)
        )
        self.cb_files = ttk.Combobox(self.ctrl)
        self.cb_files.pack(fill="x")
        self.cb_files.bind("<<ComboboxSelected>>", self._load_file)
        self.prop_frame = ttk.LabelFrame(self.ctrl, text="Properties", padding=5)
        self.prop_frame.pack(fill="both", expand=True, pady=10)
        ttk.Button(self.ctrl, text="SAVE ASSET", command=self._save_asset).pack(
            fill="x", pady=20
        )
        self.prev_frame = ttk.Frame(paned, padding=10)
        paned.add(self.prev_frame, weight=2)

        ttk.Label(self.prev_frame, text="Live Preview", font=("Bold", 12)).pack()
        self.canvas = Canvas(self.prev_frame, bg="#303030")
        self.canvas.pack(fill="both", expand=True)
        self._build_prop_ui()
        self._refresh_list()

    def _on_category_change(self):
        self._stop_anim()
        cat = self.var_cat.get()
        if cat in ["monster", "player"]:
            self._build_anim_ui()
        else:
            self._build_prop_ui()
        self._refresh_list()

    def _build_prop_ui(self):
        for widget in self.prop_frame.winfo_children():
            widget.destroy()

        self.var_tex = tk.StringVar()
        self.var_scale = tk.DoubleVar(value=1.0)
        self.var_shift = tk.IntVar(value=0)

        for v in [self.var_tex, self.var_scale, self.var_shift]:
            v.trace_add("write", lambda *a: self._update_preview_static())

        ttk.Label(self.prop_frame, text="Texture:").pack(anchor="w")
        h = ttk.Frame(self.prop_frame)
        h.pack(fill="x")
        ttk.Entry(h, textvariable=self.var_tex).pack(
            side=tk.LEFT, fill="x", expand=True
        )
        ttk.Button(
            h, text="...", width=3, command=lambda: self._browse(self.var_tex)
        ).pack(side=tk.LEFT)

        ttk.Label(self.prop_frame, text="Scale:").pack(anchor="w", pady=(5, 0))
        ttk.Scale(self.prop_frame, from_=0.1, to=3.0, variable=self.var_scale).pack(
            fill="x"
        )

        ttk.Label(self.prop_frame, text="Y-Shift:").pack(anchor="w", pady=(5, 0))
        ttk.Scale(self.prop_frame, from_=-50, to=100, variable=self.var_shift).pack(
            fill="x"
        )

    def _build_anim_ui(self):
        for widget in self.prop_frame.winfo_children():
            widget.destroy()
        self.var_scale = tk.DoubleVar(value=1.0)
        self.var_shift = tk.IntVar(value=0)
        ttk.Label(self.prop_frame, text="Animations:", font=("Bold", 9)).pack(
            anchor="w"
        )

        list_frame = ttk.Frame(self.prop_frame)
        list_frame.pack(fill="x", pady=5)

        self.lb_anims = tk.Listbox(list_frame, height=4)
        self.lb_anims.pack(side=tk.LEFT, fill="x", expand=True)
        self.lb_anims.bind("<<ListboxSelect>>", self._on_anim_select)

        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(side=tk.LEFT, fill="y")
        ttk.Button(btn_frame, text="+", width=3, command=self._add_anim).pack()
        ttk.Button(btn_frame, text="-", width=3, command=self._del_anim).pack()

        ttk.Separator(self.prop_frame).pack(fill="x", pady=5)
        self.var_anim_tex = tk.StringVar()
        self.var_anim_fw = tk.IntVar(value=32)  # Weight/Width
        self.var_anim_fh = tk.IntVar(value=32)  # Height
        self.var_anim_count = tk.IntVar(value=1)
        for v in [
            self.var_anim_tex,
            self.var_anim_fw,
            self.var_anim_fh,
            self.var_anim_count,
            self.var_scale,
            self.var_shift,
        ]:
            v.trace_add("write", lambda *a: self._on_anim_data_change())

        ttk.Label(self.prop_frame, text="Sprite Sheet:").pack(anchor="w")
        h = ttk.Frame(self.prop_frame)
        h.pack(fill="x")
        ttk.Entry(h, textvariable=self.var_anim_tex).pack(
            side=tk.LEFT, fill="x", expand=True
        )
        ttk.Button(
            h, text="...", width=3, command=lambda: self._browse(self.var_anim_tex)
        ).pack(side=tk.LEFT)

        grid = ttk.Frame(self.prop_frame)
        grid.pack(fill="x", pady=5)

        ttk.Label(grid, text="Frame Width:").grid(row=0, column=0, sticky="w")
        ttk.Entry(grid, textvariable=self.var_anim_fw, width=5).grid(row=0, column=1)

        ttk.Label(grid, text="Frame Height:").grid(row=1, column=0, sticky="w")
        ttk.Entry(grid, textvariable=self.var_anim_fh, width=5).grid(row=1, column=1)

        ttk.Label(grid, text="Image Count:").grid(row=2, column=0, sticky="w")
        ttk.Entry(grid, textvariable=self.var_anim_count, width=5).grid(row=2, column=1)

        ttk.Separator(self.prop_frame).pack(fill="x", pady=5)

        ttk.Label(self.prop_frame, text="Global Scale:").pack(anchor="w")
        ttk.Scale(self.prop_frame, from_=0.1, to=3.0, variable=self.var_scale).pack(
            fill="x"
        )

        ttk.Label(self.prop_frame, text="Global Y-Shift:").pack(anchor="w")
        ttk.Scale(self.prop_frame, from_=-50, to=100, variable=self.var_shift).pack(
            fill="x"
        )

    def _refresh_list(self):
        self.cb_files["values"] = self.app.asset_mgr.list_assets(self.var_cat.get())
        self.cb_files.set("")
        self.canvas.delete("all")

    def _load_file(self, event=None):
        name = self.cb_files.get()
        if not name:
            return
        data = self.app.asset_mgr.load_json(self.var_cat.get(), name)

        if self.var_cat.get() in ["monster", "player"]:
            self.anim_data = data
            self.var_scale.set(data.get("scale", 1.0))
            self.var_shift.set(data.get("y_shift", 0))
            self.lb_anims.delete(0, tk.END)
            anims = data.get("animations", {})
            for k in anims.keys():
                self.lb_anims.insert(tk.END, k)
            if "idle" in anims:
                idx = self.lb_anims.get(0, tk.END).index("idle")
                self.lb_anims.selection_set(idx)
                self._on_anim_select(None)
            elif anims:
                self.lb_anims.selection_set(0)
                self._on_anim_select(None)

            self._start_anim_loop()

        else:
            self.var_tex.set(data.get("texture_file", ""))
            self.var_scale.set(data.get("prop_scale", 1.0))
            self.var_shift.set(data.get("prop_y_shift", 0))
            self._update_preview_static()

    def _add_anim(self):
        name = simpledialog.askstring(
            "New Animation", "Enter animation name (e.g., 'attack'):"
        )
        if name:
            if "animations" not in self.anim_data:
                self.anim_data["animations"] = {}
            self.anim_data["animations"][name] = {
                "texture": "",
                "fw": 32,
                "fh": 32,
                "count": 1,
            }
            self.lb_anims.insert(tk.END, name)

    def _del_anim(self):
        sel = self.lb_anims.curselection()
        if not sel:
            return
        key = self.lb_anims.get(sel[0])
        if key in self.anim_data.get("animations", {}):
            del self.anim_data["animations"][key]
            self.lb_anims.delete(sel[0])

    def _on_anim_select(self, event):
        sel = self.lb_anims.curselection()
        if not sel:
            return
        key = self.lb_anims.get(sel[0])

        anim = self.anim_data.get("animations", {}).get(key, {})
        self.var_anim_tex.set(anim.get("texture", ""))
        self.var_anim_fw.set(anim.get("fw", 32))
        self.var_anim_fh.set(anim.get("fh", 32))
        self.var_anim_count.set(anim.get("count", 1))

    def _on_anim_data_change(self):
        sel = self.lb_anims.curselection()
        if not sel:
            return
        key = self.lb_anims.get(sel[0])

        if "animations" not in self.anim_data:
            self.anim_data["animations"] = {}

        self.anim_data["scale"] = self.var_scale.get()
        self.anim_data["y_shift"] = self.var_shift.get()

        self.anim_data["animations"][key] = {
            "texture": self.var_anim_tex.get(),
            "fw": self.var_anim_fw.get(),
            "fh": self.var_anim_fh.get(),
            "count": self.var_anim_count.get(),
        }

    def _browse(self, var):
        f = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg")])
        if f:
            base = os.path.basename(f)
            dest = os.path.join(Config.ASSET_DIR, base)
            if not os.path.exists(dest):
                shutil.copy(f, dest)
            var.set(base)

    def _update_preview_static(self):
        self.canvas.delete("all")
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        cx, cy = (w // 2, h // 2) if w > 1 else (200, 200)

        preview_data = {
            "texture_file": "dirt.png",  # Dummy base
            "prop_texture_file": self.var_tex.get(),
            "prop_scale": self.var_scale.get(),
            "prop_y_shift": self.var_shift.get(),
        }

        if self.var_cat.get() == "tile":
            preview_data["texture_file"] = self.var_tex.get()
            preview_data["tile_scale"] = self.var_scale.get()
            preview_data["tile_y_shift"] = self.var_shift.get()
            preview_data["prop_texture_file"] = None

        self.app.renderer.render_hex_at_pixel(
            self.canvas, cx, cy, preview_data, selected=True
        )

    def _stop_anim(self):
        if self.anim_timer:
            self.after_cancel(self.anim_timer)
            self.anim_timer = None
        self.anim_running = False

    def _start_anim_loop(self):
        self._stop_anim()
        self.anim_running = True
        self.current_frame = 0
        self._anim_loop()

    def _anim_loop(self):
        if not self.anim_running:
            return
        self.canvas.delete("all")
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        cx, cy = (w // 2, h // 2) if w > 1 else (200, 200)

        poly = HexEngine.get_hex_polygon(cx, cy)
        self.canvas.create_polygon(poly, fill="#2e3b28", outline="#555", width=2)
        sel = self.lb_anims.curselection()
        if sel:
            key = self.lb_anims.get(sel[0])
            anim = self.anim_data.get("animations", {}).get(key)
            if anim:
                tex = anim.get("texture")
                fw = anim.get("fw", 32)
                fh = anim.get("fh", 32)
                count = anim.get("count", 1)
                scale = self.var_scale.get()
                shift = self.var_shift.get()
                img = self.app.asset_mgr.get_anim_frame(
                    tex, self.current_frame, fw, fh, count, scale
                )
                if img:
                    self.canvas.create_image(
                        cx, cy - Config.CALIB_OFFSET_Y - shift, image=img
                    )
                    self.canvas.image = img  # Keep ref
        self.current_frame += 1
        self.anim_timer = self.after(150, self._anim_loop)  # 150ms per frame

    def _save_asset(self):
        name = self.cb_files.get()
        if not name:
            return
        cat = self.var_cat.get()

        if cat in ["monster", "player"]:
            self.anim_data["category"] = cat
            self.anim_data["name"] = name
            data = self.anim_data
        else:
            data = {
                "category": cat,
                "texture_file": self.var_tex.get(),
                "prop_scale": self.var_scale.get(),
                "prop_y_shift": self.var_shift.get(),
            }

        self.app.asset_mgr.save_json(cat, name, data)
        messagebox.showinfo("Success", f"Saved {name}.json")
        self._refresh_list()
        self.app.map_tab.refresh_libraries()


class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hex Architect - Animation & Spawn Support")
        self.root.geometry("1400x900")
        self.db = DatabaseManager()
        self.asset_mgr = AssetManager()
        self.renderer = Renderer(self.asset_mgr)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)
        self.map_tab = MapTab(self.notebook, self)
        self.lib_tab = LibraryTab(self.notebook, self)
        self.notebook.add(self.map_tab, text="Map Designer")
        self.notebook.add(self.lib_tab, text="Asset Library")
        self.map_tab.refresh_libraries()
        self.map_tab.render()


if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    style.theme_use("clam")
    app = MainApp(root)
    root.mainloop()
