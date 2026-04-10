from numpy import tile
import pygame
import math
from core.config import Config
from core.hexmath import HexMath
from gameplay import world


class GameRenderer:
    def __init__(self, asset_manager):
        self.assets = asset_manager
        # Colors
        self.COLOR_BG = (17, 17, 17) # #111
        self.COLOR_GRASS = (46, 59, 40) # #2e3b28
        self.COLOR_WATER = (40, 59, 69) # #283b45
        self.COLOR_STONE = (56, 56, 56) # #383838
        self.COLOR_OUTLINE = (34, 34, 34) # #222

        # render cache pool, to reduce lagging
        self.image_cache = {}

        self.cloud_images = [
        pygame.image.load("assets/assetBank/clouds/cloud 1.png").convert_alpha(),
        pygame.image.load("assets/assetBank/clouds/cloud 2.png").convert_alpha(),
        pygame.image.load("assets/assetBank/clouds/cloud 3.png").convert_alpha(),
        pygame.image.load("assets/assetBank/clouds/cloud 4.png").convert_alpha(),
        pygame.image.load("assets/assetBank/clouds/cloud 5.png").convert_alpha(),
        pygame.image.load("assets/assetBank/clouds/cloud 6.png").convert_alpha(),
        pygame.image.load("assets/assetBank/clouds/cloud 7.png").convert_alpha(),
        pygame.image.load("assets/assetBank/clouds/cloud 8.png").convert_alpha(),
        pygame.image.load("assets/assetBank/clouds/cloud 9.png").convert_alpha(),
        pygame.image.load("assets/assetBank/clouds/cloud 10.png").convert_alpha(),
        pygame.image.load("assets/assetBank/clouds/cloud 11.png").convert_alpha(),
        pygame.image.load("assets/assetBank/clouds/cloud 12.png").convert_alpha(),
        pygame.image.load("assets/assetBank/clouds/cloud 13.png").convert_alpha(),
        pygame.image.load("assets/assetBank/clouds/cloud 14.png").convert_alpha(),
        pygame.image.load("assets/assetBank/clouds/cloud 15.png").convert_alpha(),
        pygame.image.load("assets/assetBank/clouds/cloud 16.png").convert_alpha(),
        pygame.image.load("assets/assetBank/clouds/cloud 17.png").convert_alpha(),
        pygame.image.load("assets/assetBank/clouds/cloud 18.png").convert_alpha(),
        pygame.image.load("assets/assetBank/clouds/cloud 19.png").convert_alpha(),
        pygame.image.load("assets/assetBank/clouds/cloud 20.png").convert_alpha()
        ]
        

    def render(self, screen, world, frame_index=0):
        screen.fill(self.COLOR_BG)
        
        player = world.player
        if not player:
            return

        cx = Config.CENTER_X
        cy = Config.CENTER_Y
        render_range = 15
        
        # if the player is moving, let the camera focus on the player for interpolation
        if getattr(player, "is_moving", False):
            from_px, from_py = HexMath.hex_to_pixel(player.move_from_q, player.move_from_r)
            to_px, to_py = HexMath.hex_to_pixel(player.move_to_q, player.move_to_r)
            t = player.move_progress
            
            ppx = from_px + (to_px - from_px) * t
            ppy = from_py + (to_py - from_py) * t
        else:
            ppx, ppy = HexMath.hex_to_pixel(player.q, player.r)

        terrain_layer = []
        object_layer = []

        # Iterate tiles around player
        for q in range(player.q - render_range, player.q + render_range):
            for r in range(player.r - render_range, player.r + render_range):
                if HexMath.distance(q, r, player.q, player.r) > render_range:
                    continue
                    
                tile = world.get_tile(q, r)
                if not tile:
                    continue
                
                px, py = HexMath.hex_to_pixel(q, r)
                
                draw_x = cx + (px - ppx)
                draw_y = cy + (py - ppy)
                
                # Culling
                if (
                    -100 < draw_x < Config.WINDOW_WIDTH + 100
                    and -100 < draw_y < Config.WINDOW_HEIGHT + 100
                ):
                    terrain_layer.append((tile, draw_x, draw_y))
                    if tile.discovered and tile.prop_texture:
                        object_layer.append(
                            {
                                "depth": draw_y,
                                "type": "prop",
                                "tile": tile,
                                "x": draw_x,
                                "y": draw_y,
                            }
                        )
        
        # Add Player
        object_layer.append(
            {"depth": cy, "type": "entity", "entity": player, "x": cx, "y": cy}
        )

        # Add Monsters
        for monster in world.monsters:
            tile = world.get_tile(monster.q, monster.r)
            if not tile or not tile.discovered:
                continue

            if getattr(monster, "is_moving", False):
                from_px, from_py = HexMath.hex_to_pixel(monster.move_from_q, monster.move_from_r)
                to_px, to_py = HexMath.hex_to_pixel(monster.move_to_q, monster.move_to_r)
                t = monster.move_progress

                mqx = from_px + (to_px - from_px) * t
                mqy = from_py + (to_py - from_py) * t
            else:
                mqx, mqy = HexMath.hex_to_pixel(monster.q, monster.r)
                
            mdx = cx + (mqx - ppx)
            mdy = cy + (mqy - ppy)
            
            # Culling
            if (
                -100 < mdx < Config.WINDOW_WIDTH + 100
                and -100 < mdy < Config.WINDOW_HEIGHT + 100
            ):
                object_layer.append(
                    {"depth": mdy, "type": "entity", "entity": monster, "x": mdx, "y": mdy}
                )

        # Add Ground Items
        for item in world.ground_items:
            # We add q, r to the item object for rendering by converting the tile id to q, r
            tile = world.get_tile(item.q, item.r)
            iqx, iqy = HexMath.hex_to_pixel(item.q, item.r)
            idx = cx + (iqx - ppx)
            idy = cy + (iqy - ppy)
            
            # Culling (don't draw if off screen)
            if (
                -100 < idx < Config.WINDOW_WIDTH + 100
                and -100 < idy < Config.WINDOW_HEIGHT + 100
            ):
                object_layer.append(
                    {"depth": idy, "type": "item", "item": item, "x": idx, "y": idy}
                )
        
        # Draw Terrain (Sorted by Y for slight depth effect if needed, but mostly Z-order matters)
        terrain_layer.sort(key=lambda t: t[2])
        for tile, dx, dy in terrain_layer:
            self._draw_hex_base(screen, tile, dx, dy)


            # clouds that cover locked levels
            if world.is_tile_locked(tile.q, tile.r):

                if tile.discovered:
                    continue  # if already discovered, don't draw clouds

                # cloud couverage
                if (tile.q * 5 + tile.r * 7) % 200 != 0:

                    # cloud selection (images in the list)
                    idx = abs(tile.q * 31 + tile.r * 17) % len(self.cloud_images)
                    img = self.cloud_images[idx]

                    self._draw_cloud_overlay(screen, img, dx, dy, scale=2.3)


        # Draw Objects (Sorted by Depth Y)
        object_layer.sort(key=lambda obj: obj["depth"])

        for obj in object_layer:
            if obj["type"] == "prop":
                self._draw_prop(screen, obj["tile"], obj["x"], obj["y"])
            elif obj["type"] == "entity":
                self._draw_entity(screen, obj["entity"], obj["x"], obj["y"], frame_index)
            elif obj["type"] == "item":
                self._draw_item(screen, obj["item"], obj["x"], obj["y"], frame_index)

        if hasattr(world, "effects"):
            for effect in world.effects:
                # Convert hex coordinates to pixel coordinates
                eqx, eqy = HexMath.hex_to_pixel(effect.q, effect.r)
                
                # Apply camera offset to keep VFX fixed on the map
                edx = cx + (eqx - ppx)
                edy = cy + (eqy - ppy)
                
                if (
                    -200 < edx < Config.WINDOW_WIDTH + 200
                    and -200 < edy < Config.WINDOW_HEIGHT + 200
                ):
                    # Calculate alpha for fade-out effect (255 -> 0)
                    progress = effect.current_radius / effect.max_pixel_radius
                    alpha = int(255 * (1.0 - progress))
                    alpha = max(0, min(255, alpha))
                    
                    if alpha <= 0:
                        continue
                        
                    # Create a temporary surface with per-pixel alpha
                    surf_size = int(effect.max_pixel_radius * 2)
                    if surf_size <= 0:
                        continue
                        
                    temp_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
                    center = (surf_size // 2, surf_size // 2)
                    
                    # Draw the circle with color and alpha
                    pygame.draw.circle(temp_surf, (*effect.color, alpha), center, int(effect.current_radius))
                    
                    # Blit onto the main screen
                    rect = temp_surf.get_rect(
                        centerx=edx,
                        centery=edy - Config.CALIB_OFFSET_Y
                    )
                    screen.blit(temp_surf, rect)

    def _draw_hex_base(self, screen, tile, x, y):
        # HexMath returns list of floats, Pygame needs list of tuples
        poly_floats = HexMath.get_hex_polygon(x, y)
        # Convert flat list [x1, y1, x2, y2...] to [(x1,y1), (x2,y2)...]
        poly_points = list(zip(poly_floats[0::2], poly_floats[1::2]))

        if not tile.discovered:
            pygame.draw.polygon(screen, (0, 0, 0), poly_points)
            return
        
        fill = self.COLOR_GRASS
        if tile.type == "water":
            fill = self.COLOR_WATER
        elif tile.type == "stone":
            fill = self.COLOR_STONE

        pygame.draw.polygon(screen, fill, poly_points)
        pygame.draw.polygon(screen, self.COLOR_OUTLINE, poly_points, 1)

        if tile.texture:
            scale, x_shift, y_shift = self.assets.get_layout(tile.texture)
            img = self.assets.get_image(tile.texture, scale=scale)
            if img:
                # Center horizontally, shift vertically or horizontally
                rect = img.get_rect(centerx=x + x_shift, centery=y - Config.CALIB_OFFSET_Y - y_shift)
                screen.blit(img, rect)

    def _draw_prop(self, screen, tile, x, y):
        if tile.prop_texture:
            img = self.assets.get_image(tile.prop_texture, scale=tile.prop_scale)
            if img:
               rect = img.get_rect(centerx=x + tile.prop_x_shift, centery=y - Config.CALIB_OFFSET_Y - tile.prop_shift)
               screen.blit(img, rect)

    def _draw_entity(self, screen, entity, x, y, frame_index):
        if entity.texture:
            # monsters can use their own animation tick for attack
            if hasattr(entity, "anim_state") and hasattr(entity, "anim_tick"):
                # Now match with archer_...
                if entity.anim_state.endswith(("attack", "hit", "die", "move", "stun", "charge")):
                    use_frame = entity.anim_tick
                else:
                    use_frame = frame_index
            else:
                use_frame = frame_index

            base_img = self.assets.get_anim_frame(entity.texture, use_frame)
            if not base_img:
                return
        
            flash_color = None

            # first check poison state
            if getattr(entity, "poison_flash_timer", 0) > 0:
                flash_color = (180, 50, 255)
            # add red flash effect to both player and monster
            elif getattr(entity, "damage_flash_timer", 0) > 0:
                flash_color = (255, 50, 50)

            if hasattr(entity, "anim_state") and hasattr(entity, "anim_tick"):
                if entity.anim_state.endswith("die") and entity.anim_tick < 4:
                    flash_color = (255, 50, 50)

            # Change the texture direction with player and monsters direction
            is_flipped = getattr(entity, "flip_x", False)

            cache_key = (id(base_img), flash_color, is_flipped)

            # First look in cache, if not found, generate new one and cache it
            if cache_key in self.image_cache:
                img = self.image_cache[cache_key]
            else:
                img = base_img
                
                if flash_color is not None:
                    flash_img = img.copy()  # make a copy of origin img
                    flash_img.fill(flash_color, special_flags=pygame.BLEND_RGB_MULT)
                    img = flash_img

                if is_flipped:
                    img = pygame.transform.flip(img, True, False)

                # cache it
                self.image_cache[cache_key] = img

            scale, x_shift, y_shift = self.assets.get_layout(entity.texture)
            rect = img.get_rect(
                centerx=x + x_shift,
                centery=y - Config.CALIB_OFFSET_Y - y_shift
            )
            screen.blit(img, rect)
        else:
            pygame.draw.circle(screen, (255, 0, 0), (int(x), int(y)), 10)

    def _draw_item(self, screen, item, x, y, frame_index):
        if not item.texture:
            return
            
        # Check if it's animated (keys) or static
        img = self.assets.get_anim_frame(item.texture, frame_index)
        scale, x_shift, y_shift = self.assets.get_layout(item.texture)
        
        if img:
            rect = img.get_rect(
                centerx=x + x_shift,
                centery=y - Config.CALIB_OFFSET_Y - y_shift
            )
            screen.blit(img, rect)

    # cloud helper function
    def _draw_cloud_overlay(self, screen, img, x, y, scale=1.3):
        width = int(img.get_width() * scale * 1.15)   # slightly wider
        height = int(img.get_height() * scale * 0.9)   # slightly shorter
        cloud = pygame.transform.smoothscale(img, (width, height))
        cloud.set_alpha(210)  # soft fog
        rect = cloud.get_rect(center=(x, y - Config.CALIB_OFFSET_Y))
        screen.blit(cloud, rect)