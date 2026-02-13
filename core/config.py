import os

class Config:
    # Game Scale
    GAME_SCALE = 3
    BASE_HEX_RADIUS = 16
    HEX_SIZE = BASE_HEX_RADIUS * GAME_SCALE  # 48 pixels
    HEX_ASPECT_RATIO = 0.87
    CALIB_OFFSET_Y = 16 * GAME_SCALE
    
    # Window Settings
    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 800
    CENTER_X = WINDOW_WIDTH // 2
    CENTER_Y = WINDOW_HEIGHT // 2
    
    # Game Logic
    VISIBLE_RADIUS = 4  # Fog of War radius
    
    # Editor Settings (Merged)
    GRID_RANGE = 20
    MAP_WIDTH = 1400 
    MAP_HEIGHT = 900
    
    # Assets
    ASSET_DIR = "assets"
    DIRS = {
        "tile": "assets/definitions/tiles",
        "prop": "assets/definitions/props",
        "monster": "assets/definitions/monsters",
        "player": "assets/definitions/player",
    }
