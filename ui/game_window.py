import pygame
from core.config import Config
from database.db_manager import DatabaseManager
from gameplay.engine import GameEngine
from visuals.asset_manager import AssetManager
from visuals.renderer import GameRenderer
from ui.button import Button
from ui.base_screen import Screen
import random


class GameWindow(Screen):
    def __init__(self, manager, slot_id=1, selected_skin=None):
        super().__init__(manager)

        slot_id = manager.selected_slot or 1
        selected_skin = manager.selected_skin

        pygame.display.set_caption(f"Hex RPG - Slot {slot_id}")
      

        db_file = f"game_data_{slot_id}.db"
        self.db = DatabaseManager(db_file)
        # Ensure session exists (auto-create slot 1)
        if not self.db.get_session(1):
            char_type = getattr(manager, "selected_character", "warrior")
            sid = self.db.create_session(1, char_type=char_type)
            
            # Add and equip starting weapon
            weapon_name = "test_bow" if char_type == "archer" else "test_sword"
            weapon_id = self.db.get_or_create_item(weapon_name)
            if weapon_id:
                self.db.add_item(sid, weapon_id, quantity=1)
                self.db.toggle_equip(sid, weapon_id)

        if selected_skin:
            self.db.cursor.execute("UPDATE player_state SET texture_file=? WHERE session_id=1", (selected_skin,))
            self.db.conn.commit()

        self.engine = GameEngine(self.db, 1)
        # Demo: spawn a visible chest next to the player until the DB-backed
        # chest system is wired up.
        if not self.engine.world.chests:
            self.engine.world.spawn_demo_chest()
        self.assets = AssetManager()
        self.renderer = GameRenderer(self.assets)

        self.font = pygame.font.SysFont("Arial", 18)
        self.loot_font = pygame.font.SysFont("Arial", 22, bold=True)
        self.frame_index = 0
        self.anim_timer = 0

        # Active floating loot notification (only one shown at a time).
        # Each entry: {"text": str, "age_ms": int}
        # Items in engine.loot_notifications_queue drip in one-by-one.
        self.active_loot_notification = None
        self.loot_notification_duration_ms = 1000  # 1 second fade

    

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.manager.running = False
            # Key Presses (Single Action)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.manager.switch_screen("main_menu")

            # Open/Close Inventory should strictly be a single key press
            elif event.key == pygame.K_i or event.key == pygame.K_TAB:
                action = "INVENTORY"
                self.engine.run_turn(action)

            # Let the inventory still read from the input key
            elif getattr(self.engine, "show_inventory", False):
                action = None

                if event.key == pygame.K_w:
                    action = "MOVE_NORTH"       
                elif event.key == pygame.K_s:
                    action = "MOVE_SOUTH"       
                elif event.key == pygame.K_a:
                    action = "MOVE_SW"        
                elif event.key == pygame.K_f or event.key == pygame.K_SPACE:
                    action = "INTERACT"         

                if action:
                    self.engine.run_turn(action)
                    
    def update(self):
        # Loot notifications: per-frame (not tied to 50ms anim tick) so fade is smooth
        self._update_loot_notifications(self.manager.clock.get_time())

        # Animation tick
        self.anim_timer += self.manager.clock.get_time()
        if self.anim_timer > 50:
            self.anim_timer = 0
            self.frame_index += 1

            # player animation
            player = self.engine.world.player
            if player:
                player.update_animation(self.assets)

            # Update all monnster's sprite frames and handle death cleanup
            monsters_to_remove = []

            for monster in self.engine.world.monsters:
                monster.update_animation(self.assets)

                if not monster.is_alive():
                    self.engine.drop_monster_loot(monster)

                if getattr(monster, "remove_after_death", False):
                    monsters_to_remove.append(monster)

            for monster in monsters_to_remove:
                if monster in self.engine.world.monsters:
                    self.engine.world.monsters.remove(monster)

            # Chest animations + despawn after opening
            chests_to_remove = []
            for chest in self.engine.world.chests:
                chest.update_animation(self.assets)
                if chest.remove_after_open:
                    chests_to_remove.append(chest)
            for chest in chests_to_remove:
                self.engine.world.chests.remove(chest)

            if hasattr(self.engine.world, "update_vfx"):
                self.engine.world.update_vfx()

        # Implement real-time ARPG 
        player = self.engine.world.player
        if not player:
            return
        
        # Check current status
        is_player_animating = getattr(player, "is_moving", False) or getattr(player, "is_attacking", False)
        is_inventory_open = getattr(self.engine, "show_inventory", False)

        # Only process game actions if the inventory is closed
        if not is_inventory_open:

            # Only accept new commands if the player has finished their current action
            if not is_player_animating:
                keys = pygame.key.get_pressed()
                action = None
            
                if keys[pygame.K_w]: action = "MOVE_NORTH"
                elif keys[pygame.K_s]: action = "MOVE_SOUTH"
                elif keys[pygame.K_a]: action = "MOVE_SW"
                elif keys[pygame.K_d]: action = "MOVE_EAST"
                elif keys[pygame.K_q]: action = "MOVE_WEST"
                elif keys[pygame.K_e]: action = "MOVE_NE"
                elif keys[pygame.K_f] or keys[pygame.K_SPACE]: action = "INTERACT"

                if action:
                    if action in ("MOVE_WEST", "MOVE_SW"): # q, a
                        player.flip_x = True
                    elif action in ("MOVE_EAST", "MOVE_NE"): # e, d
                        player.flip_x = False
                    
                    result = self.engine.run_turn(action)
                    if result == "GAME_OVER":
                        self.manager.switch_screen("game_over")

            # Independent Monster AI Handling
            for monster in self.engine.world.monsters:
                if not monster.is_alive():
                    continue

                is_monster_animating = getattr(monster, "is_moving", False) or monster.anim_state in ("move", "attack", "hit")
                if is_monster_animating:
                    continue

                # Initialize real-time action timer 
                if not hasattr(monster, "rt_action_timer"):
                    monster.rt_action_timer = random.randint(30, 40) 
                
                monster.rt_action_timer -= 1

                # Trigger monster AI decision if timer reaches zero
                if monster.rt_action_timer <= 0:
                    if player.q > monster.q:
                        monster.flip_x = True
                    elif player.q < monster.q:
                        monster.flip_x = False

                    monster.decide_and_act(self.engine.world, player)
                    monster.rt_action_timer = random.randint(30, 40)

    def _update_loot_notifications(self, dt_ms):
        """Advance the active notification and pull the next one off the queue."""
        # Pop next notification if slot is free
        if self.active_loot_notification is None:
            if self.engine.loot_notifications_queue:
                name, count = self.engine.loot_notifications_queue.pop(0)
                self.active_loot_notification = {
                    "text": f"{name} x{count}",
                    "age_ms": 0,
                }
            return

        # Age the active one
        self.active_loot_notification["age_ms"] += dt_ms
        if self.active_loot_notification["age_ms"] >= self.loot_notification_duration_ms:
            self.active_loot_notification = None

    def _draw_loot_notification(self):
        """Draw the active floating loot text above the player with a fade."""
        notif = self.active_loot_notification
        if notif is None:
            return

        # Linear fade out across the full duration
        progress = notif["age_ms"] / self.loot_notification_duration_ms
        progress = max(0.0, min(1.0, progress))
        alpha = int(255 * (1.0 - progress))
        # Rise a little as it fades (10px over the full duration)
        y_offset = int(progress * 10)

        text_surf = self.loot_font.render(
            notif["text"], True, (255, 236, 140)
        )
        # Per-pixel alpha requires a scratch surface
        faded = pygame.Surface(text_surf.get_size(), pygame.SRCALPHA)
        faded.blit(text_surf, (0, 0))
        faded.set_alpha(alpha)

        # Center horizontally, anchor above the player's HUD position.
        # Player is always drawn at screen center.
        cx = self.manager.screen.get_width() // 2
        cy = self.manager.screen.get_height() // 2
        rect = faded.get_rect(center=(cx, cy - 80 - y_offset))
        self.manager.screen.blit(faded, rect)

    def draw(self):
        self.update()
        # Render World
        self.renderer.render(self.manager.screen, self.engine.world, self.frame_index)

        # Render UI Overlay
        self._draw_ui()

        # Loot pickup text (drawn after world, before inventory overlay)
        self._draw_loot_notification()

        # inventory
        if self.engine.show_inventory:
            self._draw_inventory()

    # Helper function which draws a rounded rectangle, keep all inentory panel box consistent
    def _draw_panel_box(self, rect, fill, border, border_width=2):
        pygame.draw.rect(self.manager.screen, fill, rect, border_radius=10)
        pygame.draw.rect(
            self.manager.screen,
            border,
            rect,
            border_width,
            border_radius=10,
        )

    # Top part of inventory page
    def _draw_inventory_header(self, panel_rect, player):
        # Create two font size for this part
        title_font = pygame.font.SysFont("Arial", 28, bold=True)
        small_font = pygame.font.SysFont("Arial", 16)

        # Dispaly title, control instruction and player info
        title = title_font.render("Inventory", True, (236, 228, 204))
        controls = small_font.render(
            "W/S: Select   F: Use/Equip   A: Drop   I: Close",
            True,
            (162, 169, 178),
        )
        summary = self.font.render(
            f"ATK: {player.total_damage}   DEF: {player.total_defense}",
            True,
            (162, 204, 198),
        )

        # Place them on the screen
        self.manager.screen.blit(title, (panel_rect.x + 24, panel_rect.y + 18))
        self.manager.screen.blit(controls, (panel_rect.x + 24, panel_rect.y + 52))
        self.manager.screen.blit(summary, (panel_rect.x + 24, panel_rect.y + 80))

    # Left side of inventory page, list all items in inventory and show which one is selected
    def _draw_inventory_list(self, rect, items):
        self._draw_panel_box(rect, (31, 34, 40), (84, 90, 98))

        # Title
        list_title = self.font.render("Items", True, (210, 214, 220))
        self.manager.screen.blit(list_title, (rect.x + 16, rect.y + 12))

        # Empty state
        if not items:
            empty = self.font.render("Your inventory is empty.", True, (145, 150, 158))
            hint = self.font.render("Pick up items to see them here.", True, (105, 112, 121))
            self.manager.screen.blit(empty, (rect.x + 16, rect.y + 52))
            self.manager.screen.blit(hint, (rect.x + 16, rect.y + 78))
            return

        row_height = 52
        top = rect.y + 42
        bottom = rect.bottom - 12

        # Loop through items and display them
        for i, item in enumerate(items):
            # If the row goes beyond the bottom of the panel, stop drawing more items
            row_y = top + i * (row_height + 8)
            if row_y + row_height > bottom:
                break

            # Engine stores selected_index which is used to determine which item is highlighted
            row_rect = pygame.Rect(rect.x + 12, row_y, rect.width - 24, row_height)
            selected = i == self.engine.selected_index
            row_fill = (92, 69, 41) if selected else (42, 46, 53)
            row_border = (230, 196, 120) if selected else (74, 80, 89)
            name_color = (255, 241, 197) if selected else (225, 228, 232)
            meta_color = (244, 214, 147) if selected else (152, 159, 168)

            self._draw_panel_box(row_rect, row_fill, row_border)

            # Display item name, quantity, type, slot and equipped status
            quantity = f"x{item.quantity}"
            name = self.font.render(f"{item.name} {quantity}", True, name_color)
            meta_bits = [item.type.title()]
            if item.is_equippable and item.slot:
                meta_bits.append(item.slot.title())
            if item.equipped:
                meta_bits.append("Equipped")
            meta = self.font.render("  |  ".join(meta_bits), True, meta_color)

            self.manager.screen.blit(name, (row_rect.x + 14, row_rect.y + 10))
            self.manager.screen.blit(meta, (row_rect.x + 14, row_rect.y + 28))

    # Right top of inventory page
    def _draw_equipment_summary(self, rect, player):
        self._draw_panel_box(rect, (31, 34, 40), (84, 90, 98))

        title = self.font.render("Equipped", True, (210, 214, 220))
        self.manager.screen.blit(title, (rect.x + 16, rect.y + 12))

        # Define display labels for each equipment slot
        slot_labels = {
            "weapon": "Weapon",
            "armor": "Armor",
        }

        line_y = rect.y + 46
        # Loop through each equipment slot and display the equipped item or "--" if empty
        for slot_name in ("weapon", "armor"):
            equipped = player.equipment.get(slot_name)
            label = equipped.name if equipped else "--"
            color = (186, 220, 198) if equipped else (120, 127, 135)
            slot_surf = self.font.render(
                f"{slot_labels[slot_name]}: {label}",
                True,
                color,
            )
            self.manager.screen.blit(slot_surf, (rect.x + 16, line_y))
            line_y += 28

    # Right bottom of inventory page
    def _selected_item_detail_lines(self, item):
        if not item:
            return [("Select an item to inspect its details.", (145, 150, 158))]

        lines = []
        if item.description:
            lines.append((item.description, (182, 188, 196)))
        if item.damage_bonus:
            lines.append((f"Damage +{item.damage_bonus}", (169, 214, 205)))
        if item.defense:
            lines.append((f"Defense +{item.defense}", (169, 214, 205)))
        if item.max_durability:
            lines.append(
                (
                    f"Durability {item.durability}/{item.max_durability}",
                    (169, 214, 205),
                )
            )
        if item.type == "food":
            lines.append((f"Heal {item.healing_amount}", (169, 214, 205)))
            lines.append((f"Hunger +{item.hunger_restore}", (169, 214, 205)))
        if item.weight:
            lines.append((f"Weight {item.weight}", (169, 214, 205)))
        if not lines:
            lines.append(("No additional details.", (145, 150, 158)))
        return lines

    # Right bottom of inventory page
    def _draw_selected_item_details(self, rect, item):
        self._draw_panel_box(rect, (31, 34, 40), (84, 90, 98))

        title = self.font.render("Details", True, (210, 214, 220))
        self.manager.screen.blit(title, (rect.x + 16, rect.y + 12))

        # If an item is selected, display its name, type and details. Otherwise show a hint to select an item
        if item:
            name = self.font.render(item.name, True, (236, 228, 204))
            item_type = self.font.render(item.type.title(), True, (244, 214, 147))
            self.manager.screen.blit(name, (rect.x + 16, rect.y + 44))
            self.manager.screen.blit(item_type, (rect.x + 16, rect.y + 68))
            line_y = rect.y + 102
        else:
            line_y = rect.y + 46

        # Loop through the lines of details for the selected item and display them
        for line, color in self._selected_item_detail_lines(item):
            surf = self.font.render(line, True, color)
            self.manager.screen.blit(surf, (rect.x + 16, line_y))
            line_y += 24


    def _draw_ui(self):
        p = self.engine.world.player
        if not p:
            return

        # Simple Stat Bar
        pygame.draw.rect(self.manager.screen, (30, 30, 30), (0, 0, Config.WINDOW_WIDTH, 40))

        hp_text = self.font.render(f"HP: {p.hp}/{p.max_hp}", True, (255, 80, 80))
        hunger_text = self.font.render(
            f"Hunger: {p.hunger}/{p.max_hunger}", True, (255, 160, 50)
        )
        dmg_text = self.font.render(f"ATK: {p.total_damage}", True, (255, 200, 100))
        def_text = self.font.render(f"DEF: {p.total_defense}", True, (100, 200, 255))
        loc_text = self.font.render(f"Q:{p.q} R:{p.r}", True, (200, 200, 200))

        self.manager.screen.blit(hp_text, (20, 10))
        self.manager.screen.blit(hunger_text, (150, 10))
        self.manager.screen.blit(dmg_text, (320, 10))
        self.manager.screen.blit(def_text, (420, 10))
        self.manager.screen.blit(loc_text, (Config.WINDOW_WIDTH - 100, 10))

    # Inventory screen with 3 sections
    def _draw_inventory(self):
        # Semi-transparent dark overlay
        overlay = pygame.Surface(
            (Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT), pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 160))
        self.manager.screen.blit(overlay, (0, 0))

        # Main panel
        p = self.engine.world.player
        panel_x, panel_y = 200, 80
        panel_w, panel_h = Config.WINDOW_WIDTH - 400, Config.WINDOW_HEIGHT - 160
        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        self._draw_panel_box(panel_rect, (22, 24, 29), (176, 182, 188), 3)

        self._draw_inventory_header(panel_rect, p)

        # Splits the panel body into left list and right sidebar
        body_top = panel_y + 116
        body_height = panel_h - 140
        left_width = int(panel_w * 0.62)
        sidebar_width = panel_w - left_width - 54

        # Define rectangles for the three sections
        list_rect = pygame.Rect(panel_x + 18, body_top, left_width, body_height)
        equipment_rect = pygame.Rect(
            list_rect.right + 18,
            body_top,
            sidebar_width,
            174,
        )
        details_rect = pygame.Rect(
            list_rect.right + 18,
            equipment_rect.bottom + 14,
            sidebar_width,
            body_height - equipment_rect.height - 14,
        )

        # Get the player's inventory items
        items = self.engine.world.player.inventory
        selected_item = None
        if items and self.engine.selected_index < len(items):
            selected_item = items[self.engine.selected_index]

        # Draw the three sections of the inventory panel
        self._draw_inventory_list(list_rect, items)
        self._draw_equipment_summary(equipment_rect, p)
        self._draw_selected_item_details(details_rect, selected_item)
