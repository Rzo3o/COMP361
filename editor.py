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

# --- EDITOR VIEW (Schematic) ---
EDITOR_HEX_SIZE = 30
GRID_RANGE = 20
MAP_WIDTH_PIXELS = 1600
MAP_HEIGHT_PIXELS = 1400
OFFSET_X = MAP_WIDTH_PIXELS // 2
OFFSET_Y = MAP_HEIGHT_PIXELS // 2

# --- GAME ENGINE VIEW (Realistic) ---
GAME_SCALE = 3
BASE_HEX_RADIUS = 16
GAME_HEX_SIZE = BASE_HEX_RADIUS * GAME_SCALE

# Game Calibration
ISO_SQUASH = 0.9280
IMG_SCALE_MODIFIER = 3.010
VERTICAL_OFFSET = -13.5

DIRS = [
    "assets/definitions/tiles",
    "assets/definitions/props",
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
        self.root.geometry("1400x950")

        self.conn = sqlite3.connect("game_data.db")
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        # Ensure DB compatibility
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

        # --- NEW: Monster Editor State ---
        # Stores the temporary list of animations for the monster currently being edited
        # Format: {"idle": {texture, fw, fh, count}, "hit": {...}}
        self.current_monster_anims = {}
        self.selected_anim_name = None

        style = ttk.Style()
        style.configure("Bold.TLabel", font=("Helvetica", 10, "bold"))

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        self.create_map_designer_tab()
        self.create_asset_library_tab()

        # Animation Loop State
        self.anim_frame_index = 0
        self.run_animation_loop()

    def apply_tile_preset(self, event):
        selection = self.tile_combo.get()
        if selection in self.tile_library:
            data = self.tile_library[selection]
            # Populate inspector fields from the JSON data
            self.sel_type.set(data.get("tile_type", "grass"))
            self.sel_texture.set(data.get("texture_file", ""))
            self.sel_passable.set(data.get("is_permanently_passable", True))
            # Note: We don't auto-save here; user must click "SAVE TILE"

    def apply_prop_preset(self, event):
        selection = self.prop_combo.get()
        if selection in self.prop_library:
            data = self.prop_library[selection]
            # Populate inspector fields
            self.sel_prop_texture.set(data.get("texture_file", ""))
            self.sel_prop_scale.set(data.get("prop_scale", 1.0))
            self.sel_prop_shift.set(data.get("prop_y_shift", 0))

    def run_animation_loop(self):
        self.anim_frame_index += 1
        # Update preview if we are in Monster mode
        if self.new_asset_category.get() == "monster":
            self.update_library_preview()
        self.root.after(100, self.run_animation_loop)

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
                if target_width:
                    w_percent = target_width / float(pil_img.size[0])
                    h_size = int((float(pil_img.size[1]) * float(w_percent)))
                    pil_img = pil_img.resize(
                        (target_width, h_size), Image.Resampling.NEAREST
                    )
                tk_img = ImageTk.PhotoImage(pil_img)
                self.tk_image_cache[cache_key] = tk_img
            except:
                return None
        return self.tk_image_cache[cache_key]

    def refresh_asset_library(self):
        self.tile_library = {}
        self.prop_library = {}
        # Load Tiles
        pt = "assets/definitions/tiles"
        if os.path.exists(pt):
            for f in os.listdir(pt):
                if f.endswith(".json"):
                    with open(os.path.join(pt, f), "r") as file:
                        self.tile_library[f] = json.load(file)
        # Load Props
        pp = "assets/definitions/props"
        if os.path.exists(pp):
            for f in os.listdir(pp):
                if f.endswith(".json"):
                    with open(os.path.join(pp, f), "r") as file:
                        self.prop_library[f] = json.load(file)

    # ======================================================
    # TAB 1: MAP DESIGNER
    # ======================================================
    def create_map_designer_tab(self):
        self.map_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.map_frame, text="Map Designer")

        paned = ttk.PanedWindow(self.map_frame, orient=tk.HORIZONTAL)
        paned.pack(fill="both", expand=True)

        # Canvas
        c_cont = ttk.Frame(paned)
        paned.add(c_cont, weight=3)
        self.v_scroll = ttk.Scrollbar(c_cont, orient=tk.VERTICAL)
        self.h_scroll = ttk.Scrollbar(c_cont, orient=tk.HORIZONTAL)
        self.canvas = Canvas(
            c_cont,
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
        self.canvas.bind("<Button-1>", self.on_map_click)

        # Inspector
        self.inspector = ttk.Frame(paned, padding=10)
        paned.add(self.inspector, weight=1)

        # Inspector Vars
        self.sel_q = tk.IntVar()
        self.sel_r = tk.IntVar()
        self.sel_type = tk.StringVar()
        self.sel_name = tk.StringVar()
        self.sel_passable = tk.BooleanVar(value=True)
        self.sel_texture = tk.StringVar()
        self.sel_prop_texture = tk.StringVar()
        self.sel_prop_scale = tk.DoubleVar(value=1.0)
        self.sel_prop_shift = tk.IntVar(value=0)

        # Triggers
        self.sel_prop_scale.trace_add("write", lambda *a: self.draw_grid())
        self.sel_prop_shift.trace_add("write", lambda *a: self.draw_grid())

        # Layout
        ttk.Label(self.inspector, text="Selected Hex", style="Bold.TLabel").pack(
            pady=(0, 10)
        )
        gf = ttk.Frame(self.inspector)
        gf.pack(fill="x")
        ttk.Label(gf, text="Q:").pack(side=tk.LEFT)
        ttk.Label(
            # Change 'fg' to 'foreground'
            gf,
            textvariable=self.sel_q,
            font=("Mono", 12, "bold"),
            foreground="blue",
        ).pack(side=tk.LEFT, padx=5)
        ttk.Label(gf, text="R:").pack(side=tk.LEFT)
        ttk.Label(
            # Change 'fg' to 'foreground'
            gf,
            textvariable=self.sel_r,
            font=("Mono", 12, "bold"),
            foreground="blue",
        ).pack(side=tk.LEFT, padx=5)

        ttk.Separator(self.inspector).pack(fill="x", pady=10)

        # Tile Settings
        ttk.Label(self.inspector, text="Terrain", style="Bold.TLabel").pack(anchor="w")
        self.tile_combo = ttk.Combobox(self.inspector, state="readonly")
        self.tile_combo.pack(fill="x", pady=5)
        self.tile_combo.bind("<<ComboboxSelected>>", self.apply_tile_preset)

        ttk.Label(self.inspector, text="Type:").pack(anchor="w")
        ttk.Entry(self.inspector, textvariable=self.sel_type).pack(fill="x")

        ttk.Label(self.inspector, text="Base Texture:").pack(anchor="w")
        bf = ttk.Frame(self.inspector)
        bf.pack(fill="x")
        ttk.Entry(bf, textvariable=self.sel_texture).pack(
            side=tk.LEFT, fill="x", expand=True
        )
        ttk.Button(
            bf,
            text="...",
            width=3,
            command=lambda: self.browse_texture(self.sel_texture),
        ).pack(side=tk.LEFT)

        ttk.Separator(self.inspector).pack(fill="x", pady=15)

        # Prop Settings
        ttk.Label(self.inspector, text="Prop / Overlay", style="Bold.TLabel").pack(
            anchor="w"
        )
        self.prop_combo = ttk.Combobox(self.inspector, state="readonly")
        self.prop_combo.pack(fill="x", pady=5)
        self.prop_combo.bind("<<ComboboxSelected>>", self.apply_prop_preset)

        ttk.Label(self.inspector, text="Prop Texture:").pack(anchor="w")
        pf = ttk.Frame(self.inspector)
        pf.pack(fill="x")
        ttk.Entry(pf, textvariable=self.sel_prop_texture).pack(
            side=tk.LEFT, fill="x", expand=True
        )
        ttk.Button(
            pf,
            text="...",
            width=3,
            command=lambda: self.browse_texture(self.sel_prop_texture),
        ).pack(side=tk.LEFT)
        ttk.Button(
            pf, text="X", width=3, command=lambda: self.sel_prop_texture.set("")
        ).pack(side=tk.LEFT)

        ttk.Label(self.inspector, text="Scale:").pack(anchor="w", pady=(5, 0))
        ttk.Scale(
            self.inspector, from_=0.1, to=10.0, variable=self.sel_prop_scale
        ).pack(fill="x")

        ttk.Label(self.inspector, text="Y-Shift:").pack(anchor="w", pady=(5, 0))
        ttk.Scale(
            self.inspector, from_=-100, to=200, variable=self.sel_prop_shift
        ).pack(fill="x")

        ttk.Separator(self.inspector).pack(fill="x", pady=20)
        ttk.Button(self.inspector, text="SAVE TILE", command=self.save_tile_to_db).pack(
            fill="x", pady=5
        )
        ttk.Button(self.inspector, text="DELETE TILE", command=self.delete_tile).pack(
            fill="x"
        )

        self.update_asset_combos()
        self.draw_grid()
        self.root.after(100, self.center_on_origin)

    def center_on_origin(self):
        # Center the scrollbars
        self.canvas.xview_moveto(
            (OFFSET_X - self.canvas.winfo_width() / 2) / MAP_WIDTH_PIXELS
        )
        self.canvas.yview_moveto(
            (OFFSET_Y - self.canvas.winfo_height() / 2) / MAP_HEIGHT_PIXELS
        )

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
    # TAB 2: ASSET LIBRARY & MONSTER EDITOR
    # ======================================================
    def create_asset_library_tab(self):
        self.lib_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.lib_frame, text="Asset Library")

        paned_lib = ttk.PanedWindow(self.lib_frame, orient=tk.HORIZONTAL)
        paned_lib.pack(fill="both", expand=True)

        # --- LEFT: CONTROLS ---
        control_frame = ttk.Frame(paned_lib, padding=20)
        paned_lib.add(control_frame, weight=1)

        # Shared Variables
        self.new_asset_category = tk.StringVar(value="tile")
        self.new_asset_filename = tk.StringVar()
        self.new_asset_texture = tk.StringVar()

        # Tile/Prop Variables
        self.new_asset_type = tk.StringVar(value="grass")
        self.new_asset_passable = tk.BooleanVar(value=True)
        self.new_prop_scale = tk.DoubleVar(value=1.0)
        self.new_prop_shift = tk.IntVar(value=0)

        # --- NEW: Monster Variables ---
        self.monster_scale = tk.DoubleVar(value=3.0)
        self.monster_y_shift = tk.IntVar(value=0)  # <--- NEW Y-SHIFT VARIABLE

        # Triggers
        self.new_asset_texture.trace_add(
            "write", lambda *a: self.update_library_preview()
        )
        self.new_prop_scale.trace_add("write", lambda *a: self.update_library_preview())
        self.new_prop_shift.trace_add("write", lambda *a: self.update_library_preview())
        self.monster_y_shift.trace_add(
            "write", lambda *a: self.update_library_preview()
        )  # <--- TRIGGER UPDATE
        self.new_asset_category.trace_add("write", lambda *a: self.toggle_lib_inputs())

        # Category Selector
        ttk.Label(control_frame, text="Create New Asset", style="Bold.TLabel").pack(
            pady=10
        )
        cat_frame = ttk.LabelFrame(control_frame, text="Category")
        cat_frame.pack(fill="x", pady=5)

        ttk.Radiobutton(
            cat_frame, text="Tile", variable=self.new_asset_category, value="tile"
        ).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(
            cat_frame, text="Prop", variable=self.new_asset_category, value="prop"
        ).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(
            cat_frame, text="Monster", variable=self.new_asset_category, value="monster"
        ).pack(side=tk.LEFT, padx=10)

        # File Name Input
        r1 = ttk.Frame(control_frame)
        r1.pack(fill="x", pady=5)
        ttk.Label(r1, text="Asset ID / Name:").pack(side=tk.LEFT)
        ttk.Entry(r1, textvariable=self.new_asset_filename).pack(
            side=tk.RIGHT, expand=True, fill="x", padx=5
        )

        # --- PANEL A: TILE SETTINGS ---
        self.tile_opts_frame = ttk.LabelFrame(control_frame, text="Tile Configuration")
        ttk.Label(self.tile_opts_frame, text="Texture:").pack(anchor="w")
        tf = ttk.Frame(self.tile_opts_frame)
        tf.pack(fill="x")
        ttk.Entry(tf, textvariable=self.new_asset_texture).pack(
            side=tk.LEFT, fill="x", expand=True
        )
        ttk.Button(
            tf,
            text="Browse",
            command=lambda: self.browse_texture(self.new_asset_texture),
        ).pack(side=tk.LEFT)
        ttk.Label(self.tile_opts_frame, text="Type (grass, water...):").pack(anchor="w")
        ttk.Entry(self.tile_opts_frame, textvariable=self.new_asset_type).pack(fill="x")
        ttk.Checkbutton(
            self.tile_opts_frame, text="Passable?", variable=self.new_asset_passable
        ).pack(anchor="w", pady=5)

        # --- PANEL B: PROP SETTINGS ---
        self.prop_opts_frame = ttk.LabelFrame(control_frame, text="Prop Configuration")
        ttk.Label(self.prop_opts_frame, text="Texture:").pack(anchor="w")
        pf = ttk.Frame(self.prop_opts_frame)
        pf.pack(fill="x")
        ttk.Entry(pf, textvariable=self.new_asset_texture).pack(
            side=tk.LEFT, fill="x", expand=True
        )
        ttk.Button(
            pf,
            text="Browse",
            command=lambda: self.browse_texture(self.new_asset_texture),
        ).pack(side=tk.LEFT)
        ttk.Label(self.prop_opts_frame, text="Scale:").pack(anchor="w")
        ttk.Scale(
            self.prop_opts_frame, from_=0.1, to=5.0, variable=self.new_prop_scale
        ).pack(fill="x")
        ttk.Label(self.prop_opts_frame, text="Y-Shift:").pack(anchor="w")
        ttk.Scale(
            self.prop_opts_frame, from_=-100, to=200, variable=self.new_prop_shift
        ).pack(fill="x")

        # --- PANEL C: MONSTER SETTINGS (COMPLEX) ---
        self.monster_opts_frame = ttk.LabelFrame(
            control_frame, text="Monster Animation Manager"
        )

        # Global Scale & Shift
        ttk.Label(self.monster_opts_frame, text="Global Scale:").pack(anchor="w")
        ttk.Scale(
            self.monster_opts_frame,
            from_=0.5,
            to=5.0,
            variable=self.monster_scale,
            orient="horizontal",
        ).pack(fill="x")

        # --- NEW SLIDER HERE ---
        ttk.Label(self.monster_opts_frame, text="Global Y-Shift:").pack(anchor="w")
        ttk.Scale(
            self.monster_opts_frame,
            from_=-100,
            to=100,
            variable=self.monster_y_shift,
            orient="horizontal",
        ).pack(fill="x")

        # Animation List
        ttk.Label(self.monster_opts_frame, text="Animations:").pack(
            anchor="w", pady=(10, 0)
        )
        self.anim_listbox = tk.Listbox(self.monster_opts_frame, height=4)
        self.anim_listbox.pack(fill="x", padx=5)
        self.anim_listbox.bind("<<ListboxSelect>>", self.on_anim_select)

        btn_row = ttk.Frame(self.monster_opts_frame)
        btn_row.pack(fill="x", pady=2)
        ttk.Button(btn_row, text="+ Add Anim", command=self.add_anim_entry).pack(
            side=tk.LEFT, expand=True
        )
        ttk.Button(btn_row, text="- Remove", command=self.remove_anim_entry).pack(
            side=tk.LEFT, expand=True
        )

        ttk.Separator(self.monster_opts_frame).pack(fill="x", pady=5)

        # Specific Animation Details
        self.anim_name_var = tk.StringVar()
        self.anim_tex_var = tk.StringVar()
        self.anim_fw_var = tk.IntVar(value=32)
        self.anim_fh_var = tk.IntVar(value=32)
        self.anim_count_var = tk.IntVar(value=4)

        # Auto-update current anim data when these change
        self.anim_tex_var.trace_add("write", self.save_current_anim_field)
        self.anim_fw_var.trace_add("write", self.save_current_anim_field)
        self.anim_fh_var.trace_add("write", self.save_current_anim_field)
        self.anim_count_var.trace_add("write", self.save_current_anim_field)

        grid = ttk.Frame(self.monster_opts_frame)
        grid.pack(fill="x", pady=5)

        ttk.Label(grid, text="Anim Name:").grid(row=0, column=0, sticky="w")
        ttk.Entry(grid, textvariable=self.anim_name_var, state="readonly").grid(
            row=0, column=1, sticky="ew"
        )

        ttk.Label(grid, text="Texture:").grid(row=1, column=0, sticky="w")
        tf2 = ttk.Frame(grid)
        tf2.grid(row=1, column=1, sticky="ew")
        ttk.Entry(tf2, textvariable=self.anim_tex_var).pack(
            side=tk.LEFT, fill="x", expand=True
        )
        ttk.Button(
            tf2,
            text="...",
            width=2,
            command=lambda: self.browse_texture(self.anim_tex_var),
        ).pack(side=tk.LEFT)

        ttk.Label(grid, text="Frame W:").grid(row=2, column=0, sticky="w")
        ttk.Entry(grid, textvariable=self.anim_fw_var).grid(
            row=2, column=1, sticky="ew"
        )
        ttk.Label(grid, text="Frame H:").grid(row=3, column=0, sticky="w")
        ttk.Entry(grid, textvariable=self.anim_fh_var).grid(
            row=3, column=1, sticky="ew"
        )
        ttk.Label(grid, text="Count:").grid(row=4, column=0, sticky="w")
        ttk.Entry(grid, textvariable=self.anim_count_var).grid(
            row=4, column=1, sticky="ew"
        )

        # Save Button
        ttk.Button(
            control_frame, text="SAVE ASSET DEFINITION", command=self.save_asset_json
        ).pack(pady=20, fill="x")

        # --- RIGHT: PREVIEW ---
        preview_container = ttk.Frame(paned_lib)
        paned_lib.add(preview_container, weight=2)

        ttk.Label(
            preview_container, text="Real-time Preview", style="Bold.TLabel"
        ).pack(pady=10)
        self.preview_canvas = Canvas(
            preview_container, bg="#303030", width=500, height=500
        )
        self.preview_canvas.pack(fill="both", expand=True, padx=10, pady=10)

        self.toggle_lib_inputs()

    # ==========================================
    # MONSTER ANIMATION LOGIC
    # ==========================================
    def add_anim_entry(self):
        # Ask for name
        from tkinter import simpledialog

        name = simpledialog.askstring(
            "New Animation", "Enter state name (e.g. 'idle', 'walk', 'hit'):"
        )
        if name and name not in self.current_monster_anims:
            # Default Data
            self.current_monster_anims[name] = {
                "texture": "",
                "fw": 32,
                "fh": 32,
                "count": 4,
            }
            self.anim_listbox.insert(tk.END, name)
            self.anim_listbox.selection_clear(0, tk.END)
            self.anim_listbox.selection_set(tk.END)
            self.on_anim_select(None)

    def remove_anim_entry(self):
        sel = self.anim_listbox.curselection()
        if not sel:
            return
        name = self.anim_listbox.get(sel[0])
        if name in self.current_monster_anims:
            del self.current_monster_anims[name]
        self.anim_listbox.delete(sel[0])
        self.selected_anim_name = None
        self.anim_name_var.set("")

    def on_anim_select(self, event):
        sel = self.anim_listbox.curselection()
        if not sel:
            return
        name = self.anim_listbox.get(sel[0])
        self.selected_anim_name = name

        data = self.current_monster_anims[name]
        self.anim_name_var.set(name)
        self.anim_tex_var.set(data["texture"])
        self.anim_fw_var.set(data["fw"])
        self.anim_fh_var.set(data["fh"])
        self.anim_count_var.set(data["count"])

        # Trigger preview update
        self.update_library_preview()

    def save_current_anim_field(self, *args):
        if not self.selected_anim_name:
            return
        try:
            self.current_monster_anims[self.selected_anim_name] = {
                "texture": self.anim_tex_var.get(),
                "fw": self.anim_fw_var.get(),
                "fh": self.anim_fh_var.get(),
                "count": self.anim_count_var.get(),
            }
            self.update_library_preview()
        except:
            pass

    # ==========================================
    # GENERAL LIBRARY LOGIC
    # ==========================================
    def toggle_lib_inputs(self):
        cat = self.new_asset_category.get()
        self.tile_opts_frame.pack_forget()
        self.prop_opts_frame.pack_forget()
        self.monster_opts_frame.pack_forget()

        if cat == "tile":
            self.tile_opts_frame.pack(fill="x", pady=10)
        elif cat == "prop":
            self.prop_opts_frame.pack(fill="x", pady=10)
        elif cat == "monster":
            self.monster_opts_frame.pack(fill="x", pady=10)

        self.update_library_preview()

    def update_library_preview(self):
        self.preview_canvas.delete("all")
        w = self.preview_canvas.winfo_width()
        h = self.preview_canvas.winfo_height()
        cx, cy = w // 2, h // 2

        # Draw Grid
        points = []
        for i in range(6):
            angle = math.radians(60 * i)
            px = GAME_HEX_SIZE * math.cos(angle)
            py = GAME_HEX_SIZE * math.sin(angle) * ISO_SQUASH
            points.append(cx + px)
            points.append(cy + py)
        self.preview_canvas.create_polygon(
            points, fill="", outline="#4caf50", dash=(2, 2)
        )

        cat = self.new_asset_category.get()

        # === MONSTER PREVIEW ===
        if cat == "monster":
            base_img = self.get_tk_image(
                "default.png", target_width=int(GAME_HEX_SIZE * IMG_SCALE_MODIFIER)
            )
            if base_img:
                self.preview_canvas.create_image(
                    cx, cy + VERTICAL_OFFSET, image=base_img, anchor="center"
                )

            if not self.selected_anim_name:
                self.preview_canvas.create_text(
                    cx, cy, text="No Animation Selected", fill="white"
                )
                return

            data = self.current_monster_anims.get(self.selected_anim_name)
            if not data or not data["texture"]:
                return

            try:
                # Load Texture
                path = os.path.join("assets", data["texture"])
                if not os.path.exists(path):
                    return

                pil_full = Image.open(path)
                fw = int(data["fw"])
                fh = int(data["fh"])
                count = int(data["count"])
                if count < 1:
                    count = 1
                if fw < 1:
                    fw = 32

                # Crop Frame
                cur_frame = self.anim_frame_index % count
                crop_x = cur_frame * fw
                if crop_x + fw > pil_full.width:
                    crop_x = 0

                pil_frame = pil_full.crop((crop_x, 0, crop_x + fw, fh))

                # Scale
                m_scale = self.monster_scale.get()
                m_shift = self.monster_y_shift.get()  # <--- GET Y-SHIFT

                target_w = int(fw * m_scale)
                target_h = int(fh * m_scale)
                pil_frame = pil_frame.resize(
                    (target_w, target_h), Image.Resampling.NEAREST
                )

                tk_img = ImageTk.PhotoImage(pil_frame)
                self.current_monster_img = tk_img

                # Draw with shift
                draw_y = (cy - (target_h // 2) + 15) + m_shift  # <--- APPLY Y-SHIFT
                self.preview_canvas.create_image(
                    cx, draw_y, image=tk_img, anchor="center"
                )

                self.preview_canvas.create_text(
                    cx,
                    cy + 80,
                    text=f"Playing: {self.selected_anim_name}",
                    fill="yellow",
                )

            except Exception as e:
                print(e)
                pass

        # === PROP/TILE PREVIEW ===
        else:
            tex = self.new_asset_texture.get()
            if not tex:
                return

            if cat == "prop":
                base_img = self.get_tk_image(
                    "default.png", target_width=int(GAME_HEX_SIZE * IMG_SCALE_MODIFIER)
                )
                if base_img:
                    self.preview_canvas.create_image(
                        cx, cy + VERTICAL_OFFSET, image=base_img
                    )

            scale = self.new_prop_scale.get() if cat == "prop" else IMG_SCALE_MODIFIER
            shift = self.new_prop_shift.get() if cat == "prop" else 0

            target_w = int(GAME_HEX_SIZE * scale)
            img = self.get_tk_image(tex, target_width=target_w)

            if img:
                draw_y = cy - shift if cat == "prop" else cy + VERTICAL_OFFSET
                self.preview_canvas.create_image(cx, draw_y, image=img, anchor="center")

    def save_asset_json(self):
        fn = self.new_asset_filename.get().strip()
        if not fn:
            return messagebox.showerror("Error", "Filename required")
        cat = self.new_asset_category.get()

        data = {}
        folder = ""

        if cat == "monster":
            folder = "assets/definitions/monsters"
            data = {
                "category": "monster",
                "name": fn,
                "scale": self.monster_scale.get(),
                "y_shift": self.monster_y_shift.get(),  # <--- SAVE Y-SHIFT
                "animations": self.current_monster_anims,
            }
        elif cat == "tile":
            folder = "assets/definitions/tiles"
            data = {
                "category": "tile",
                "tile_type": self.new_asset_type.get(),
                "location_name": self.new_asset_filename.get(),
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

        if not os.path.exists(folder):
            os.makedirs(folder)
        with open(f"{folder}/{fn}.json", "w") as f:
            json.dump(data, f, indent=4)

        messagebox.showinfo("Success", f"Saved {fn} to {folder}")
        self.update_asset_combos()

    # ==========================================
    # DB / GRID HELPERS
    # ==========================================
    def hex_to_pixel(self, q, r):
        x = EDITOR_HEX_SIZE * (3.0 / 2 * q)
        y = EDITOR_HEX_SIZE * (math.sqrt(3) / 2 * q + math.sqrt(3) * r)
        return x, y

    def pixel_to_hex(self, x, y):
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
                cx, cy = local_x + OFFSET_X, local_y + OFFSET_Y

                if (q, r) not in existing_tiles:
                    self.canvas.create_polygon(
                        self.get_hex_points(cx, cy),
                        fill="",
                        outline="#333",
                        tags=("ghost", f"{q},{r}"),
                    )

        sorted_coords = sorted(existing_tiles.keys(), key=lambda k: (k[1], k[0]))
        for q, r in sorted_coords:
            t = existing_tiles[(q, r)]
            cx, cy = self.hex_to_pixel(q, r)
            cx += OFFSET_X
            cy += OFFSET_Y

            color = "#4caf50"
            if t.get("tile_type") == "water":
                color = "#2196f3"
            elif t.get("tile_type") == "mountain":
                color = "#795548"

            self.canvas.create_polygon(
                self.get_hex_points(cx, cy),
                fill=color,
                outline="#666",
                tags=("hex", f"{q},{r}"),
            )

            if t.get("texture_file"):
                img = self.get_tk_image(
                    t["texture_file"], target_width=int(EDITOR_HEX_SIZE * 2)
                )
                if img:
                    self.canvas.create_image(cx, cy, image=img)

            prop = t.get("prop_texture_file") or t.get("overlay_texture_file")
            # Apply selection preview override
            if (
                q == self.sel_q.get()
                and r == self.sel_r.get()
                and self.sel_prop_texture.get()
            ):
                prop = self.sel_prop_texture.get()
                scale = self.sel_prop_scale.get()
            else:
                scale = t.get("prop_scale", 1.0)

            if prop:
                p_img = self.get_tk_image(
                    prop, target_width=int(EDITOR_HEX_SIZE * (scale or 1.0))
                )
                if p_img:
                    self.canvas.create_image(cx, cy - 5, image=p_img)

        self.canvas.create_text(
            OFFSET_X, OFFSET_Y, text="0,0", fill="white", font=("Arial", 8)
        )

    def get_hex_points(self, cx, cy):
        points = []
        for i in range(6):
            angle = math.radians(60 * i)
            points.append(cx + EDITOR_HEX_SIZE * math.cos(angle))
            points.append(cy + EDITOR_HEX_SIZE * math.sin(angle))
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
            self.sel_texture.set(row["texture_file"] or "")
            self.sel_prop_texture.set(row["prop_texture_file"] or "")
            self.sel_prop_scale.set(row["prop_scale"] or 1.0)
            self.sel_prop_shift.set(row["prop_y_shift"] or 0)
        else:
            self.sel_type.set("grass")
            self.sel_texture.set("")
            self.sel_prop_texture.set("")
            self.sel_prop_scale.set(1.0)
            self.sel_prop_shift.set(0)

    def save_tile_to_db(self):
        q, r = self.sel_q.get(), self.sel_r.get()
        try:
            self.cursor.execute(
                """
                INSERT INTO map_tiles (q, r, tile_type, texture_file, prop_texture_file, prop_scale, prop_y_shift)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(q, r) DO UPDATE SET
                    tile_type=excluded.tile_type,
                    texture_file=excluded.texture_file,
                    prop_texture_file=excluded.prop_texture_file,
                    prop_scale=excluded.prop_scale,
                    prop_y_shift=excluded.prop_y_shift
            """,
                (
                    q,
                    r,
                    self.sel_type.get(),
                    self.sel_texture.get(),
                    self.sel_prop_texture.get(),
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

    def update_asset_combos(self):
        self.refresh_asset_library()
        self.tile_combo["values"] = list(self.tile_library.keys())
        self.prop_combo["values"] = list(self.prop_library.keys())


if __name__ == "__main__":
    root = tk.Tk()
    app = GameEditor(root)
    root.mainloop()
