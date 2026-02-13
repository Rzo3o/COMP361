import pygame
import math
from core.config import Config
from core.hexmath import HexMath

class GameRenderer:
    def __init__(self, asset_manager):
        self.assets = asset_manager
        # Colors
        self.COLOR_BG = (17, 17, 17) # #111
        self.COLOR_GRASS = (46, 59, 40) # #2e3b28
        self.COLOR_WATER = (40, 59, 69) # #283b45
        self.COLOR_STONE = (56, 56, 56) # #383838
        self.COLOR_OUTLINE = (34, 34, 34) # #222

    def render(self, screen, world, frame_index=0):
        screen.fill(self.COLOR_BG)
        
        player = world.player
        if not player:
            return

        cx = Config.CENTER_X
        cy = Config.CENTER_Y
        render_range = 15
        
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
        
        # Draw Terrain (Sorted by Y for slight depth effect if needed, but mostly Z-order matters)
        terrain_layer.sort(key=lambda t: t[2])
        for tile, dx, dy in terrain_layer:
            self._draw_hex_base(screen, tile, dx, dy)
            
        # Draw Objects (Sorted by Depth Y)
        object_layer.sort(key=lambda obj: obj["depth"])

        for obj in object_layer:
            if obj["type"] == "prop":
                self._draw_prop(screen, obj["tile"], obj["x"], obj["y"])
            elif obj["type"] == "entity":
                self._draw_entity(screen, obj["entity"], obj["x"], obj["y"], frame_index)

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
            scale, shift = self.assets.get_layout(tile.texture)
            img = self.assets.get_image(tile.texture, scale=scale)
            if img:
                # Center horizontally, shift vertically
                rect = img.get_rect(centerx=x, bottom=y - Config.CALIB_OFFSET_Y - shift + img.get_height())
                screen.blit(img, rect)

    def _draw_prop(self, screen, tile, x, y):
        if tile.prop_texture:
            img = self.assets.get_image(tile.prop_texture, scale=tile.prop_scale)
            if img:
               rect = img.get_rect(centerx=x, bottom=y - Config.CALIB_OFFSET_Y - tile.prop_shift + img.get_height())
               screen.blit(img, rect)

    def _draw_entity(self, screen, entity, x, y, frame_index):
        if entity.texture:
            img = self.assets.get_anim_frame(entity.texture, frame_index)
            scale, shift = self.assets.get_layout(entity.texture)

            if img:
                rect = img.get_rect(centerx=x, bottom=y - Config.CALIB_OFFSET_Y - shift + img.get_height())
                screen.blit(img, rect)
        else:
            pygame.draw.circle(screen, (255, 0, 0), (int(x), int(y)), 10)
