import tkinter as tk
from tkinter import ttk, filedialog, messagebox, Canvas
import sqlite3
import shutil
import os
import json
import math
from PIL import Image, ImageTk

# ==========================================
# 1. CONSTANTS
# ==========================================

# --- EDITOR VIEW (Schematic / Abstract) ---
# This is for the "Map Designer" tab.
# Smaller, flatter, easier to see the whole map.
EDITOR_HEX_SIZE = 30
GRID_RANGE = 20
MAP_WIDTH_PIXELS = 1600
MAP_HEIGHT_PIXELS = 1400
OFFSET_X = MAP_WIDTH_PIXELS // 2
OFFSET_Y = MAP_HEIGHT_PIXELS // 2

# --- GAME ENGINE VIEW (Realistic / 1:1) ---
# This is for the "Asset Library" preview.
# Matches game.py exactly.
GAME_SCALE = 3
BASE_HEX_RADIUS = 16
GAME_HEX_SIZE = BASE_HEX_RADIUS * GAME_SCALE  # 48

# Game Calibration
ISO_SQUASH = 0.9280
IMG_SCALE_MODIFIER = 3.010
VERTICAL_OFFSET = -13.5
# ------------------------------------------

DIRS = [
    "assets/definitions/tiles",
    "assets/definitions/props",
    "assets/definitions/items",
    "assets/definitions/monsters",
    "assets",
]
for d in DIRS:
    if not os.path.exists(d):
        os.makedirs(d)


class GameEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Hex Game: World Architect")
        self.root.geometry("1400x900")

        self.conn = sqlite3.connect("game_data.db")
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        try:
            self.cursor.execute(
                "ALTER TABLE map_tiles ADD COLUMN prop_scale REAL DEFAULT 1.0"
            )
            self.cursor.execute(
                "ALTER TABLE map_tiles ADD COLUMN prop_y_shift INTEGER DEFAULT 0"
            )
            self.conn.commit()
        except sqlite3.OperationalError:
            pass

        self.tile_library = {}
        self.prop_library = {}
        self.tk_image_cache = {}
        self.refresh_asset_library()

        style = ttk.Style()
        style.configure("Bold.TLabel", font=("Helvetica", 10, "bold"))

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        self.create_map_designer_tab()
        self.create_asset_library_tab()

    def get_tk_image(self, filename, target_width=None):
        if not filename:
            return None

        path = os.path.join("assets", filename)
        if not os.path.exists(path):
            path = filename
            if not os.path.exists(path):
                return None

        cache_key = (path, target_width)

        if cache_key not in self.tk_image_cache:
            try:
                pil_img = Image.open(path)
                # NEAREST neighbor to keep pixel art crisp
                if target_width:
                    w_percent = target_width / float(pil_img.size[0])
                    h_size = int((float(pil_img.size[1]) * float(w_percent)))
                    pil_img = pil_img.resize(
                        (target_width, h_size), Image.Resampling.NEAREST
                    )

                tk_img = ImageTk.PhotoImage(pil_img)
                self.tk_image_cache[cache_key] = tk_img
            except Exception as e:
                print(f"Error loading image {path}: {e}")
                return None

        return self.tk_image_cache[cache_key]

    def refresh_asset_library(self):
        self.tile_library = {}
        self.prop_library = {}

        path_tiles = "assets/definitions/tiles"
        if os.path.exists(path_tiles):
            for f in os.listdir(path_tiles):
                if f.endswith(".json"):
                    try:
                        with open(os.path.join(path_tiles, f), "r") as file:
                            self.tile_library[f] = json.load(file)
                    except:
                        pass

        path_props = "assets/definitions/props"
        if os.path.exists(path_props):
            for f in os.listdir(path_props):
                if f.endswith(".json"):
                    try:
                        with open(os.path.join(path_props, f), "r") as file:
                            self.prop_library[f] = json.load(file)
                    except:
                        pass

    # ======================================================
    # TAB 1: VISUAL MAP DESIGNER (SCHEMATIC VIEW)
    # ======================================================
    def create_map_designer_tab(self):
        self.map_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.map_frame, text="Map Designer")

        paned = ttk.PanedWindow(self.map_frame, orient=tk.HORIZONTAL)
        paned.pack(fill="both", expand=True)

        canvas_container = ttk.Frame(paned)
        paned.add(canvas_container, weight=3)

        self.v_scroll = ttk.Scrollbar(canvas_container, orient=tk.VERTICAL)
        self.h_scroll = ttk.Scrollbar(canvas_container, orient=tk.HORIZONTAL)
        self.canvas = Canvas(
            canvas_container,
            bg="#202020",
            scrollregion=(0, 0, MAP_WIDTH_PIXELS, MAP_HEIGHT_PIXELS),
            yscrollcommand=self.v_scroll.set,
            xscrollcommand=self.h_scroll.set,
        )

        self.v_scroll.config(command=self.canvas.yview)
        self.h_scroll.config(command=self.canvas.xview)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill="both", expand=True)

        self.root.after(100, self.center_on_origin)
        self.canvas.bind("<Button-1>", self.on_map_click)

        self.inspector = ttk.Frame(paned, padding=10)
        paned.add(self.inspector, weight=1)

        self.sel_q = tk.IntVar()
        self.sel_r = tk.IntVar()
        self.sel_type = tk.StringVar()
        self.sel_name = tk.StringVar()
        self.sel_passable = tk.BooleanVar(value=True)
        self.sel_texture = tk.StringVar()
        self.sel_prop_texture = tk.StringVar()
        self.sel_prop_scale = tk.DoubleVar(value=1.0)
        self.sel_prop_shift = tk.IntVar(value=0)

        # Refresh map when sliders change
        self.sel_prop_scale.trace_add("write", lambda *args: self.draw_grid())
        self.sel_prop_shift.trace_add("write", lambda *args: self.draw_grid())

        ttk.Label(self.inspector, text="Selected Hex", style="Bold.TLabel").pack(
            pady=(0, 10)
        )

        grid_info = ttk.Frame(self.inspector)
        grid_info.pack(fill="x", pady=5)
        ttk.Label(grid_info, text="Q:").pack(side=tk.LEFT)
        ttk.Label(
            grid_info,
            textvariable=self.sel_q,
            font=("Mono", 12, "bold"),
            foreground="blue",
        ).pack(side=tk.LEFT, padx=5)
        ttk.Label(grid_info, text="R:").pack(side=tk.LEFT)
        ttk.Label(
            grid_info,
            textvariable=self.sel_r,
            font=("Mono", 12, "bold"),
            foreground="blue",
        ).pack(side=tk.LEFT, padx=5)

        ttk.Separator(self.inspector, orient="horizontal").pack(fill="x", pady=10)

        ttk.Label(
            self.inspector, text="Terrain (Base Layer)", style="Bold.TLabel"
        ).pack(anchor="w")

        self.tile_combo = ttk.Combobox(self.inspector, state="readonly")
        self.tile_combo.pack(fill="x", pady=(5, 5))
        self.tile_combo.set("Load Terrain Preset...")
        self.tile_combo.bind("<<ComboboxSelected>>", self.apply_tile_preset)

        ttk.Label(self.inspector, text="Type:").pack(anchor="w")
        ttk.Entry(self.inspector, textvariable=self.sel_type).pack(fill="x")
        ttk.Label(self.inspector, text="Location Name:").pack(anchor="w")
        ttk.Entry(self.inspector, textvariable=self.sel_name).pack(fill="x")
        ttk.Checkbutton(
            self.inspector, text="Passable?", variable=self.sel_passable
        ).pack(anchor="w", pady=5)

        ttk.Label(self.inspector, text="Base Texture:").pack(anchor="w")
        base_f = ttk.Frame(self.inspector)
        base_f.pack(fill="x")
        ttk.Entry(base_f, textvariable=self.sel_texture).pack(
            side=tk.LEFT, fill="x", expand=True
        )
        ttk.Button(
            base_f,
            text="...",
            width=3,
            command=lambda: self.browse_texture(self.sel_texture),
        ).pack(side=tk.LEFT)

        ttk.Separator(self.inspector, orient="horizontal").pack(fill="x", pady=15)
        ttk.Label(self.inspector, text="Prop (Top Layer)", style="Bold.TLabel").pack(
            anchor="w"
        )

        self.prop_combo = ttk.Combobox(self.inspector, state="readonly")
        self.prop_combo.pack(fill="x", pady=(5, 5))
        self.prop_combo.set("Load Prop Preset...")
        self.prop_combo.bind("<<ComboboxSelected>>", self.apply_prop_preset)

        ttk.Label(self.inspector, text="Prop Texture:").pack(anchor="w")
        prop_f = ttk.Frame(self.inspector)
        prop_f.pack(fill="x")
        ttk.Entry(prop_f, textvariable=self.sel_prop_texture).pack(
            side=tk.LEFT, fill="x", expand=True
        )
        ttk.Button(
            prop_f,
            text="...",
            width=3,
            command=lambda: self.browse_texture(self.sel_prop_texture),
        ).pack(side=tk.LEFT)
        ttk.Button(
            prop_f, text="X", width=3, command=lambda: self.sel_prop_texture.set("")
        ).pack(side=tk.LEFT)

        props_settings = ttk.Frame(self.inspector)
        props_settings.pack(fill="x", pady=5)

        ttk.Label(props_settings, text="Scale:").pack(anchor="w")
        scale_row = ttk.Frame(props_settings)
        scale_row.pack(fill="x")
        ttk.Scale(
            scale_row,
            from_=0.1,
            to=10.0,
            variable=self.sel_prop_scale,
            orient="horizontal",
        ).pack(side=tk.LEFT, fill="x", expand=True)
        ttk.Entry(scale_row, textvariable=self.sel_prop_scale, width=5).pack(
            side=tk.LEFT, padx=5
        )

        ttk.Label(props_settings, text="Vertical Shift (Up/Down):").pack(
            anchor="w", pady=(5, 0)
        )
        shift_row = ttk.Frame(props_settings)
        shift_row.pack(fill="x")
        ttk.Scale(
            shift_row,
            from_=-100,
            to=200,
            variable=self.sel_prop_shift,
            orient="horizontal",
        ).pack(side=tk.LEFT, fill="x", expand=True)
        ttk.Entry(shift_row, textvariable=self.sel_prop_shift, width=5).pack(
            side=tk.LEFT, padx=5
        )

        ttk.Separator(self.inspector, orient="horizontal").pack(fill="x", pady=20)
        ttk.Button(
            self.inspector, text="Refresh Libraries", command=self.update_asset_combos
        ).pack(fill="x", pady=2)
        ttk.Button(self.inspector, text="SAVE TILE", command=self.save_tile_to_db).pack(
            fill="x", pady=5
        )
        ttk.Button(self.inspector, text="DELETE TILE", command=self.delete_tile).pack(
            fill="x"
        )

        self.update_asset_combos()
        self.draw_grid()

    def center_on_origin(self):
        view_w = self.canvas.winfo_width()
        view_h = self.canvas.winfo_height()
        if view_w <= 1 or view_h <= 1:
            self.root.after(50, self.center_on_origin)
            return
        target_x = (OFFSET_X - (view_w / 2)) / MAP_WIDTH_PIXELS
        target_y = (OFFSET_Y - (view_h / 2)) / MAP_HEIGHT_PIXELS
        self.canvas.xview_moveto(target_x)
        self.canvas.yview_moveto(target_y)

    def browse_texture(self, var):
        f = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg")])
        if f:
            fname = os.path.basename(f)
            dest = os.path.join("assets", fname)
            if not os.path.exists(dest):
                try:
                    shutil.copy(f, dest)
                except:
                    pass
            var.set(fname)
            self.update_library_preview()

    # ======================================================
    # ASSET LIBRARY TAB (REALISTIC PREVIEW)
    # ======================================================
    def create_asset_library_tab(self):
        self.lib_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.lib_frame, text="Asset Library")

        paned_lib = ttk.PanedWindow(self.lib_frame, orient=tk.HORIZONTAL)
        paned_lib.pack(fill="both", expand=True)

        control_frame = ttk.Frame(paned_lib, padding=20)
        paned_lib.add(control_frame, weight=1)

        self.new_asset_category = tk.StringVar(value="tile")
        self.new_asset_filename = tk.StringVar()
        self.new_asset_type = tk.StringVar(value="grass")
        self.new_asset_name = tk.StringVar()
        self.new_asset_texture = tk.StringVar()
        self.new_asset_passable = tk.BooleanVar(value=True)

        self.new_prop_scale = tk.DoubleVar(value=1.0)
        self.new_prop_shift = tk.IntVar(value=0)

        # Trigger preview updates
        self.new_asset_texture.trace_add(
            "write", lambda *a: self.update_library_preview()
        )
        self.new_prop_scale.trace_add("write", lambda *a: self.update_library_preview())
        self.new_prop_shift.trace_add("write", lambda *a: self.update_library_preview())
        self.new_asset_category.trace_add(
            "write", lambda *a: self.update_library_preview()
        )

        ttk.Label(
            control_frame, text="Create Asset Blueprint", style="Bold.TLabel"
        ).pack(pady=10)

        cat_frame = ttk.LabelFrame(control_frame, text="Category")
        cat_frame.pack(fill="x", pady=5)
        ttk.Radiobutton(
            cat_frame,
            text="Terrain Tile",
            variable=self.new_asset_category,
            value="tile",
            command=self.toggle_lib_inputs,
        ).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(
            cat_frame,
            text="Prop / Topper",
            variable=self.new_asset_category,
            value="prop",
            command=self.toggle_lib_inputs,
        ).pack(side=tk.LEFT, padx=10)

        r1 = ttk.Frame(control_frame)
        r1.pack(fill="x", pady=5)
        ttk.Label(r1, text="Filename (no .json):").pack(side=tk.LEFT)
        ttk.Entry(r1, textvariable=self.new_asset_filename).pack(
            side=tk.RIGHT, expand=True, fill="x"
        )

        ttk.Label(control_frame, text="Texture (Select to Auto-Import):").pack(
            anchor="w"
        )
        row_tex = ttk.Frame(control_frame)
        row_tex.pack(fill="x")
        ttk.Entry(row_tex, textvariable=self.new_asset_texture).pack(
            side=tk.LEFT, fill="x", expand=True
        )
        ttk.Button(
            row_tex,
            text="Browse...",
            command=lambda: self.browse_texture(self.new_asset_texture),
        ).pack(side=tk.LEFT)

        self.tile_opts_frame = ttk.LabelFrame(control_frame, text="Terrain Settings")
        self.tile_opts_frame.pack(fill="x", pady=10)

        ttk.Label(self.tile_opts_frame, text="Type (e.g. grass, water):").pack(
            anchor="w"
        )
        ttk.Entry(self.tile_opts_frame, textvariable=self.new_asset_type).pack(fill="x")

        ttk.Label(self.tile_opts_frame, text="Default Name:").pack(anchor="w")
        ttk.Entry(self.tile_opts_frame, textvariable=self.new_asset_name).pack(fill="x")

        ttk.Checkbutton(
            self.tile_opts_frame, text="Is Passable?", variable=self.new_asset_passable
        ).pack(anchor="w", pady=5)

        self.prop_opts_frame = ttk.LabelFrame(control_frame, text="Prop Settings")

        ttk.Label(self.prop_opts_frame, text="Default Scale:").pack(anchor="w")
        ps_row = ttk.Frame(self.prop_opts_frame)
        ps_row.pack(fill="x")
        ttk.Scale(
            ps_row, from_=0.1, to=5.0, variable=self.new_prop_scale, orient="horizontal"
        ).pack(side=tk.LEFT, fill="x", expand=True)
        ttk.Entry(ps_row, textvariable=self.new_prop_scale, width=5).pack(
            side=tk.LEFT, padx=5
        )

        ttk.Label(self.prop_opts_frame, text="Default Y-Shift:").pack(anchor="w")
        ys_row = ttk.Frame(self.prop_opts_frame)
        ys_row.pack(fill="x")
        ttk.Scale(
            ys_row,
            from_=-100,
            to=200,
            variable=self.new_prop_shift,
            orient="horizontal",
        ).pack(side=tk.LEFT, fill="x", expand=True)
        ttk.Entry(ys_row, textvariable=self.new_prop_shift, width=5).pack(
            side=tk.LEFT, padx=5
        )

        ttk.Button(
            control_frame, text="SAVE BLUEPRINT", command=self.save_asset_json
        ).pack(pady=20, fill="x")

        preview_container = ttk.Frame(paned_lib)
        paned_lib.add(preview_container, weight=2)

        ttk.Label(
            preview_container, text="Real-time Game Preview", style="Bold.TLabel"
        ).pack(pady=10)

        self.preview_canvas = Canvas(
            preview_container, bg="#303030", width=500, height=500
        )
        self.preview_canvas.pack(fill="both", expand=True, padx=10, pady=10)

        self.toggle_lib_inputs()

    def toggle_lib_inputs(self):
        cat = self.new_asset_category.get()
        if cat == "tile":
            self.prop_opts_frame.pack_forget()
            self.tile_opts_frame.pack(fill="x", pady=10)
        else:
            self.tile_opts_frame.pack_forget()
            self.prop_opts_frame.pack(fill="x", pady=10)
        self.update_library_preview()

    # --- THIS PREVIEW MATCHES THE GAME ENGINE (GAME_HEX_SIZE) ---
    def update_library_preview(self):
        self.preview_canvas.delete("all")

        w = self.preview_canvas.winfo_width()
        h = self.preview_canvas.winfo_height()
        if w < 10:
            w = 500
        if h < 10:
            h = 500
        cx, cy = w // 2, h // 2

        # 1. Draw Iso Reference Grid (Using GAME_HEX_SIZE and ISO_SQUASH)
        points = []
        for i in range(6):
            angle_deg = 60 * i
            angle_rad = math.pi / 180 * angle_deg
            px = GAME_HEX_SIZE * math.cos(angle_rad)
            py = GAME_HEX_SIZE * math.sin(angle_rad) * ISO_SQUASH
            points.append(cx + px)
            points.append(cy + py)

        self.preview_canvas.create_polygon(
            points, fill="", outline="#4caf50", width=1, dash=(2, 2)
        )
        self.preview_canvas.create_line(cx - 5, cy, cx + 5, cy, fill="red")
        self.preview_canvas.create_line(cx, cy - 5, cx, cy + 5, fill="red")

        tex = self.new_asset_texture.get()
        cat = self.new_asset_category.get()

        # 2. IF PROP: Load 'default.png' as the base tile
        if cat == "prop":
            base_tex = "default.png"
            target_w_base = int(GAME_HEX_SIZE * IMG_SCALE_MODIFIER)
            base_img = self.get_tk_image(base_tex, target_width=target_w_base)

            if base_img:
                draw_y_base = cy + VERTICAL_OFFSET
                self.preview_canvas.create_image(
                    cx, draw_y_base, image=base_img, anchor="center"
                )
            else:
                self.preview_canvas.create_text(
                    cx, cy + 20, text="(default.png not found)", fill="red"
                )

        if not tex:
            return

        # 3. Draw Selected Asset (Scaled 1:1 with Game)
        if cat == "tile":
            target_w = int(GAME_HEX_SIZE * IMG_SCALE_MODIFIER)
            img = self.get_tk_image(tex, target_width=target_w)
            if img:
                draw_y = cy + VERTICAL_OFFSET
                self.preview_canvas.create_image(cx, draw_y, image=img, anchor="center")

        elif cat == "prop":
            try:
                scale = self.new_prop_scale.get()
                shift = self.new_prop_shift.get()

                target_w = int(GAME_HEX_SIZE * scale)
                if target_w <= 0:
                    target_w = 1

                p_img = self.get_tk_image(tex, target_width=target_w)

                if p_img:
                    draw_y = cy - shift
                    self.preview_canvas.create_image(
                        cx, draw_y, image=p_img, anchor="center"
                    )

            except Exception:
                pass

    def update_asset_combos(self):
        self.refresh_asset_library()
        self.tile_combo["values"] = list(self.tile_library.keys())
        self.prop_combo["values"] = list(self.prop_library.keys())

    def apply_tile_preset(self, event):
        sel = self.tile_combo.get()
        if sel in self.tile_library:
            d = self.tile_library[sel]
            self.sel_type.set(d.get("tile_type", "grass"))
            self.sel_name.set(d.get("location_name", ""))
            self.sel_passable.set(d.get("is_permanently_passable", True))
            self.sel_texture.set(d.get("texture_file", ""))

    def apply_prop_preset(self, event):
        sel = self.prop_combo.get()
        if sel in self.prop_library:
            d = self.prop_library[sel]
            self.sel_prop_texture.set(d.get("texture_file", ""))
            self.sel_prop_scale.set(d.get("prop_scale", 1.0))
            self.sel_prop_shift.set(d.get("prop_y_shift", 0))

    def save_asset_json(self):
        fn = self.new_asset_filename.get().strip()
        if not fn:
            messagebox.showerror("Error", "Filename required")
            return

        cat = self.new_asset_category.get()

        if cat == "tile":
            folder = "assets/definitions/tiles"
            data = {
                "category": "tile",
                "tile_type": self.new_asset_type.get(),
                "location_name": self.new_asset_name.get(),
                "is_permanently_passable": self.new_asset_passable.get(),
                "texture_file": self.new_asset_texture.get(),
            }
        else:
            folder = "assets/definitions/props"
            data = {
                "category": "prop",
                "texture_file": self.new_asset_texture.get(),
                "prop_scale": self.new_prop_scale.get(),
                "prop_y_shift": self.new_prop_shift.get(),
            }

        with open(f"{folder}/{fn}.json", "w") as f:
            json.dump(data, f, indent=4)

        messagebox.showinfo("Saved", f"Saved {cat} definition.")
        self.update_asset_combos()

    # ======================================================
    # GRID LOGIC (SCHEMATIC / EDITOR_HEX_SIZE)
    # ======================================================
    def hex_to_pixel(self, q, r):
        # Uses EDITOR_HEX_SIZE for schematic view
        x = EDITOR_HEX_SIZE * (3.0 / 2 * q)
        y = EDITOR_HEX_SIZE * (math.sqrt(3) / 2 * q + math.sqrt(3) * r)
        return x, y

    def pixel_to_hex(self, x, y):
        # Uses EDITOR_HEX_SIZE for schematic view
        x = x - OFFSET_X
        y = y - OFFSET_Y
        q = (2.0 / 3 * x) / EDITOR_HEX_SIZE
        r = (-1.0 / 3 * x + math.sqrt(3) / 3 * y) / EDITOR_HEX_SIZE
        return self.cube_round(q, r, -q - r)

    def cube_round(self, frac_q, frac_r, frac_s):
        q = round(frac_q)
        r = round(frac_r)
        s = round(frac_s)
        q_diff = abs(q - frac_q)
        r_diff = abs(r - frac_r)
        s_diff = abs(s - frac_s)
        if q_diff > r_diff and q_diff > s_diff:
            q = -r - s
        elif r_diff > s_diff:
            r = -q - s
        else:
            s = -q - r
        return int(q), int(r)

    def draw_grid(self):
        self.canvas.delete("all")
        self.tk_image_cache = {}

        self.cursor.execute("SELECT * FROM map_tiles")
        rows = self.cursor.fetchall()
        existing_tiles = {}
        for row in rows:
            existing_tiles[(row["q"], row["r"])] = dict(row)

        for q in range(-GRID_RANGE, GRID_RANGE + 1):
            for r in range(-GRID_RANGE, GRID_RANGE + 1):
                if abs(q + r) > GRID_RANGE:
                    continue

                local_x, local_y = self.hex_to_pixel(q, r)
                cx = local_x + OFFSET_X
                cy = local_y + OFFSET_Y

                if (q, r) not in existing_tiles:
                    points = self.get_hex_points(cx, cy)
                    self.canvas.create_polygon(
                        points, fill="", outline="#333", tags=("ghost", f"{q},{r}")
                    )

        sorted_coords = sorted(existing_tiles.keys(), key=lambda k: (k[1], k[0]))

        for q, r in sorted_coords:
            t = existing_tiles[(q, r)]
            local_x, local_y = self.hex_to_pixel(q, r)
            cx = local_x + OFFSET_X
            cy = local_y + OFFSET_Y

            points = self.get_hex_points(cx, cy)

            color = "#4caf50"
            ttype = t.get("tile_type", "grass")
            if ttype == "water":
                color = "#2196f3"
            elif ttype == "mountain":
                color = "#795548"

            self.canvas.create_polygon(
                points, fill=color, outline="#666", tags=("hex", f"{q},{r}")
            )

            # --- SCHEMATIC VIEW: Scale images to fit EDITOR_HEX_SIZE ---
            # 1. Base Tile
            if t.get("texture_file"):
                # Scale slightly larger than the hex to fill it
                target_w = int(EDITOR_HEX_SIZE * 2.0)
                img = self.get_tk_image(t["texture_file"], target_width=target_w)
                if img:
                    self.canvas.create_image(cx, cy, image=img, anchor="center")

            # 2. Prop (Schematic)
            # Just center it on the tile, scaled down
            prop = t.get("prop_texture_file") or t.get("overlay_texture_file")
            is_selected = q == self.sel_q.get() and r == self.sel_r.get()

            if is_selected:
                scale = self.sel_prop_scale.get()
                ui_prop = self.sel_prop_texture.get()
                if ui_prop:
                    prop = ui_prop
            else:
                scale = t.get("prop_scale", 1.0)

            if scale is None:
                scale = 1.0

            if prop:
                # Scale relative to the Editor Hex, ignoring complex game shifts
                target_w = int(EDITOR_HEX_SIZE * scale)
                if target_w <= 0:
                    target_w = 1
                p_img = self.get_tk_image(prop, target_width=target_w)
                if p_img:
                    # Draw slightly above center to mimic "standing" on tile
                    self.canvas.create_image(cx, cy - 5, image=p_img, anchor="center")

        cx0, cy0 = self.hex_to_pixel(0, 0)
        cx0 += OFFSET_X
        cy0 += OFFSET_Y
        self.canvas.create_text(cx0, cy0, text="0,0", fill="white", font=("Arial", 8))

    # Helper for drawing grid hexagons (uses EDITOR_HEX_SIZE)
    def get_hex_points(self, cx, cy):
        points = []
        for i in range(6):
            angle_deg = 60 * i
            angle_rad = math.pi / 180 * angle_deg
            # Flat hex for schematic view (no ISO_SQUASH)
            px = cx + EDITOR_HEX_SIZE * math.cos(angle_rad)
            py = cy + EDITOR_HEX_SIZE * math.sin(angle_rad)
            points.append(px)
            points.append(py)
        return points

    def on_map_click(self, event):
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        q, r = self.pixel_to_hex(cx, cy)
        self.load_tile_inspector(q, r)

    def load_tile_inspector(self, q, r):
        self.sel_q.set(q)
        self.sel_r.set(r)

        self.cursor.execute("SELECT * FROM map_tiles WHERE q=? AND r=?", (q, r))
        row = self.cursor.fetchone()

        if row:
            self.sel_type.set(row["tile_type"])
            self.sel_name.set(row["location_name"] or "")
            self.sel_passable.set(bool(row["is_permanently_passable"]))
            self.sel_texture.set(row["texture_file"] or "")

            prop = ""
            if "prop_texture_file" in row.keys():
                prop = row["prop_texture_file"]
            elif "overlay_texture_file" in row.keys():
                prop = row["overlay_texture_file"]

            self.sel_prop_texture.set(prop or "")
            self.sel_prop_scale.set(
                row["prop_scale"] if row["prop_scale"] is not None else 1.0
            )
            self.sel_prop_shift.set(
                row["prop_y_shift"] if row["prop_y_shift"] is not None else 0
            )
        else:
            self.sel_type.set("grass")
            self.sel_name.set("")
            self.sel_passable.set(True)
            self.sel_texture.set("")
            self.sel_prop_texture.set("")
            self.sel_prop_scale.set(1.0)
            self.sel_prop_shift.set(0)

    def save_tile_to_db(self):
        q, r = self.sel_q.get(), self.sel_r.get()
        prop = self.sel_prop_texture.get().strip() or None

        try:
            self.cursor.execute(
                """
                INSERT INTO map_tiles (
                    q, r, tile_type, location_name, level, texture_file, 
                    is_permanently_passable, prop_texture_file, prop_scale, prop_y_shift
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(q, r) DO UPDATE SET
                    tile_type=excluded.tile_type,
                    location_name=excluded.location_name,
                    level=excluded.level,
                    texture_file=excluded.texture_file,
                    is_permanently_passable=excluded.is_permanently_passable,
                    prop_texture_file=excluded.prop_texture_file,
                    prop_scale=excluded.prop_scale,
                    prop_y_shift=excluded.prop_y_shift
            """,
                (
                    q,
                    r,
                    self.sel_type.get(),
                    self.sel_name.get() or None,
                    1,
                    self.sel_texture.get(),
                    self.sel_passable.get(),
                    prop,
                    self.sel_prop_scale.get(),
                    self.sel_prop_shift.get(),
                ),
            )
            self.conn.commit()
            self.draw_grid()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_tile(self):
        q, r = self.sel_q.get(), self.sel_r.get()
        if messagebox.askyesno("Delete", f"Delete tile {q},{r}?"):
            self.cursor.execute("DELETE FROM map_tiles WHERE q=? AND r=?", (q, r))
            self.conn.commit()
            self.draw_grid()
            self.load_tile_inspector(q, r)


if __name__ == "__main__":
    root = tk.Tk()
    app = GameEditor(root)
    root.mainloop()
